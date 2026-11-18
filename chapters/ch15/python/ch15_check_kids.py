# Chapter 15 - Check three KID extractions against the document, the ISIN rule and the fund master data
import json
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.kid_extract import check_extraction

funds = pd.read_csv("data/am/funds.csv").set_index("fund_code")
candidates = json.load(open("evals/candidates/kid_extractions.json"))
truth = json.load(open("evals/kid_truth.json"))
for code, obj in candidates.items():
    document = open(f"data/am/documents/{code.lower()}_kid.md", encoding="utf-8").read()
    problems = check_extraction(obj, document, funds.loc[code])
    wrong = [f for f in obj if obj[f] != truth[code][f]]
    print(f"{code}: {'accepted' if not problems else 'REJECTED'}   (fields actually wrong: {wrong or 'none'})")
    for p in problems:
        print("   -", p)
