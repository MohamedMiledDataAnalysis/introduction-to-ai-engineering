# Exercise 21.4 - The commentary tool, in its minimum form (the full solution: ex21_4_commentary_tool.py)
# Run from the root of the repository:  python chapters/ch21/python/solutions/ex21_4_minimum.py

import sys; sys.path.insert(0, ".")
from aie.tools import REGISTRY, run_tool

import pandas as pd
from aie.investor_report import (TAPE, month_figures, reconcile,
                                 template_commentary, check_commentary)

DATES = sorted(pd.read_csv(TAPE)["RREL6"].unique())[1:]

def draft_investor_commentary(cutoff_date):
    if cutoff_date not in DATES:
        raise ValueError(f"no investor report for {cutoff_date}; "
                         f"reports run from {DATES[0]} to {DATES[-1]}")
    f = month_figures(cutoff_date)
    checks = reconcile(f)
    if not all(checks.values()):
        raise ValueError("reconciliation failed: " +
                         "; ".join(k for k, ok in checks.items() if not ok))
    text = template_commentary(f)          # or draft_commentary(f) of Exercise 14.2
    return {"cutoff_date": cutoff_date, "commentary": text,
            "unsupported_figures": [raw for raw, hits in check_commentary(text, f) if not hits],
            "approval_required": True}

REGISTRY["draft_investor_commentary"] = (
    draft_investor_commentary,
    "Draft the commentary of the Larkfield 2025-1 investor report for one "
    "collection period, after the reconciliations pass. The draft must be "
    "approved by an analyst before publication.",
    {"type": "object",
     "properties": {"cutoff_date": {"type": "string",
                                    "pattern": "20[0-9]{2}-[0-9]{2}-[0-9]{2}"}},
     "required": ["cutoff_date"], "additionalProperties": False})

for d in ("2026-09-30", "2026-10-31"):
    print(run_tool({"name": "draft_investor_commentary", "arguments": {"cutoff_date": d}})[:300])
