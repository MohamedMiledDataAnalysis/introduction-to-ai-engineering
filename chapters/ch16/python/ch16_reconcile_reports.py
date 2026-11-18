# Chapter 16 - Reconcile extracted servicer report figures with the report text and with the loan data
import json
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.servicer_pdf import pdf_text, reconcile_report

pd.set_option("display.width", 120)
extractions = json.load(open("evals/candidates/servicer_report_extractions.json"))
for cutoff, extracted in extractions.items():
    text = pdf_text(f"data/sf/rmbs/servicer_reports/servicer_report_{cutoff[:7].replace('-', '_')}.pdf")
    table = reconcile_report(extracted, text, cutoff)
    print(f"\n{extracted['collection_period']}")
    print(table[["field", "extracted", "loan_data", "difference", "verdict"]].to_string(index=False))
