# Exercise 19.3 - The evidence of the incident note
# Run from the root of the repository:  python chapters/ch19/python/solutions/ex19_3_incident_evidence.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.monitor import load_log

df = load_log("data/logs/requests_2026_10.jsonl")

sf = df[(df.domain == "sf") & (df.status != "error")]
print(sf.groupby("prompt").status.apply(lambda s: round((s != "verified").mean(), 3)))
print(sf.groupby("prompt").size())
