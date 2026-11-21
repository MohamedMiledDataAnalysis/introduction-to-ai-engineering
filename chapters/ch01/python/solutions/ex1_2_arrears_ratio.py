# Exercise 1.2 - Arrears ratio by balance at 30 September 2026
# Run from the root of the repository:  python chapters/ch01/python/solutions/ex1_2_arrears_ratio.py

import pandas as pd

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep = tape[tape["RREL6"] == "2026-09-30"]
arrears = sep.loc[sep["RREL69"] == "ARRE", "RREL30"].sum()
pool = sep["RREL30"].sum()
print(f"Balance in arrears: GBP {arrears:,.2f}")
print(f"Pool balance:       GBP {pool:,.2f}")
print(f"Arrears ratio:      {arrears / pool:.2%}")
