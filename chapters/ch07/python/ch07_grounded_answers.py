# Chapter 7 - Check that answers cite the passages they were given, and that their figures are in them
import sys

sys.path.insert(0, ".")
from aie.retrieval import BM25, check_citations, chunk_markdown

text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md", encoding="utf-8").read()
index = BM25(chunk_markdown(text, "LMF"))
retrieved = [c for c, _ in index.search("What is the Reserve Fund Required Amount?", 3)]
print("Retrieved:", [c["id"] for c in retrieved])

answers = {
    "A grounded": "The Reserve Fund Required Amount is £6,082,667.80, equal to 1.50% of the pool [LMF#3].",
    "B no citation": "The Reserve Fund Required Amount is £6,082,667.80.",
    "C wrong figure": "The Reserve Fund Required Amount is £6,028,667.80 [LMF#3].",
    "D cites unseen": "The reserve fund is replenished at item (l) [LMF#6.3].",
}
for name, ans in answers.items():
    problems = check_citations(ans, retrieved)
    print(f"{name:<16} {'grounded' if not problems else '; '.join(problems)}")
