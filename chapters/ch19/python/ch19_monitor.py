# Chapter 19 - From a month of request logs to daily metrics, alerts and explanations
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.monitor import alerts, daily_metrics, load_log

pd.set_option("display.width", 130)
df = load_log("data/logs/requests_2026_10.jsonl")
m = daily_metrics(df)
print(f"{len(df)} requests, {df.day.nunique()} days; total cost at the "
      f"illustrative price: ${m.cost_usd.sum():.2f}\n")
show = m[m.domain == "sf"].drop(columns="domain").round(3)
show.columns = ["day", "requests", "errors", "review", "p50_s", "p95_s", "tokens", "cost_usd"]             # short names: the table fits the page
print(show.to_string(index=False), "\n")
a = alerts(m)
print(a.to_string(index=False), "\n")
print("Review rate by prompt version (SF):")
print(df[(df.domain == "sf") & (df.status != "error")].groupby("prompt")
      .status.apply(lambda s: round((s != "verified").mean(), 3)).to_string())
