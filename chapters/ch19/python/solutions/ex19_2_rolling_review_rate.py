# Exercise 19.2 - A rolling review rate
# Run from the root of the repository:  python chapters/ch19/python/solutions/ex19_2_rolling_review_rate.py

import sys


sys.path.insert(0, ".")
from aie.monitor import load_log

df = load_log("data/logs/requests_2026_10.jsonl")

ok = df[df.status != "error"]
def rolling_review(domain, window=5):
    x = ok[ok.domain == domain]
    flagged = x.groupby("day").status.apply(lambda s: (s != "verified").sum())
    total = x.groupby("day").size()
    return (flagged.rolling(window).sum() / total.rolling(window).sum()).round(3)
r = rolling_review("sf")
print(r[r > 0.10])

r_am = rolling_review("am")
print("AM maximum:", r_am.max())
