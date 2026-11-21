# Chapter 9 - Watch the agent work, recover from an unsupported figure, and stop a loop
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
if os.environ.get("USE_MOCK_SCRIPTS"):           # scripted model, for the scenarios
    for script in ("tools/scripts/ch09_correction.json",
                   "tools/scripts/ch09_loop.json"):
        with start_mock(script):                 # the mock on a free port
            print(f"Scenario {os.path.basename(script)}")
            show(agent.run(question))
else:
    show(agent.run(question))
