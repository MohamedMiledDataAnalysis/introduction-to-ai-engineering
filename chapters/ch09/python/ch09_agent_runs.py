# Chapter 9 - Watch the agent work, recover from an unsupported figure, and stop a loop
import os
import subprocess
import sys
import time

sys.path.insert(0, ".")
from aie.agent import Agent

SYSTEM = ("You are an assistant for Larkfield Mortgage Funding 2025-1. Use the tools for every figure and "
          "search the prospectus for rules and definitions. Cite passage identifiers such as [LMF#3]. "
          "Never compute or estimate a figure yourself.")
agent = Agent(SYSTEM, ["pool_summary", "note_balance", "waterfall_summary", "search_prospectus"], max_steps=6)


def show(result):
    for name, args, res in result["trace"]:
        print(f"  {name:<18} {str(args)[:60]:<60} {res[:60]}")
    print(f"  status={result['status']} steps={result['steps']} unsupported={result['unsupported']}")
    print(f"  answer: {result['answer']}\n")


question = "How much excess spread was released in September 2026, and to whom does it go?"
if os.environ.get("USE_MOCK_SCRIPTS"):          # replay scripted model behaviour for testing
    for script in ("tools/scripts/ch09_correction.json", "tools/scripts/ch09_loop.json"):
        server = subprocess.Popen([sys.executable, "tools/mock_ollama.py"], env={**os.environ, "MOCK_SCRIPT": script},
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        print(f"Scenario {os.path.basename(script)}")
        show(agent.run(question))
        server.terminate()
        server.wait()
else:
    show(agent.run(question))
