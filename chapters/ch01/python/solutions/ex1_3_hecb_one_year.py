# Exercise 1.3 - One-year return of the euro corporate bond fund, checked against the factsheet
import pandas as pd

nav = pd.read_csv("data/am/fund_nav_monthly.csv")
bm = pd.read_csv("data/am/benchmark_returns_monthly.csv")

fund = nav[nav["fund_code"] == "HECB"].tail(12)["net_return"]
bench = bm.tail(12)["HECB"]
fund_1y = (1 + fund).prod() - 1
bench_1y = (1 + bench).prod() - 1
print(f"Fund 1 year:      {fund_1y:.2%}")
print(f"Benchmark 1 year: {bench_1y:.2%}")
print(f"Relative:         {fund_1y - bench_1y:+.2%}")
print(f"Relative from the rounded figures: "
      f"{round(fund_1y * 100, 2) - round(bench_1y * 100, 2):+.2f}%")
