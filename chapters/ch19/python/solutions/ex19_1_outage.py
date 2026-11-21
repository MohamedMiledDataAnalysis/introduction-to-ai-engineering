# Exercise 19.1 - The outage of 7 October
# Run from the root of the repository:  python chapters/ch19/python/solutions/ex19_1_outage.py

import sys; sys.path.insert(0, ".")
from aie.monitor import load_log
df = load_log("data/logs/requests_2026_10.jsonl")
err = df[df.status == "error"]
print(err.ts.min(), err.ts.max(), err.groupby("domain").size().to_dict())
print(err.seconds.min(), err.seconds.max())
