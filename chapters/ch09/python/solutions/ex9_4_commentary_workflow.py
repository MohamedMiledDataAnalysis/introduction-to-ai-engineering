# Exercise 9.4 - The commentary as a workflow
# Run from the root of the repository:  python chapters/ch09/python/solutions/ex9_4_commentary_workflow.py

import sys; sys.path.insert(0, ".")
from aie.llm import chat

import json
from aie.tools import note_balance, pool_summary, waterfall_summary
from aie.agent import facts_from_results
from aie.factcheck import check_text

d = "2026-09-30"
results = [("waterfall_summary", json.dumps(waterfall_summary(d))),
           ("pool_summary", json.dumps(pool_summary(d))),
           ("note_balance", json.dumps(note_balance("A", d)))]

prompt = ("Write a four-sentence investor commentary for Larkfield "
          "Mortgage Funding 2025-1 for the period ending 30 September 2026, "
          "using only these figures, quoted as given:\n"
          + "\n".join(r for _, r in results))
draft = chat([{"role": "user", "content": prompt}])["text"]

facts = facts_from_results(results)
for fig, hits in check_text(draft, facts):
    print(fig.raw, "OK" if hits else "NOT SUPPORTED")
