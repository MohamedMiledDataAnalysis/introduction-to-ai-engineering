# Exercise 5.2 - Numbers written in words
# Run from the root of the repository:  python chapters/ch05/python/solutions/ex5_2_numbers_in_words.py

import re
import sys

import pandas as pd

sys.path.insert(0, ".")
import aie.evals
from aie.evals import NUMBER, run_eval

WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
         "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
         "twelve": 12}

def numbers_in(text):
    for word, value in WORDS.items():
        text = re.sub(rf"\b{word}\b", str(value), text, flags=re.I)
    return [float(n.replace(",", "")) for n in NUMBER.findall(text)
            if any(ch.isdigit() for ch in n)]

aie.evals.numbers_in = numbers_in          # the scorers now use the new function

cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str, keep_default_na=False)
for run in ("a", "b"):
    answers = pd.read_csv(f"evals/candidates/prospectus_qa_run_{run}.csv") \
                .set_index("id")["answer"].to_dict()
    res = run_eval(cases, answers)
    print(f"Run {run.upper()}: {res.passed.sum()}/{len(res)} passed; "
          f"failures: {res[~res.passed].id.tolist()}")
