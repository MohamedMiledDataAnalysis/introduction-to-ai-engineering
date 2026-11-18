# Chapter 7 - Hybrid retrieval: BM25 + embeddings, fused by reciprocal rank (needs: ollama pull nomic-embed-text)
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.llm import embed
from aie.retrieval import BM25, chunk_markdown, cosine, reciprocal_rank_fusion

text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md", encoding="utf-8").read()
chunks = chunk_markdown(text, "LMF")
index = BM25(chunks)
# nomic-embed-text expects a task prefix: "search_document: " for what is searched, "search_query: " for questions
vectors = embed(["search_document: " + c["text"] for c in chunks])       # one call embeds every chunk

cases = pd.read_csv("evals/sf_prospectus_qa.csv", dtype=str, keep_default_na=False)
cases = cases[cases["source_section"] != ""]
q_vectors = embed(["search_query: " + q for q in cases["question"]])

for k in (1, 2, 3):
    hits = {"bm25": 0, "embeddings": 0, "hybrid": 0}
    for (_, case), qv in zip(cases.iterrows(), q_vectors):
        bm25_rank = [c["id"] for c, _ in index.search(case["question"], len(chunks))]
        emb_rank = [chunks[i]["id"] for i in sorted(range(len(chunks)), key=lambda i: -cosine(qv, vectors[i]))]
        for name, ranking in (("bm25", bm25_rank), ("embeddings", emb_rank),
                              ("hybrid", reciprocal_rank_fusion([bm25_rank, emb_rank]))):
            sections = [cid.split("#")[1].split(".")[0] for cid in ranking[:k]]
            hits[name] += case["source_section"] in sections
    print(f"k={k}: " + "  ".join(f"{n} {h}/{len(cases)}" for n, h in hits.items()))
