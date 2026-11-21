# Exercise 20.2 - The evaluation of the SQL assistant
# Run from the root of the repository:  python chapters/ch20/python/solutions/ex20_2_sql_model_card.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.evals import wilson_interval

from aie.sqlguard import run_sql, same_result

cases = pd.read_csv("evals/am_sql_qa.csv")
cands = pd.read_csv("evals/candidates/am_sql_candidates.csv").set_index("id")["sql"]
passed = [same_result(run_sql(c.reference_sql), run_sql(cands[c.id]), bool(c.ordered))
          for c in cases.itertuples()]
k, n = sum(passed), len(passed)
low, high = wilson_interval(k, n)
failed = [c for c, p in zip(cases.id, passed) if not p]

print(f"Evaluation: {k}/{n} passed (95% interval {low:.0%} to {high:.0%}), failed cases: {failed}")
