# Chapter 11 - Check model-written SQL: guard it, run it read-only, compare its result with the reference
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.sqlguard import run_sql, same_result

cases = pd.read_csv("evals/am_sql_qa.csv")
cands = pd.read_csv("evals/candidates/am_sql_candidates.csv") \
          .set_index("id")["sql"]
passed = 0
for c in cases.itertuples():
    ref = run_sql(c.reference_sql)
    got = run_sql(cands[c.id])
    ok = same_result(ref, got, ordered=bool(c.ordered))
    passed += ok
    detail = got["error"] if "error" in got else f"rows={got['rows'][:2]}"
    print(f"{c.id} {'PASS' if ok else 'FAIL'}  reference rows={ref['rows'][:2]}"
          f"\n      candidate {detail}")
print(f"\n{passed}/{len(cases)} candidate queries return the reference result")
