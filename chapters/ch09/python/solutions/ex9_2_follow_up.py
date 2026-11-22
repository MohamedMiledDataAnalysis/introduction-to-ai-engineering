# Exercise 9.2 - A follow-up question with history
# Run from the root of the repository:  python chapters/ch09/python/solutions/ex9_2_follow_up.py

import sys

sys.path.insert(0, ".")
from aie.agent import Agent

SYSTEM = ("You are an assistant for Larkfield Mortgage Funding 2025-1. "
          "Use the tools for every figure and search the prospectus for rules "
          "and definitions. Cite passage identifiers such as [LMF#3]. "
          "Never compute or estimate a figure yourself.")
agent = Agent(SYSTEM, ["pool_summary", "note_balance", "waterfall_summary",
                       "search_prospectus"], max_steps=6)

def show(result):
    for name, args, res in result["trace"]:
        print(f"  {name:<18} {str(args)[:60]:<60} {res[:60]}")
    print(f"  status={result['status']} steps={result['steps']} "
          f"unsupported={result['unsupported']}")
    print(f"  answer: {result['answer']}\n")

first_q = "What was the pool balance at 30 September 2026?"
first = agent.run(first_q)
history = [{"role": "user", "content": first_q},
           {"role": "assistant", "content": first["answer"]}]
second = agent.run("And at the end of August?", history=history)
show(second)
