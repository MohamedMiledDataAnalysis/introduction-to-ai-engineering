# Exercise 19.5 - The cost of October
# Run from the root of the repository:  python chapters/ch19/python/solutions/ex19_5_cost.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.monitor import load_log

df = load_log("data/logs/requests_2026_10.jsonl")

print((df.groupby("domain").tokens.sum() / 1e6 * 3).round(2))
print((df.groupby("caller").tokens.sum() / 1e6 * 3).round(2))
print(df.groupby("domain").tokens.mean().round(0))
