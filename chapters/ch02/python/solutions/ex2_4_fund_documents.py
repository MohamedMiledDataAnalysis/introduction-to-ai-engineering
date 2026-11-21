# Exercise 2.4 - Tokens of the fund documents
# Run from the root of the repository:  python chapters/ch02/python/solutions/ex2_4_fund_documents.py

import pandas as pd

prospectus = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
                  encoding="utf-8").read()
tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
one_month = tape[tape["RREL6"] == "2026-09-30"]
csv_text = one_month.to_csv(index=False)

CHARS_PER_TOKEN = 4      # budgeting rule for English text; measure yours
CONTEXT_WINDOW = 16_384  # tokens: the window chat() asks for (Chapter 3)

for name, s in [("Prospectus excerpt", prospectus),
                ("Loan tape, one month", csv_text)]:
    est = len(s) / CHARS_PER_TOKEN
    print(f"{name:<22} {len(s):>10,} characters  ~{est:>9,.0f} tokens  "
          f"{est / CONTEXT_WINDOW:>6.1f} x the window")

per_row = len(csv_text) / len(one_month) / CHARS_PER_TOKEN
print(f"\nOne loan row: ~{per_row:.0f} tokens; rows that fit in the window: "
      f"~{CONTEXT_WINDOW / per_row:,.0f}")

docs = {name: open(f"data/am/documents/{name}", encoding="utf-8").read()
        for name in ["hgef_factsheet_2026_09.md", "hgef_kid.md",
                     "hecb_kid.md", "hbma_kid.md"]}
for name, s in docs.items():
    print(f"{name:<28} {len(s):>6,} characters  ~{len(s) / 4:>6,.0f} tokens")
kids = sum(len(s) for n, s in docs.items() if n.endswith("kid.md")) / 4
print(f"Three KIDs together: ~{kids:,.0f} tokens")
