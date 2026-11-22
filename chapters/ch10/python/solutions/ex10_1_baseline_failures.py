# Exercise 10.1 - Why the baseline fails
# Run from the root of the repository:  python chapters/ch10/python/solutions/ex10_1_baseline_failures.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.prospectus_qa import answer_extractive, build_index

index = build_index()
cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str,
                    keep_default_na=False)

fails = ["Q01", "Q02", "Q03", "Q04", "Q07", "Q08", "Q13", "Q16"]
for c in cases[cases.id.isin(fails)].to_dict("records"):
    best, score = index.search(c["question"], 1)[0]
    out = answer_extractive(c["question"], index)
    print(c["id"], c["source_section"], best["id"], round(score, 2), out["answer"][:60])
