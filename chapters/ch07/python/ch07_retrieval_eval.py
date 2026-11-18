# Chapter 7 - Chunk the prospectus, retrieve with BM25 and measure the hit rate on the evaluation set
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.retrieval import BM25, chunk_markdown

text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
            encoding="utf-8").read()
chunks = chunk_markdown(text, "LMF")
print(f"{len(chunks)} chunks:", ", ".join(c["id"] for c in chunks))

index = BM25(chunks)
cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str,
                    keep_default_na=False)
cases = cases[cases["source_section"] != ""]    # answerable questions only

for k in (1, 2, 3):
    hits, misses = 0, []
    for case in cases.to_dict("records"):
        found = [c["id"].split("#")[1].split(".")[0]
                 for c, _ in index.search(case["question"], k)]
        if case["source_section"] in found:
            hits += 1
        else:
            misses.append(case["id"])
    print(f"hit rate at k={k}: {hits}/{len(cases)} = "
          f"{hits / len(cases):.0%}   missed: {misses}")

q = cases.set_index("id").loc["Q16", "question"]
print("\nQ16:", q)
for c, s in index.search(q, 3):
    print(f"  {s:>6}  {c['id']:<8} {c['title']}")
