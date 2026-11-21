# Exercise 9.3 - A step limit of 3
# Run from the root of the repository:  python chapters/ch09/python/solutions/ex9_3_step_limit.py
# Before you run it: start the mock with MOCK_SCRIPT=tools/scripts/ch09_correction.json python tools/mock_ollama.py

import os
import sys

sys.path.insert(0, ".")
from aie.agent import Agent
from tools.mock import start_mock

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

question = ("How much excess spread was released in September 2026, "
            "and to whom does it go?")
agent3 = Agent(SYSTEM, ["pool_summary", "note_balance", "waterfall_summary",
                        "search_prospectus"], max_steps=3)
show(agent3.run(question))
