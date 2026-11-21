# Exercise 16.2 - Extract and reconcile three reports
# Run from the root of the repository:  python chapters/ch16/python/solutions/ex16_2_three_reports.py

import sys

sys.path.insert(0, ".")
from aie.servicer_pdf import extract_report, pdf_text, reconcile_report

for cutoff in ("2026-07-31", "2026-08-31", "2026-09-30"):
    path = ("data/sf/rmbs/servicer_reports/"
            f"servicer_report_{cutoff[:7].replace('-', '_')}.pdf")
    obj, schema_errors, version = extract_report(path)
    table = reconcile_report(obj, pdf_text(path), cutoff)
    print(cutoff, schema_errors or "schema ok")
    print(table.verdict.value_counts().to_string())
