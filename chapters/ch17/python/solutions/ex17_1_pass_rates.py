# Exercise 17.1 - Pass rates of six summaries
# Run from the root of the repository:  python chapters/ch17/python/solutions/ex17_1_pass_rates.py

import json, sys
sys.path.insert(0, ".")
from collections import Counter
from aie.summary_check import check_summary, summarise_note

key_facts = json.load(open("data/am/research/key_facts.json"))
fails = Counter()
for i in range(1, 7):
    nid = f"R{i:02d}"
    note = open(f"data/am/research/{nid}.md", encoding="utf-8").read()
    text, version = summarise_note(nid)
    for p in check_summary(text, note, key_facts[nid]):
        kind = ("faithful" if "not in the note" in p else
                "consistent" if p.startswith("recommendation") else
                "complete" if p.startswith("missing") else "short")
        fails[kind] += 1
print(fails)
