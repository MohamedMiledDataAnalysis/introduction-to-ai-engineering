# Exercise 7.5 - One cause, two messages
# Run from the root of the repository:  python chapters/ch07/python/solutions/ex7_5_no_citation.py

import sys

sys.path.insert(0, ".")
from aie.retrieval import BM25, CITATION, check_citations, chunk_markdown

text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
            encoding="utf-8").read()
index = BM25(chunk_markdown(text, "LMF"))
retrieved = [c for c, _ in index.search("What is the Reserve Fund Required Amount?", 3)]
b = "The Reserve Fund Required Amount is £6,082,667.80."
print(check_citations(b, retrieved))
print(check_citations(b + " [LMF#3]", retrieved))      # with the citation: both problems go


def check_citations_early(answer, retrieved):
    """The same check, returning at once when nothing is cited."""
    cited = CITATION.findall(answer)
    if not cited:
        return ["no citation"]
    return check_citations(answer, retrieved)


print(check_citations_early(b, retrieved))
