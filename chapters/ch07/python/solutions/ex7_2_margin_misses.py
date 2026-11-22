# Exercise 7.2 - Two ways to fix the margin questions
# Run from the root of the repository:  python chapters/ch07/python/solutions/ex7_2_margin_misses.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.retrieval import BM25, chunk_markdown

text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
            encoding="utf-8").read()
cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str,
                    keep_default_na=False)
cases = cases[cases["source_section"] != ""]    # answerable questions only

import re
SYNONYMS = {"margin": "interest rate margin"}
def rewrite(q):
    for word, repl in SYNONYMS.items():
        q = re.sub(rf"\b{word}\b", repl, q, flags=re.I)
    return q


def hit_rate(index, question_of, k=1):
    hits, misses = 0, []
    for case in cases.to_dict("records"):
        found = [c["id"].split("#")[1].split(".")[0]
                 for c, _ in index.search(question_of(case), k)]
        if case["source_section"] in found:
            hits += 1
        else:
            misses.append(case["id"])
    return f"{hits}/{len(cases)}   missed: {misses}"


print("Original:      ", hit_rate(BM25(chunk_markdown(text, "LMF")), lambda c: c["question"]))
chunks = chunk_markdown(text, "LMF")
for c in chunks:
    if c["id"] == "LMF#2":
        c["text"] += "\nKeywords: margin, coupon, spread, interest rate"
index = BM25(chunks)
print("(a) keywords:  ", hit_rate(index, lambda c: c["question"]))
original = BM25(chunk_markdown(text, "LMF"))
print("(b) rewritten: ", hit_rate(original, lambda c: rewrite(c["question"])))
