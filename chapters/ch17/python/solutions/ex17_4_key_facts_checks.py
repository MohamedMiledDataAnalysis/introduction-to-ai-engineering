# Exercise 17.4 - Checks of the extracted key facts
# Run from the root of the repository:  python chapters/ch17/python/solutions/ex17_4_key_facts_checks.py

import json
import re

def check_key_facts(obj, note):
    problems = []
    fmt = {"target_price_eur": "EUR {:.2f}", "revenue_growth_pct": "{:.1f}%",
           "operating_margin_pct": "{:.1f}%", "previous_margin_pct": "{:.1f}%",
           "net_debt_to_ebitda": "{:.1f} times"}
    for field, f in fmt.items():
        if obj.get(field) is not None and f.format(obj[field]) not in note:
            problems.append(f"{field} = {obj[field]} not written in the note")
    rec = re.search(r"Recommendation: (\w+)", note)
    if not rec or rec.group(1) != obj["recommendation"]:
        problems.append("recommendation differs from the note's Recommendation line")
    if obj.get("main_risk") and obj["main_risk"] not in note:
        problems.append("main risk is not a phrase of the note")
    if obj["issuer"] not in note.split("\n")[0]:
        problems.append("issuer is not the name in the title")
    return problems

key_facts = json.load(open("data/am/research/key_facts.json"))
note = open("data/am/research/R01.md", encoding="utf-8").read()
print(check_key_facts(key_facts["R01"], note) or "no problem")
print(check_key_facts(dict(key_facts["R01"], target_price_eur=32.36), note))
