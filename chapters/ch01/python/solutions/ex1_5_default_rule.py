# Exercise 1.5 - Check the prospectus definition of a Defaulted Loan against the tape
# Run from the root of the repository:  python chapters/ch01/python/solutions/ex1_5_default_rule.py

import pandas as pd

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
defaulted = tape[tape["RREL69"] == "DFLT"]
print("Rows with status DFLT:       ", len(defaulted))
print("Distinct defaulted loans:    ", defaulted["RREL2"].nunique())
print("Minimum days in arrears:     ", defaulted["RREL68"].min())
print("Rows breaking the rule:      ", (defaulted["RREL68"] < 180).sum())
