# Exercise 5.3 - A choice scorer for Q10
# Run from the root of the repository:  python chapters/ch05/python/solutions/ex5_3_choice_scorer.py

import sys

sys.path.insert(0, ".")
from aie.evals import score_one


def score_choice(case, answer):
    kind = case["answer_type"]
    if kind == "choice":
        options = [o.strip().lower() for o in str(case["keywords"]).split("|")]
        present = [o for o in options if o in answer.lower()]
        ok = present == [case["expected"].lower()]
        return ok, "choice correct" if ok else f"found {present}"
    return score_one(case, answer)


q10 = {"answer_type": "choice", "expected": "revenue", "keywords": "revenue|principal"}
for answer in ["Recoveries are not revenue receipts; they are principal receipts.",
               "Recoveries on Defaulted Loans are revenue receipts."]:
    print(score_choice(q10, answer), "<-", answer)
