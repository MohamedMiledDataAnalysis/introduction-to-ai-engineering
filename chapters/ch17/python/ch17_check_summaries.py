# Chapter 17 - Check summaries of research notes: faithful, consistent, complete, short
import json
import sys

sys.path.insert(0, ".")
from aie.summary_check import check_summary

key_facts = json.load(open("data/am/research/key_facts.json"))
summaries = json.load(open("evals/candidates/research_summaries.json"))
for nid, versions in summaries.items():
    note = open(f"data/am/research/{nid}.md", encoding="utf-8").read()
    for label, text in versions.items():
        problems = check_summary(text, note, key_facts[nid])
        print(f"{nid} summary {label}: "
              f"{'accepted' if not problems else 'REJECTED'}")
        for p in problems:
            print("    -", p)
