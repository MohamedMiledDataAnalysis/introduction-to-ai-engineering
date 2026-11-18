"""
A copy of the Larkfield September 2026 tape with twelve injected data errors, and the list of errors
(data/sf/rmbs/dq/). Used in Chapter 12 to measure a data-quality checker.
Run:  python scripts/make_dq_tape.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
out_dir = ROOT / "data/sf/rmbs/dq"
out_dir.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(2025)
tape = pd.read_csv(ROOT / "data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep = tape[tape["RREL6"] == "2026-09-30"].reset_index(drop=True)
perf = sep.index[(sep["RREL69"] == "PERF") & (sep["RREL35"] == "FRXX")].tolist()
picks = rng.choice(perf, 13, replace=False)
errors = []


def inject(i, field, value, rule):
    errors.append({"loan_id": sep.at[i, "RREL2"], "field": field, "old": sep.at[i, field] if field in sep else None,
                   "new": value, "rule": rule})
    sep.at[i, field] = value


inject(picks[0], "RREL30", -round(sep.at[picks[0], "RREL30"], 2), "negative_balance")
inject(picks[1], "RREL30", round(sep.at[picks[1], "RREL29"] * 1.35, 2), "balance_above_original")
inject(picks[2], "RREL24", "2015-06-30", "maturity_before_origination")
inject(picks[3], "RREL69", "DFLT", "default_without_180_days")
inject(picks[4], "RREL69", "ARRE", "arrears_without_balance")
inject(picks[5], "RREC12", 187.4, "ltv_implausible")
inject(picks[6], "RREL43", 59.0, "rate_out_of_range")
inject(picks[7], "RREL11", None, "missing_region")
inject(picks[8], "RREL68", 60, "performing_with_days_in_arrears")
inject(picks[9], "RREC16", 98.5, "original_ltv_above_95")
inject(picks[10], "RREL6", "2026-08-31", "wrong_cutoff_date")
inject(picks[12], "RREL29", round(sep.at[picks[12], "RREL29"] * 10, 2), "original_balance_typo")
dup = sep.loc[[picks[11]]].copy()
errors.append({"loan_id": sep.at[picks[11], "RREL2"], "field": "RREL2", "old": None, "new": "duplicate row",
               "rule": "duplicate_loan"})
sep = pd.concat([sep, dup], ignore_index=True)
sep.to_csv(out_dir / "larkfield_2026_09_received.csv", index=False)
json.dump(errors, open(out_dir / "injected_errors.json", "w"), indent=1, default=str)
print(f"{len(sep)} rows written; {len(errors)} errors injected")
