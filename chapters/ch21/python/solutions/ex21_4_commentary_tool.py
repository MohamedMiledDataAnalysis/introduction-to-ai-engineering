# Exercise 21.4 - The investor report workflow of Chapter 14 as a tool of the SF agent
# Run from the root of the repository, with the mock model on the script of this exercise:
#   MOCK_SCRIPT=tools/scripts/ex21_4_commentary.json python tools/mock_ollama.py &
#   python chapters/ch21/python/solutions/ex21_4_commentary_tool.py
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, ".")
import pandas as pd

import aie.investor_report as ir
from aie.assistants import Assistant
from aie.investor_report import TAPE, check_commentary, facts, month_figures, reconcile, template_commentary
from aie.tools import REGISTRY, run_tool

DATES = sorted(pd.read_csv(TAPE)["RREL6"].unique())[1:]          # collection period ends: no report at closing
SUFFIX = {"money": "_gbp", "percent": "_pct", "number": ""}


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
            "approval_required": True,
            # Going further than the book: the figures the commentary may quote, named with the unit suffixes
            # the agent's verifier reads (_gbp, _pct), so that an answer quoting the draft can be verified.
            "figures": {name.replace(" ", "_") + SUFFIX[unit]: round(float(v), 4)
                        for name, (v, unit) in facts(f).items()}}


REGISTRY["draft_investor_commentary"] = (
    draft_investor_commentary,
    "Draft the commentary of the Larkfield 2025-1 investor report for one "
    "collection period, after the reconciliations pass. The draft must be "
    "approved by an analyst before publication.",
    {"type": "object",
     "properties": {"cutoff_date": {"type": "string",
                                    "pattern": "20[0-9]{2}-[0-9]{2}-[0-9]{2}"}},
     "required": ["cutoff_date"], "additionalProperties": False})


def ask_sf(assistant, question):
    """The SF assistant's answer, with the status forced to needs_review when the commentary tool ran."""
    r = assistant.ask(question)
    if any(step[0] == "draft_investor_commentary" for step in r["trace"]):
        r["status"] = "needs_review"
        r["unsupported"] = r["unsupported"] + ["investor commentary: approval required"]
    return r


# 1. The tool on its own, through run_tool() as the agent calls it
for date in ("2026-09-30", "2026-10-31", "2025-06-30"):
    out = json.loads(run_tool({"name": "draft_investor_commentary", "arguments": {"cutoff_date": date}}))
    print(date, "->", out.get("error") or out["commentary"][:70] + "...",
          "" if "error" in out else f"| unsupported: {out['unsupported_figures']}")

# 2. The reconciliation gate: break one note balance in a copy of the notes file
tmp = tempfile.mkdtemp()
broken = os.path.join(tmp, "notes.csv")
notes = pd.read_csv(ir.NOTES)
row = (notes["cutoff"] == "2026-09-30") & (notes["cls"] == "A")
notes.loc[row, "closing"] += 100.0
notes.to_csv(broken, index=False)
shipped, ir.NOTES = ir.NOTES, broken
out = json.loads(run_tool({"name": "draft_investor_commentary", "arguments": {"cutoff_date": "2026-09-30"}}))
print("broken notes ->", out)
ir.NOTES = shipped
shutil.rmtree(tmp)

# 3. The agent with the new tool, on the scripted model
sf = Assistant("sf")
sf.agent.tool_names = sf.agent.tool_names + ["draft_investor_commentary"]
r = ask_sf(sf, "Draft the commentary for the September 2026 investor report.")
print("agent tools used:", [step[0] for step in r["trace"]])
print("status:", r["status"], "| flags:", r["unsupported"])

# 4. Why the tool returns its figures: without them, the verifier cannot support the quoted commentary
from aie.agent import Agent
text = template_commentary(month_figures("2026-09-30"))
bare = json.dumps({"cutoff_date": "2026-09-30", "commentary": text, "approval_required": True})
print("without 'figures', unsupported:", Agent("", [])._verify(text, [("draft_investor_commentary", bare)]))
