# Chapter 13 - Build the facts of the HGEF commentary and check two drafts: value, label and direction
import re
import sys

sys.path.insert(0, ".")
from aie.commentary import check_commentary, hgef_facts

facts, attr = hgef_facts()
top = attr.sort_values("total")
print("Largest detractors (bp):", [(r.sector, round(10000 * r.total, 1))
                                   for r in top.head(3).itertuples()])
print("Largest contributors (bp):", [(r.sector, round(10000 * r.total, 1))
                                     for r in top.tail(2).itertuples()][::-1])

drafts = re.split(r"\n\s*\n", open("evals/drafts/hgef_commentary_2026_09.txt",
                                   encoding="utf-8").read().strip())
for d in drafts:
    title, body = d.split("\n", 1)
    print("\n" + title)
    for raw, hits, problem in check_commentary(body, facts):
        print(f"  {raw:<7} "
              f"{'PROBLEM: ' + problem if problem else 'OK  ' + ', '.join(hits)}")
