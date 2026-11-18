"""Answer a question with tools: the model asks for tool calls, code runs them, the model answers."""
from aie.llm import chat
from aie.tools import run_tool, tool_specs

SYSTEM = ("You answer questions about Larkfield Mortgage Funding 2025-1 and Harbourline funds. "
          "Get every figure from a tool; never compute or estimate a figure yourself. "
          "Quote figures as the tools return them, rounded only as the question asks. "
          "If no tool can answer, say so.")


def ask_with_tools(question, tool_names=None, max_rounds=3, system=SYSTEM, trace=None):
    messages = [{"role": "user", "content": question}]
    tools = tool_specs(tool_names)
    for _ in range(max_rounds):
        reply = chat(messages, system=system, tools=tools)
        if not reply["tool_calls"]:
            return reply["text"]
        messages.append({"role": "assistant", "content": reply["text"],
                         "tool_calls": [{"function": c} for c in reply["tool_calls"]]})
        for call in reply["tool_calls"]:
            result = run_tool(call, allowed=tool_names)
            if trace is not None:
                trace.append((call["name"], call.get("arguments"), result))
            messages.append({"role": "tool", "content": result, "tool_name": call["name"]})
    return "I could not complete the answer within the allowed number of steps."
