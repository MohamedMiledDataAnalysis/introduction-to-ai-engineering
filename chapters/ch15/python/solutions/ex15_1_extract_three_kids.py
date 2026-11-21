# Exercise 15.1 - Extract and check the three KIDs
# Run from the root of the repository:  python chapters/ch15/python/solutions/ex15_1_extract_three_kids.py

import json, sys
sys.path.insert(0, ".")
import pandas as pd
from aie.kid_extract import extract_kid, check_extraction

funds = pd.read_csv("data/am/funds.csv").set_index("fund_code")
truth = json.load(open("evals/kid_truth.json"))
for code in ("HGEF", "HECB", "HBMA"):
    obj, version = extract_kid(code)
    document = open(f"data/am/documents/{code.lower()}_kid.md",
                    encoding="utf-8").read()
    problems = check_extraction(obj, document, funds.loc[code])
    wrong = [f for f in obj if obj.get(f) != truth[code][f]]
    print(code, problems or "accepted", "| wrong:", wrong or "none")
