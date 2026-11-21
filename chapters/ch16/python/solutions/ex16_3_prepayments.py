# Exercise 16.3 - Full and partial prepayments
# Run from the root of the repository:  python chapters/ch16/python/solutions/ex16_3_prepayments.py

import pandas as pd

cf = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_cashflows.csv")
sep = cf[(cf.cutoff == "2026-09-30") & (cf.prepayment > 0)]
print(len(sep), round(sep.prepayment.sum(), 2))

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
redeemed = tape[(tape.RREL6 == "2026-09-30") & (tape.RREL69 == "REDM")].RREL2
full = sep[sep.loan.isin(redeemed)]
print(len(full), round(full.prepayment.sum(), 2), round(sep.prepayment.sum() - full.prepayment.sum(), 2))
