# Exercise 10.3 - The model against the baseline
# Run from the root of the repository:  python chapters/ch10/python/solutions/ex10_3_model_against_baseline.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.evals import compare_runs, run_eval
from aie.prospectus_qa import answer_extractive, answer_llm, build_index

index = build_index()
cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str,
                    keep_default_na=False)

base = run_eval(cases, {c["id"]: answer_extractive(c["question"], index)["answer"]
                        for c in cases.to_dict("records")})
model = run_eval(cases, {c["id"]: answer_llm(c["question"], index)["answer"]
                         for c in cases.to_dict("records")})
print(compare_runs(base, model))
