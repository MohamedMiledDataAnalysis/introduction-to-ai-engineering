# Exercise 13.2 - Allocation and selection both detracted
# Run from the root of the repository:  python chapters/ch13/python/solutions/ex13_2_both_detracted.py

import pandas as pd

attr = pd.read_csv("data/am/hgef_attribution_2026_09.csv")

print(100 * attr.allocation.sum(), 100 * attr.selection.sum(),
      100 * attr.interaction.sum())
