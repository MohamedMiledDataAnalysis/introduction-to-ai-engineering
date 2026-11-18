# Chapter 6 - Check every figure in two draft commentaries against facts computed from the data
import re
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.factcheck import check_text, forbidden_phrases

CUT = "2026-09-30"
tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
wf = pd.read_csv("data/sf/rmbs/larkfield_2025_1_waterfall.csv")
notes = pd.read_csv("data/sf/rmbs/larkfield_2025_1_notes.csv")

sep = tape[tape["RREL6"] == CUT]
w = wf[wf["cutoff"] == CUT].set_index("item")["paid"]
n = notes[notes["cutoff"] == CUT].set_index("cls")
pool = sep["RREL30"].sum()

facts = {   # name: (value, unit)   - every figure a commentary may quote
    "revenue receipts": (w["Available revenue receipts"], "money"),
    "principal receipts": (w["Available principal receipts"], "money"),
    "Class A principal paid": (n.loc["A", "principal_paid"], "money"),
    "Class A closing balance": (n.loc["A", "closing"], "money"),
    "pool balance": (pool, "money"),
    "arrears ratio": (100 * sep.loc[sep["RREL69"] == "ARRE", "RREL30"].sum() / pool, "percent"),
    "reserve fund balance": (w["Reserve fund closing balance"], "money"),
    "excess spread": (w["Excess spread released"], "money"),
}

drafts = re.split(r"\n\s*\n", open("evals/drafts/larkfield_commentary_2026_09.txt", encoding="utf-8").read().strip())
for d in drafts:
    title, body = d.split("\n", 1)
    print(title)
    for fig, hits in check_text(body, facts):
        print(f"  {fig.raw:<18} {'OK  ' + ', '.join(hits) if hits else 'NOT SUPPORTED'}")
    bad = forbidden_phrases(body)
    print("  Forbidden phrases:", bad if bad else "none", "\n")
