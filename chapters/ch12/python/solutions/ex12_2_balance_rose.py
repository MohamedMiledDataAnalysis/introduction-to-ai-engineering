# Exercise 12.2 - A repayment loan whose balance rose
# Run from the root of the repository:  python chapters/ch12/python/solutions/ex12_2_balance_rose.py

import sys

import pandas as pd

sys.path.insert(0, ".")

tape = pd.read_csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv")

prev = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
prev = prev[prev["RREL6"] == "2026-08-31"][["RREL2", "RREL30"]]
m = tape.merge(prev, on="RREL2", how="left", suffixes=("", "_prev"))
rose = m[(m["RREL35"] == "FRXX") & (m["RREL30"] > m["RREL30_prev"] + 1)]
print(rose[["RREL2", "RREL30", "RREL30_prev", "RREL69"]])
