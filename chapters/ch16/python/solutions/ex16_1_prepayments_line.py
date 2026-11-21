# Exercise 16.1 - The prepayments line in each library
# Run from the root of the repository:  python chapters/ch16/python/solutions/ex16_1_prepayments_line.py

import sys; sys.path.insert(0, ".")
from aie.servicer_pdf import pdf_text

text = pdf_text("data/sf/rmbs/servicer_reports/servicer_report_2026_09.pdf")
lines = text.split("\n")
i = next(k for k, l in enumerate(lines) if "Prepayments" in l)
print(lines[i:i + 2])
