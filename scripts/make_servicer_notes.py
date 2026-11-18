"""
Servicer notes for Larkfield loans in arrears at 30 September 2026 (fictional).
Each note is free text written by a collections officer; the truth file gives
the facts each note contains, so that extraction can be evaluated (Chapters 4-5).
Run:  python scripts/make_servicer_notes.py
"""
import json
import random
from pathlib import Path

import pandas as pd

random.seed(2025)
ROOT = Path(__file__).resolve().parents[1]
tape = pd.read_csv(ROOT / "data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep = tape[(tape.RREL6 == "2026-09-30") & (tape.RREL69 == "ARRE")].copy()

ACTIONS = {
    "payment_plan": ["agreed a payment arrangement", "set up an arrangement to clear the arrears",
                     "accepted a repayment plan"],
    "no_contact": ["could not be reached despite three calls and a letter",
                   "has not responded to our letters", "did not answer our calls this month"],
    "litigation": ["has been referred to our solicitors", "is now with the litigation team",
                   "has been passed to solicitors for possession proceedings"],
}
REASONS = ["reduced working hours", "a period of illness", "the end of a fixed-term contract",
           "a relationship breakdown", "an increase in the monthly payment after the fixed rate ended"]
officers = ["J. Patel", "S. Okafor", "R. Lindqvist", "M. Haddad"]

notes = []
for i, r in enumerate(sep.itertuples()):
    months = int(r.RREL68 // 30)
    action = random.choice(["payment_plan"] * 3 + ["no_contact"] * 2 + (["litigation"] if months >= 3 else []))
    promise = None
    if action == "payment_plan":
        promise = f"2026-10-{random.choice([5, 10, 15, 20, 28]):02d}"
    reason = random.choice(REASONS)
    amount = f"£{r.RREL67:,.2f}"
    style = i % 3
    if style == 0:
        text = (f"Loan {r.RREL2}. Borrower is {months} month{'s' if months > 1 else ''} behind, "
                f"arrears of {amount}. Cause given: {reason}. Borrower {random.choice(ACTIONS[action])}"
                + (f"; first payment promised for {pd.Timestamp(promise):%d %B %Y}." if promise else ".")
                + f" — {random.choice(officers)}, 30/09/2026")
    elif style == 1:
        text = (f"30 Sep 2026 – account {r.RREL2}: {amount} outstanding in arrears "
                f"({months * 30} days). The customer {random.choice(ACTIONS[action])}"
                + (f", starting {pd.Timestamp(promise):%d/%m/%Y}" if promise else "")
                + f". Reason: {reason}. Next review in 30 days.")
    else:
        text = (f"Collections update for {r.RREL2} (Larkfield 2025-1). "
                f"The borrower {random.choice(ACTIONS[action])}. Missed payments: {months}. "
                f"Arrears balance {amount}."
                + (f" Promise to pay dated {pd.Timestamp(promise):%-d %b %Y}." if promise else "")
                + f" Circumstances: {reason}.")
    truth = {"loan_id": r.RREL2, "months_in_arrears": months, "arrears_balance": round(r.RREL67, 2),
             "action": action, "promise_date": promise}
    notes.append({"note_id": f"N{i + 1:03d}", "text": text, "truth": truth})

out = ROOT / "data/sf/rmbs/servicer_notes_2026_09.jsonl"
with open(out, "w", encoding="utf-8") as f:
    for n in notes:
        f.write(json.dumps(n, ensure_ascii=False) + "\n")
print(f"{len(notes)} notes written to {out.relative_to(ROOT)}")
print(notes[0]["text"])
print(notes[1]["text"])
print(notes[2]["text"])
