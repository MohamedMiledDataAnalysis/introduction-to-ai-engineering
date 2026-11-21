# Exercise 14.3 - What became of March's arrears
# Run from the root of the repository:  python chapters/ch14/python/solutions/ex14_3_march_arrears.py

import sys; sys.path.insert(0, ".")
import pandas as pd
from aie.investor_report import TAPE

t = pd.read_csv(TAPE)
march = set(t[(t.RREL6 == "2026-03-31") & (t.RREL69 == "ARRE")].RREL2)
sep = t[t.RREL6 == "2026-09-30"].set_index("RREL2")["RREL69"]
print(len(march))
print(pd.Series({l: sep.get(l, "gone") for l in march}).value_counts())
