"""
Evaluate one of the final-project agents on its evaluation set: answers, tools used and status.
Run from the repository root:  python agents/python/evaluate_agent.py sf     (or am)
"""
import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, ".")
from aie.assistants import Assistant
from aie.evals import run_eval, wilson_interval

domain = sys.argv[1] if len(sys.argv) > 1 else "sf"
cases = pd.read_csv(f"evals/{domain}_agent_eval.csv", dtype=str, keep_default_na=False)
assistant = Assistant(domain)
rows = []
for case in cases.to_dict("records"):
    r = assistant.ask(case["question"])
    tools = [t[0] for t in r["trace"] if t[0] != "verification"]
    rows.append({"id": case["id"], "answer": r["answer"], "status": r["status"], "tools": ";".join(tools),
                 "right_tool": (case["expected_tool"] == "") or (case["expected_tool"] in tools),
                 "tokens": r["tokens"]})
out = pd.DataFrame(rows)
res = run_eval(cases, dict(zip(out.id, out.answer)))
out = out.merge(res[["id", "passed", "reason"]], on="id")
stamp = datetime.now().strftime("%Y%m%d_%H%M")
out.to_csv(f"evals/candidates/{domain}_agent_run_{stamp}.csv", index=False)
low, high = wilson_interval(out.passed.sum(), len(out))
print(f"{domain.upper()} agent, prompt {assistant.version}")
print(f"  correct answers : {out.passed.sum()}/{len(out)} (95% interval {low:.0%}-{high:.0%})")
print(f"  right tool used : {out.right_tool.sum()}/{len(out)}")
print(f"  status          : {out.status.value_counts().to_dict()}")
print(f"  tokens          : {out.tokens.sum():,}")
for r in out[~out.passed | ~out.right_tool].itertuples():
    print(f"  {r.id} {r.reason} | tools: {r.tools or '-'} | {r.answer[:80]}")
