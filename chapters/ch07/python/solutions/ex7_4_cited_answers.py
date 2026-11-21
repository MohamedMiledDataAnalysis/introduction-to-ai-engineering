# Exercise 7.4 - Answers that cite their passages
# Run from the root of the repository:  python chapters/ch07/python/solutions/ex7_4_cited_answers.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.llm import chat
from aie.prompts import load_prompt, render
from aie.retrieval import BM25, check_citations, chunk_markdown

text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
            encoding="utf-8").read()
index = BM25(chunk_markdown(text, "LMF"))
cases = pd.read_csv("evals/sf_prospectus_qa.csv").set_index("id")
for case_id in ("Q05", "Q10"):
    q = cases.loc[case_id, "question"]
    print(case_id, q)
    template, version = load_prompt("answer_with_citations_v1")
    retrieved = [c for c, _ in index.search(q, 3)]
    passages = "\n\n".join(f"[{c['id']}]\n{c['text']}" for c in retrieved)
    reply = chat([{"role": "user", "content":
                   render(template, passages=passages, question=q)}])
    print(reply["text"])
    print(check_citations(reply["text"], retrieved))
