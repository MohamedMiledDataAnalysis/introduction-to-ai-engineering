# Exercise 6.3 - Direction words must agree with the sign
# Run from the root of the repository:  python chapters/ch06/python/solutions/ex6_3_direction_words.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.factcheck import check_text

nav = pd.read_csv("data/am/fund_nav_monthly.csv")
bm = pd.read_csv("data/am/benchmark_returns_monthly.csv")
f = nav[nav["fund_code"] == "HGEF"].set_index("month_end")["net_return"]
b = bm.set_index("month_end")["HGEF"]
facts = {
    "fund 1 month": (100 * f.iloc[-1], "percent"),
    "benchmark 1 month": (100 * b.iloc[-1], "percent"),
    "relative 1 month": (100 * (f.iloc[-1] - b.iloc[-1]), "percent"),
}

POSITIVE = ["outperformed", "outperforming", "ahead of", "beat", "above"]
NEGATIVE = ["lagged", "lagging", "behind", "underperformed", "below"]

def direction_errors(text, facts, window=40):
    errors = []
    for fig, hits in check_text(text, facts):
        for name in hits:
            if not name.startswith("relative"):
                continue
            context = text[max(0, fig.start - window):fig.start].lower()
            sign = facts[name][0]
            if sign < 0 and any(w in context for w in POSITIVE):
                errors.append(f"{fig.raw}: says ahead, fact is negative")
            if sign > 0 and any(w in context for w in NEGATIVE):
                errors.append(f"{fig.raw}: says behind, fact is positive")
    return errors

for draft in ["In September the fund returned 4.53% against 5.03% for its benchmark, lagging by 0.50%.",
              "In September the fund returned 4.53% against 5.03% for its benchmark, outperforming by 0.50%."]:
    print(direction_errors(draft, facts) or "no error", "<-", draft[-30:])
