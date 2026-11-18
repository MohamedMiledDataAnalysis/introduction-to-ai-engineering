# Chapter 12 - Run the data-quality rules on the received tape and measure them against the injected errors
import json
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.dq import run_rules

tape = pd.read_csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv")
truth = pd.DataFrame(json.load(open("data/sf/rmbs/dq/injected_errors.json")))
found = run_rules(tape, "2026-09-30")
print(found.groupby("rule").size().to_string(), "\n")

key = lambda df: set(zip(df["loan_id"], df["rule"]))
tp, fp, fn = key(found) & key(truth), key(found) - key(truth), key(truth) - key(found)
print(f"true positives {len(tp)}, false positives {len(fp)}, false negatives {len(fn)}")
print(f"precision {len(tp) / len(key(found)):.0%}, recall {len(tp) / len(key(truth)):.0%}")
for loan, rule in sorted(fp):
    print("  extra flag:", loan, rule)
for loan, rule in sorted(fn):
    print("  missed:    ", loan, rule)
