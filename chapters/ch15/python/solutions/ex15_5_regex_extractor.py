# Exercise 15.5 - A regular-expression extractor
# Run from the root of the repository:  python chapters/ch15/python/solutions/ex15_5_regex_extractor.py

import re

def regex_extract(document):
    sri = re.search(r"Risk indicator:\*\* (\d) on a scale", document)
    oc = re.search(r"operating costs \| ([\d.]+)% of the value", document)
    return {"summary_risk_indicator": int(sri.group(1)) if sri else None,
            "management_costs_pct": float(oc.group(1)) if oc else None}

import json

truth = json.load(open("evals/kid_truth.json"))
for code in ("HGEF", "HECB", "HBMA"):
    doc = open(f"data/am/documents/{code.lower()}_kid.md", encoding="utf-8").read()
    got = regex_extract(doc)
    print(code, got, "equal to the truth:",
          all(got[k] == truth[code][k] for k in got))
