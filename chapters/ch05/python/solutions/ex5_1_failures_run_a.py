# Exercise 5.1 - Run A's failures and their reasons
# Run from the root of the repository:  python chapters/ch05/python/solutions/ex5_1_failures_run_a.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.evals import compare_runs, run_eval

cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str,
                    keep_default_na=False)
results = {}
for run in ("a", "b"):
    answers = pd.read_csv(f"evals/candidates/prospectus_qa_run_{run}.csv") \
                .set_index("id")["answer"].to_dict()
    res = run_eval(cases, answers)
    results[run] = res
    print(f"Run {run.upper()}: {res.passed.sum()}/{len(res)} passed "
          f"({res.passed.mean():.0%})")
    print(res.groupby("answer_type").passed.agg(["sum", "count"])
             .to_string(), "\n")

print("Failures in run A:")
print(results["a"][~results["a"].passed][["id", "reason"]]
      .to_string(index=False))

print("Failures in run B:")
print(results["b"][~results["b"].passed][["id", "reason"]]
      .to_string(index=False))

regressions, fixes = compare_runs(results["a"], results["b"])
print("\nRegressions from A to B:", regressions)
print("Fixes from A to B:      ", fixes)
