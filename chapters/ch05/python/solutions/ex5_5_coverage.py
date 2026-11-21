# Exercise 5.5 - Coverage of the evaluation set by section
# Run from the root of the repository:  python chapters/ch05/python/solutions/ex5_5_coverage.py

import pandas as pd

cases = pd.read_csv("evals/sf_prospectus_qa.csv")
print(cases.source_section.value_counts().sort_index())
