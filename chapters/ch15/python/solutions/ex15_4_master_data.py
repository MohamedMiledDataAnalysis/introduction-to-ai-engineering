# Exercise 15.4 - When the master data disagrees
# Run from the root of the repository:  python chapters/ch15/python/solutions/ex15_4_master_data.py

import json
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.kid_extract import check_extraction

funds = pd.read_csv("data/am/funds.csv").set_index("fund_code")
truth = json.load(open("evals/kid_truth.json"))
candidates = json.load(open("evals/candidates/kid_extractions.json"))

f = funds.copy()
f.loc["HECB", "ocf"] = 0.0038
doc = open("data/am/documents/hecb_kid.md", encoding="utf-8").read()
print(check_extraction(truth["HECB"], doc, f.loc["HECB"]))
