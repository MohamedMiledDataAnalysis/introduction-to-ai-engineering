# Exercise 13.1 - The attribution identity
# Run from the root of the repository:  python chapters/ch13/python/solutions/ex13_1_attribution_identity.py

import pandas as pd
attr = pd.read_csv("data/am/hgef_attribution_2026_09.csv")
total_active = (attr.allocation + attr.selection + attr.interaction).sum()

nav = pd.read_csv("data/am/fund_nav_monthly.csv")
net = nav[(nav.fund_code == "HGEF") & (nav.month_end == "2026-09-30")].net_return.iloc[0]
gross = net + 0.0075 / 12
bench = pd.read_csv("data/am/benchmark_returns_monthly.csv").set_index("month_end").loc["2026-09-30", "HGEF"]
print(round(100 * total_active, 4), round(100 * (gross - bench), 4))
