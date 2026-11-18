# Chapter 10 - Evaluate the model-based assistant: answers, grounding and retrieval, side by side
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.evals import run_eval, wilson_interval
from aie.prospectus_qa import answer_llm, build_index

index = build_index()
cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str, keep_default_na=False)
outputs = {c["id"]: answer_llm(c["question"], index) for c in cases.to_dict("records")}
res = run_eval(cases, {k: v["answer"] for k, v in outputs.items()})

grounded = sum(not o["problems"] for o in outputs.values())
answerable = cases[cases["source_section"] != ""]
retrieved_ok = sum(any(r.split("#")[1].split(".")[0] == c["source_section"] for r in outputs[c["id"]]["retrieved"])
                   for c in answerable.to_dict("records"))
low, high = wilson_interval(res.passed.sum(), len(res))
print(f"prompt {next(iter(outputs.values()))['prompt']}")
print(f"answers correct : {res.passed.sum()}/{len(res)} ({low:.0%}-{high:.0%})")
print(f"answers grounded: {grounded}/{len(res)}")
print(f"retrieval hits  : {retrieved_ok}/{len(answerable)}")
for r in res[~res.passed].itertuples():
    print(f"  {r.id}  {r.reason}  | problems: {outputs[r.id]['problems']}")
