# Exercise 6.1 - Check a fund commentary
# Run from the root of the repository:  python chapters/ch06/python/solutions/ex6_1_fund_commentary.py

import sys; sys.path.insert(0, ".")
import pandas as pd
from aie.factcheck import check_text

nav = pd.read_csv("data/am/fund_nav_monthly.csv")
bm = pd.read_csv("data/am/benchmark_returns_monthly.csv")
f = nav[nav["fund_code"] == "HGEF"].set_index("month_end")["net_return"]
b = bm.set_index("month_end")["HGEF"]
facts = {
    "fund 1 month": (100 * f.iloc[-1], "percent"),
    "benchmark 1 month": (100 * b.iloc[-1], "percent"),
    "relative 1 month": (100 * (f.iloc[-1] - b.iloc[-1]), "percent"),
    "fund 1 year": (100 * ((1 + f.iloc[-12:]).prod() - 1), "percent"),
    "benchmark 1 year": (100 * ((1 + b.iloc[-12:]).prod() - 1), "percent"),
}
draft = ("In September the fund returned 4.53% against 5.03% for its benchmark, "
         "lagging by 0.49%. Over one year the fund gained 6.46%, behind the "
         "benchmark's 7.86%.")
for fig, hits in check_text(draft, facts):
    print(f"  {fig.raw:<7} {'OK  ' + ', '.join(hits) if hits else 'NOT SUPPORTED'}")
