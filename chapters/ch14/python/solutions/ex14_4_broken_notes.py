# Exercise 14.4 - Break the notes file on purpose
# Run from the root of the repository:  python chapters/ch14/python/solutions/ex14_4_broken_notes.py

import sys; sys.path.insert(0, ".")

import tempfile
from pathlib import Path

import pandas as pd
import aie.investor_report as ir

notes = pd.read_csv(ir.NOTES)
mask = (notes.cutoff == "2026-09-30") & (notes.cls == "B")
notes.loc[mask, "closing"] -= 100
broken = Path(tempfile.gettempdir()) / "notes_broken.csv"
notes.to_csv(broken, index=False)

ir.NOTES = str(broken)
print(ir.reconcile(ir.month_figures("2026-09-30")))
