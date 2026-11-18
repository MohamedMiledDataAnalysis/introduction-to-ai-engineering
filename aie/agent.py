"""
A small, inspectable agent: a model that decides which tools to call, under limits,
with every step recorded and the final answer verified before it is returned.
"""
import json
import re

from aie.factcheck import check_text
from aie.llm import chat
from aie.tools import run_tool, tool_specs

UNIT_BY_SUFFIX = (("_pct", "percent"), ("_gbp", "money"), ("_eur", "money"))


def facts_from_results(results):
    """Every numeric value in tool results, with a unit read from the field name."""
    facts = {}

    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            unit = next((u for s, u in UNIT_BY_SUFFIX if path.endswith(s)), "number")
            facts[path] = (obj, unit)
            if unit == "money":
                facts[path + "#plain"] = (obj, "number")

    calls = {}
    for name, result in results:                       # a second call of the same tool gets its own names
        calls[name] = calls.get(name, 0) + 1
        walk(json.loads(result), name if calls[name] == 1 else f"{name}#{calls[name]}")
    return facts


def passage_facts(results):
    """Figures written inside retrieved passages, so that quoting a passage is supported."""
    from aie.factcheck import extract_figures
    facts = {}
    for name, result in results:
        for p in json.loads(result).get("passages", []):
            for i, f in enumerate(extract_figures(p["text"])):
                facts[f"{p['id']}#{i}"] = (f.value * f.scale, f.unit)
    return facts


class Agent:
    def __init__(self, system, tool_names, max_steps=6, max_tokens=20_000, verify=True):
        self.system, self.tool_names = system, tool_names
        self.max_steps, self.max_tokens, self.verify = max_steps, max_tokens, verify

    def run(self, question, history=None):
        messages = list(history or []) + [{"role": "user", "content": question}]
        trace, results, seen, tokens = [], [], set(), 0
        tools = tool_specs(self.tool_names)
        for step in range(1, self.max_steps + 1):
            reply = chat(messages, system=self.system, tools=tools)
            tokens += reply["input_tokens"] + reply["output_tokens"]
            if tokens > self.max_tokens:
                return self._end("stopped: token budget exceeded", trace, step, tokens, "stopped")
            if not reply["tool_calls"]:
                answer = reply["text"].strip()
                problems = self._verify(answer, results) if self.verify else []
                if problems and not any(t[0] == "verification" for t in trace):
                    trace.append(("verification", None, "; ".join(problems)))
                    messages += [{"role": "assistant", "content": answer},
                                 {"role": "user", "content": "These figures are not supported by the tool results: "
                                  + "; ".join(problems) + ". Correct the answer using only figures from the tools."}]
                    continue
                status = "needs_review" if problems else "verified"
                return self._end(answer, trace, step, tokens, status, problems)
            messages.append({"role": "assistant", "content": reply["text"],
                             "tool_calls": [{"function": c} for c in reply["tool_calls"]]})
            for call in reply["tool_calls"]:
                key = (call["name"], json.dumps(call.get("arguments"), sort_keys=True))
                if key in seen:
                    result = json.dumps({"error": "you already made this exact call; use its result above"})
                else:
                    seen.add(key)
                    result = run_tool(call, allowed=self.tool_names)
                    if '"error"' not in result[:10]:
                        results.append((call["name"], result))
                trace.append((call["name"], call.get("arguments"), result))
                messages.append({"role": "tool", "content": result, "tool_name": call["name"]})
        return self._end("stopped: step limit reached", trace, self.max_steps, tokens, "stopped")

    def _verify(self, answer, results):
        facts = {**facts_from_results(results), **passage_facts(results)}
        clean = re.sub(r"\[[A-Z][A-Za-z\-]*#[\d.]+\]", "", answer)
        return [f"{fig.raw}" for fig, hits in check_text(clean, facts) if not hits]

    @staticmethod
    def _end(answer, trace, steps, tokens, status, problems=()):
        return {"answer": answer, "status": status, "steps": steps, "tokens": tokens,
                "trace": trace, "unsupported": list(problems)}
