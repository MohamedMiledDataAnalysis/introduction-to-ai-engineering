"""Extract KID data into a schema, one document per call, and check every value three ways."""
import json
import re

import pandas as pd

from aie.validate import validate

SCHEMA = json.load(open("prompts/kid_schema.json"))
DOC_FORMAT = {"management_costs_pct": "{:.2f}%", "transaction_costs_pct": "{:.2f}%", "summary_risk_indicator": "{} on a scale",
              "recommended_holding_period_years": "{} years", "moderate_scenario_rhp_eur": "EUR {:,.0f}",
              "entry_costs_eur": "EUR {:,.0f}", "isin": "{}"}


def isin_valid(code):
    digits = "".join(str(int(ch, 36)) for ch in code[:-1])
    total = sum((d * 2 - 9 if d * 2 > 9 else d * 2) if i % 2 == 0 else d
                for i, d in enumerate(int(x) for x in reversed(digits)))
    return (10 - total % 10) % 10 == int(code[-1])


def check_extraction(obj, document, fund_row):
    problems = [f"schema: {e}" for e in validate(obj, SCHEMA)]
    for field, fmt in DOC_FORMAT.items():           # 1. the value is written in the document, as the KID writes it
        if obj.get(field) is not None and fmt.format(obj[field]) not in document:
            problems.append(f"{field} = {obj[field]} not found in the document as '{fmt.format(obj[field])}'")
    if obj.get("isin") and not isin_valid(obj["isin"]):   # 2. identifiers are valid
        problems.append("isin check digit is wrong")
    if obj.get("summary_risk_indicator") != fund_row["sri"]:          # 3. agrees with the fund master data
        problems.append(f"risk indicator {obj.get('summary_risk_indicator')} differs from the fund master ({fund_row['sri']})")
    if obj.get("management_costs_pct") is not None and round(obj["management_costs_pct"] / 100, 6) != round(fund_row["ocf"], 6):
        problems.append(f"management costs {obj['management_costs_pct']}% differ from the fund master's "
                        f"ongoing charges ({100 * fund_row['ocf']:.2f}%)")
    return problems


def extract_kid(code):
    from aie.llm import chat
    from aie.prompts import load_prompt, render
    from aie.validate import parse_json_reply
    document = open(f"data/am/documents/{code.lower()}_kid.md", encoding="utf-8").read()
    template, version = load_prompt("extract_kid_v1")
    reply = chat([{"role": "user", "content": render(template, document=document)}], format=SCHEMA)
    return parse_json_reply(reply["text"]), version
