# Exercise 19.4 - The growth of the AM prompts
# Run from the root of the repository:  python chapters/ch19/python/solutions/ex19_4_token_growth.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.monitor import load_log

df = load_log("data/logs/requests_2026_10.jsonl")

import numpy as np
from aie.monitor import daily_metrics
m = daily_metrics(df)
am = m[m.domain == "am"][["day", "avg_tokens"]].reset_index(drop=True)
am["t"] = (pd.to_datetime(am.day) - pd.Timestamp("2026-10-01")).dt.days
slope, intercept = np.polyfit(am.t, am.avg_tokens, 1)
print(round(slope, 1), round(intercept))
