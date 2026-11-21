# Exercise 17.3 - The direction of the margin
# Run from the root of the repository:  python chapters/ch17/python/solutions/ex17_3_margin_direction.py

import json
import re

def margin_direction_errors(summary, key):
    if key["operating_margin_pct"] == key["previous_margin_pct"]:
        up = None
    else:
        up = key["operating_margin_pct"] > key["previous_margin_pct"]
    problems = []
    for clause in re.split(r"[.;,]|\band\b", summary.lower()):
        if "margin" not in clause:
            continue
        said_up = re.search(r"\b(rose|increased|up|higher|improved|widened)\b", clause)
        said_down = re.search(r"\b(fell|declined|down|lower|narrowed)\b", clause)
        if said_up and up is not True:
            problems.append("says the margin rose; it did not")
        if said_down and up is not False:
            problems.append("says the margin fell; it did not")
    return problems

key_facts = json.load(open("data/am/research/key_facts.json"))
r03 = key_facts["R03"]
print(margin_direction_errors("the operating margin rose to 14.9%", r03))
print(margin_direction_errors("Revenue grew 8.2% and the operating margin fell to 14.9% from 15.5%",
                              key_facts["R02"]) or "no error")
