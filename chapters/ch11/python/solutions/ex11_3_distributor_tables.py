# Exercise 11.3 - Tables for a distributor
# Run from the root of the repository:  python chapters/ch11/python/solutions/ex11_3_distributor_tables.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.sqlguard import run_sql

cands = pd.read_csv("evals/candidates/am_sql_candidates.csv").set_index("id")["sql"]

DISTRIBUTOR_TABLES = {"funds", "securities", "holdings", "nav",
                      "benchmark_returns", "issuer_esg"}
print(run_sql(cands["S07"], allowed_tables=DISTRIBUTOR_TABLES))
