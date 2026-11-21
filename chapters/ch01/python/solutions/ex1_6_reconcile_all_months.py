# Exercise 1.6 - Reconcile notes, PDL and pool for every month
# Run from the root of the repository:  python chapters/ch01/python/solutions/ex1_6_reconcile_all_months.py

import pandas as pd

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
notes = pd.read_csv("data/sf/rmbs/larkfield_2025_1_notes.csv")

pool = tape.groupby("RREL6")["RREL30"].sum()
notes_out = notes.groupby("cutoff")["closing"].sum()
pdl = notes.groupby("cutoff")["pdl_balance"].sum()

check = (notes_out - pdl - pool).round(2)
print(check.to_string())
print("Largest absolute difference:", check.abs().max())
