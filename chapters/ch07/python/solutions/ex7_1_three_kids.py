# Exercise 7.1 - One index for three KIDs
# Run from the root of the repository:  python chapters/ch07/python/solutions/ex7_1_three_kids.py

import sys; sys.path.insert(0, ".")
from aie.retrieval import BM25, chunk_markdown

chunks = []
for code in ("hgef", "hecb", "hbma"):
    text = open(f"data/am/documents/{code}_kid.md", encoding="utf-8").read()
    chunks += chunk_markdown(text, code.upper())
index = BM25(chunks)
for c, s in index.search(
        "What are the ongoing costs of the euro corporate bond fund?", 3):
    print(s, c["id"])
