# Exercise 10.2 - The baseline's threshold
# Run from the root of the repository:  python chapters/ch10/python/solutions/ex10_2_threshold.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.evals import run_eval
from aie.prospectus_qa import answer_extractive, build_index

index = build_index()
cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str,
                    keep_default_na=False)

for t in (0, 2, 4, 6, 8):
    answers = {c["id"]: answer_extractive(c["question"], index, t)["answer"]
               for c in cases.to_dict("records")}
    res = run_eval(cases, answers)
    print(t, res.passed.sum(), res[~res.passed].id.tolist())
