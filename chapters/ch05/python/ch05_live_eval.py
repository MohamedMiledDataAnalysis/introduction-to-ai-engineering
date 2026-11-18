# Chapter 5 - Run the evaluation against the live assistant and save the answers
import re
import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, ".")
from aie.evals import run_eval, wilson_interval
from aie.llm import chat

PROSPECTUS = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md", encoding="utf-8").read()
SYSTEM = ("You answer questions about the Larkfield Mortgage Funding 2025-1 prospectus using only the "
          "text provided. Quote figures exactly as written. If the text does not contain the answer, "
          "say: 'The document does not state this.'")

cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str, keep_default_na=False)
answers = {}
for case in cases.to_dict("records"):
    reply = chat(system=SYSTEM, messages=[{"role": "user",
                 "content": f"TEXT:\n{PROSPECTUS}\n\nQUESTION: {case['question']}"}])
    answers[case["id"]] = reply["text"].strip()

stamp = datetime.now().strftime("%Y%m%d_%H%M")
pd.DataFrame({"id": list(answers), "answer": list(answers.values())}) \
    .to_csv(f"evals/candidates/prospectus_qa_live_{stamp}.csv", index=False)

res = run_eval(cases, answers)
low, high = wilson_interval(res.passed.sum(), len(res))
print(f"Live run: {res.passed.sum()}/{len(res)} passed; 95% interval {low:.0%} to {high:.0%}")
print(res[~res.passed][["id", "reason"]].to_string(index=False))
