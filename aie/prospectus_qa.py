"""The Larkfield prospectus assistant: retrieve, answer with citations, check grounding."""
import re

from aie.llm import chat
from aie.prompts import load_prompt, render
from aie.retrieval import BM25, check_citations, chunk_markdown, tokens

REFUSAL = "The passages provided do not state this."
KEYWORDS = {"LMF#2": "Keywords: margin, coupon, spread, interest rate"}


def build_index(path="data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md"):
    chunks = chunk_markdown(open(path, encoding="utf-8").read(), "LMF")
    for c in chunks:
        if c["id"] in KEYWORDS:
            c["text"] += "\n" + KEYWORDS[c["id"]]
    return BM25(chunks)


def answer_llm(question, index, k=3):
    retrieved = [c for c, _ in index.search(question, k)]
    template, version = load_prompt("answer_with_citations_v1")
    passages = "\n\n".join(f"[{c['id']}]\n{c['text']}" for c in retrieved)
    text = chat([{"role": "user", "content": render(
        template, passages=passages, question=question)}])["text"].strip()
    problems = [] if text.startswith(REFUSAL) \
        else check_citations(text, retrieved)
    return {"answer": text, "retrieved": [c["id"] for c in retrieved],
            "problems": problems, "prompt": version}


def answer_extractive(question, index, min_score=4.0):
    """Baseline without a model: the sentence or table row of the best chunk that shares most words."""
    best, score = index.search(question, 1)[0]
    if score < min_score:
        return {"answer": REFUSAL, "retrieved": [best["id"]], "problems": [], "prompt": "extractive"}
    q = set(tokens(question))
    pieces = [p.strip() for p in re.split(r"(?<=[.;])\s+|\n", best["text"]) if p.strip()]
    sentence = max(pieces, key=lambda p: len(q & set(tokens(p))))
    return {"answer": f"{sentence} [{best['id']}]", "retrieved": [best["id"]], "problems": [], "prompt": "extractive"}
