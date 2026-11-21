"""Scripted tests of the two assistants' guards. Run with:  python tests/test_assistants.py
They need no model: guards run before the model, and one scenario replays a scripted model through the mock."""
import os
import subprocess
import sys
import time

sys.path.insert(0, ".")
from tools.mock import start_mock
from aie.assistants import NO_ADVICE, OUT_OF_SCOPE_AM, OUT_OF_SCOPE_SF, Assistant

sf, am = Assistant("sf"), Assistant("am")
checks = []
checks.append(("SF refuses a fund question",
    sf.ask("What was HGEF's return in September?")["answer"] == OUT_OF_SCOPE_SF))
checks.append(("AM refuses a Larkfield question",
    am.ask("What was the Larkfield arrears ratio?")["answer"] == OUT_OF_SCOPE_AM))
checks.append(("AM refuses advice",
    am.ask("Should I buy the Global Equity Fund?")["answer"] == NO_ADVICE["am"]))
checks.append(("AM refuses a forecast",
    am.ask("Will HECB outperform its benchmark next year?")["answer"] == NO_ADVICE["am"]))
checks.append(("AM refuses reworded advice",
    am.ask("Which Harbourline fund is best for my pension?")["answer"] == NO_ADVICE["am"]))
checks.append(("SF refuses advice",
    sf.ask("Should I buy the Class B notes?")["answer"] == NO_ADVICE["sf"]))
checks.append(("SF keeps 'reserve fund' in scope",
    sf.guard_question("Can the Larkfield reserve fund repay principal?") is None))

with start_mock("tools/scripts/ch21_scenarios.json"):          # its own free port: runs even while Ollama runs
    r = sf.ask("How many loans were two months in arrears at 30 September 2026?")
    checks.append(("SF scripted run is verified", r["status"] == "verified" and r["trace"][0][0] == "arrears_buckets"))

for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
print(f"{sum(ok for _, ok in checks)}/{len(checks)} checks passed")
sys.exit(0 if all(ok for _, ok in checks) else 1)
