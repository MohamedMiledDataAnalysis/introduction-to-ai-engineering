"""Read a servicer report PDF, extract its figures into a schema, and reconcile them with the loan data."""
import json

import pandas as pd
from pypdf import PdfReader

SCHEMA = json.load(open("prompts/servicer_report_schema.json"))


def pdf_text(path):
    return "\n".join(page.extract_text() for page in PdfReader(path).pages)


def extract_report(path):
    from aie.llm import chat
    from aie.prompts import load_prompt, render
    from aie.validate import parse_json_reply, validate
    template, version = load_prompt("extract_servicer_report_v1")
    reply = chat([{"role": "user", "content": render(template, report=pdf_text(path))}], format=SCHEMA)
    obj = parse_json_reply(reply["text"])
    return obj, validate(obj, SCHEMA), version


def independent_figures(cutoff):
    """The same figures, computed from the loan-level data the servicer also sends."""
    tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
    cf = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_cashflows.csv")
    m, c = tape[tape.RREL6 == cutoff], cf[cf.cutoff == cutoff]
    return {"interest_collected_gbp": round(c.interest.sum(), 2), "scheduled_principal_gbp": round(c.sched_principal.sum(), 2),
            "prepayments_gbp": round(c.prepayment.sum(), 2), "recoveries_gbp": round(c.recovery.sum(), 2),
            "loans_outstanding": int((m.RREL30 > 0).sum()), "pool_balance_gbp": round(m.RREL30.sum(), 2),
            "new_defaults_gbp": round(c.new_default.sum(), 2)}


def figure_in_text(value, text):
    """Is the value written in the report text (as GBP 1,234.56 or as a count)?"""
    return (f"{value:,.2f}" in text) if isinstance(value, float) else (f"{value:,}" in text)


def reconcile_report(extracted, text, cutoff, tolerance=0.01):
    """For each field: is the extraction faithful to the report, and does the report agree with the loan data?"""
    ind = independent_figures(cutoff)
    rows = []
    for field, expected in ind.items():
        got = extracted.get(field)
        in_report = got == 0 or figure_in_text(got, text)
        diff = None if got is None else round(got - expected, 2)
        verdict = ("extraction error: value not in the report" if not in_report else
                   "agrees" if abs(diff) <= tolerance else "REPORT DISAGREES WITH LOAN DATA")
        rows.append({"field": field, "extracted": got, "loan_data": expected, "difference": diff, "verdict": verdict})
    return pd.DataFrame(rows)
