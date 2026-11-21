# Exercise 12.1 - A consistency rule for the LTV
# Run from the root of the repository:  python chapters/ch12/python/solutions/ex12_1_ltv_rule.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.dq import RULES, run_rules

tape = pd.read_csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv")

RULES["ltv_inconsistent"] = (
    "Original LTV (RREC16) disagrees with original balance / original "
    "valuation (RREL29 / RREC17) by more than 0.5 points",
    lambda t, d: (100 * t["RREL29"] / t["RREC17"] - t["RREC16"]).abs() > 0.5)

found = run_rules(tape, "2026-09-30")
print(found[found["rule"] == "ltv_inconsistent"][["loan_id", "rule"]].to_string(index=False))
t = tape[tape["RREL2"].isin(found.loc[found["rule"] == "ltv_inconsistent", "loan_id"])]
print(t[["RREL2", "RREL29", "RREC17", "RREC16"]].to_string(index=False))
