# Chapter 10 - Score a no-model baseline on the prospectus evaluation set; the model must beat it
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.evals import run_eval, wilson_interval
from aie.prospectus_qa import answer_extractive, build_index

index = build_index()
cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str,
                    keep_default_na=False)
answers = {c["id"]: answer_extractive(c["question"], index)["answer"]
           for c in cases.to_dict("records")}
res = run_eval(cases, answers)
low, high = wilson_interval(res.passed.sum(), len(res))
print(f"Extractive baseline: {res.passed.sum()}/{len(res)} passed "
      f"(95% interval {low:.0%}-{high:.0%})")
for r in res[~res.passed].itertuples():
    print(f"  {r.id}  {r.reason:<45} {answers[r.id][:70]}")
