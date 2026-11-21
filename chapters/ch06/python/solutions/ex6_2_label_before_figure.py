# Exercise 6.2 - A figure must be named before it
# Run from the root of the repository:  python chapters/ch06/python/solutions/ex6_2_label_before_figure.py

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

arrears_pct = 100 * sep.loc[sep["RREL69"] == "ARRE", "RREL30"].sum() / pool
facts = {
    "revenue receipts": (w["Available revenue receipts"], "money", ["revenue"]),
    "principal receipts": (w["Available principal receipts"], "money", ["principal"]),
    "Class A principal paid": (n.loc["A", "principal_paid"], "money",
                               ["class a", "repaid", "reducing"]),
    "Class A closing balance": (n.loc["A", "closing"], "money", ["class a", "outstanding"]),
    "pool balance": (pool, "money", ["pool", "portfolio"]),
    "arrears ratio": (arrears_pct, "percent", ["arrears"]),
    "reserve fund balance": (w["Reserve fund closing balance"], "money", ["reserve"]),
    "excess spread": (w["Excess spread released"], "money", ["excess", "spread", "residual"]),
}

from aie.factcheck import extract_figures, matches

def check_text_labelled(text, facts, window=60):
    report = []
    for fig in extract_figures(text):
        context = text[max(0, fig.start - window):fig.start].lower()
        hits = [name for name, (v, u, keys) in facts.items()
                if matches(fig, v, u) and any(k in context for k in keys)]
        report.append((fig, hits))
    return report

print("Revenue receipts were £4.88 million:",
      [hits for _, hits in check_text_labelled("Revenue receipts were £4.88 million", facts)], "\n")

drafts = re.split(r"\n\s*\n", open(
    "evals/drafts/larkfield_commentary_2026_09.txt",
    encoding="utf-8").read().strip())
for d in drafts:
    title, body = d.split("\n", 1)
    print(title)
    for fig, hits in check_text_labelled(body, facts):
        print(f"  {fig.raw:<18} "
              f"{'OK  ' + ', '.join(hits) if hits else 'NOT SUPPORTED'}")
    bad = forbidden_phrases(body)
    print("  Forbidden phrases:", bad if bad else "none", "\n")
