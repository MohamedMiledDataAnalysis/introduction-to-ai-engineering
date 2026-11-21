# Exercise 15.2 - A positional check for the moderate scenario
# Run from the root of the repository:  python chapters/ch15/python/solutions/ex15_2_positional_check.py

import json
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.kid_extract import check_extraction

funds = pd.read_csv("data/am/funds.csv").set_index("fund_code")
truth = json.load(open("evals/kid_truth.json"))
candidates = json.load(open("evals/candidates/kid_extractions.json"))
import re

def moderate_rhp_in_document(document):
    m = re.search(r"^\| Moderate \|[^\n]*\| EUR ([\d,]+) \|\s*$", document, re.M)
    return float(m.group(1).replace(",", "")) if m else None


def check_extraction_rhp(obj, document, fund_row):
    """check_extraction(), plus the positional check of the moderate scenario."""
    problems = check_extraction(obj, document, fund_row)
    expected = moderate_rhp_in_document(document)
    if expected is not None and obj.get("moderate_scenario_rhp_eur") != expected:
        problems.append(f"moderate scenario {obj['moderate_scenario_rhp_eur']} "
                        f"is not the RHP column value ({expected})")
    return problems


for code, obj in candidates.items():
    document = open(f"data/am/documents/{code.lower()}_kid.md", encoding="utf-8").read()
    print(code, check_extraction_rhp(obj, document, funds.loc[code]) or "accepted")
