# Exercise 22.1 - Characteristics of the three funds
# Run from the root of the repository:  python chapters/ch22/python/solutions/ex22_1_characteristics.py

import sys; sys.path.insert(0, ".")
from aie.tools import fund_characteristics
for f in ("HGEF", "HECB", "HBMA"):
    print(fund_characteristics(f))
