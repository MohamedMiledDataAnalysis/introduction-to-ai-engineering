# Exercise 1.1 - Number of loans by account status at 30 September 2026
# Run from the root of the repository:  python chapters/ch01/python/solutions/ex1_1_status_counts.py

import pandas as pd

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep = tape[tape["RREL6"] == "2026-09-30"]
print(sep["RREL69"].value_counts())
