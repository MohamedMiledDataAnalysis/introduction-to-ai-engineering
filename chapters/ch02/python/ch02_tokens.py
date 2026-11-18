# Chapter 2 - How much text fits in a model's context window?
import pandas as pd

prospectus = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
                  encoding="utf-8").read()
tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
one_month = tape[tape["RREL6"] == "2026-09-30"]
csv_text = one_month.to_csv(index=False)

CHARS_PER_TOKEN = 4      # budgeting rule for English text; measure yours
CONTEXT_WINDOW = 32_000  # tokens; check the figure for your model

for name, s in [("Prospectus excerpt", prospectus),
                ("Loan tape, one month", csv_text)]:
    est = len(s) / CHARS_PER_TOKEN
    print(f"{name:<22} {len(s):>10,} characters  ~{est:>9,.0f} tokens  "
          f"{est / CONTEXT_WINDOW:>6.1f} x the window")

per_row = len(csv_text) / len(one_month) / CHARS_PER_TOKEN
print(f"\nOne loan row: ~{per_row:.0f} tokens; rows that fit in the window: "
      f"~{CONTEXT_WINDOW / per_row:,.0f}")
