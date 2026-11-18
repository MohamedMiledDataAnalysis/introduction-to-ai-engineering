# Chapter 1 - Applied example: meet the two datasets and reconcile them
# Run from the root of the repository:  python chapters/ch01/python/ch01_meet_the_data.py
import pandas as pd

# ---- Structured finance: Larkfield Mortgage Funding 2025-1 ----
tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
notes = pd.read_csv("data/sf/rmbs/larkfield_2025_1_notes.csv")

cut = "2026-09-30"
pool = tape.loc[tape["RREL6"] == cut, "RREL30"].sum()
n = notes[notes["cutoff"] == cut]
notes_out = n["closing"].sum()
pdl = n["pdl_balance"].sum()

print("Larkfield 2025-1 at", cut)
print(f"  Pool balance (RREL30):   GBP {pool:,.2f}")
print(f"  Notes outstanding:       GBP {notes_out:,.2f}")
print(f"  PDL balance:             GBP {pdl:,.2f}")
print(f"  Notes - PDL - pool:      GBP {notes_out - pdl - pool:,.2f}")

# ---- Asset management: Harbourline Global Equity Fund ----
nav = pd.read_csv("data/am/fund_nav_monthly.csv")
bm = pd.read_csv("data/am/benchmark_returns_monthly.csv")

fund_1m = nav.loc[(nav["fund_code"] == "HGEF")
                  & (nav["month_end"] == cut), "net_return"].iloc[0]
bm_1m = bm.loc[bm["month_end"] == cut, "HGEF"].iloc[0]

print("\nHarbourline Global Equity Fund, September 2026")
print(f"  Fund return (net):       {fund_1m:.2%}")
print(f"  Benchmark return:        {bm_1m:.2%}")
print(f"  Relative return:         {fund_1m - bm_1m:+.2%}")
