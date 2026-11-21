# 7. Retrieval: Giving the Model the Right Passages

## Exercises

**Exercise 7.1.** Index the three Harbourline Key Information Documents together, with document codes `HGEF`, `HECB` and `HBMA`. Retrieve for *“What are the ongoing costs of the euro corporate bond fund?”*. Which chunk comes first? What would go wrong if a chunk of another fund came first?

**Exercise 7.2.** Repair the *margin* misses (Q01, Q02) without embeddings, in two ways: (a) add to each chunk of section 2 a line of keywords, *“Keywords: margin, coupon, spread, interest rate”*; (b) rewrite the question before searching, replacing *margin* with *interest rate*. Measure the hit rate at $k=1$ for each. Which do you prefer, and why?

**Exercise 7.3.** Compute by hand the fused score of `LMF#2` in Figure 7.3 and check the order of the fused list.

**Exercise 7.4.** Write a prompt template `prompts/answer_with_citations_v1.txt` that receives the retrieved chunks and the question, and requires a citation after every sentence. Then run it with Ollama on Q05 and Q10 and pass the answers to `check_citations()`.

**Exercise 7.5.** Answer B of Step 3 contains a correct figure but no citation, and the checker reports two problems. Explain the second problem, and say whether it is a false fail.

## Corrections

### Exercise 7.1

**What the question asks.** Index the three funds’ KIDs together, search for the euro corporate bond fund’s ongoing costs, see which chunk comes first, and explain the risk when another fund’s chunk wins.

**The plan.** (1) Chunk each KID with its fund code as document identifier. (2) Build one BM25 index. (3) Search and print the top three. (4) Find where the right chunk ranks, and why.

**Step by step.**

``` python
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
```

- `chunk_markdown(text, "HECB")` cuts a document at its headings (and long sections into parts of at most 180 words); each chunk’s identifier is the code, `#`, and the start of its heading.
- `chunks += ...` adds the three funds’ chunks to one list, so one index covers all three.
- `index.search(question, 3)` returns the three best chunks with their BM25 scores.

``` r
source("aie_r/retrieval.R")
chunks <- list()
for (code in c("hgef", "hecb", "hbma")) {
  text <- paste(readLines(sprintf("data/am/documents/%s_kid.md", code),
                          encoding = "UTF-8"), collapse = "\n")
  chunks <- c(chunks, chunk_markdown(text, toupper(code)))
}
index <- bm25_index(chunks)
for (h in bm25_search(index, "What are the ongoing costs of the euro corporate bond fund?", 3))
  cat(h$score, h$chunk$id, "\n")
```

**Reading the result.**

**What you should see**

``` text
11.452 HECB#Product
7.089 HECB#What is this product?
3.785 HGEF#What are the costs?
```

The two chunks that name the fund (*Euro Corporate Bond*) come first, and neither contains costs. The third chunk is the cost section of the **global equity** fund.

**Checking the answer.** Search with $k = 30$ and find the cost sections: HGEF’s is third, HECB’s fourth and HBMA’s fifth, **all with the same score, 3.785**. The three cost sections have the same wording (*costs*, *ongoing*, *management fees*), and none contains *euro corporate bond*; the tie is broken by the order in which the funds were indexed. Index HECB first and its cost section would come third: the result depends on an accident of order.

**Mistakes to avoid.**

- Concluding that BM25 “chose” HGEF. It could not tell the three cost sections apart.
- Trusting the grounding check to catch the error. The model would answer with HGEF’s costs (0.75% management and operating costs) instead of HECB’s (0.40%), cite `HGEF#What are the costs?`, and the figure *is* in the cited passage: the check passes. A correct figure from the wrong fund is the most dangerous kind of error.

**Trade-offs.** Two fixes, used together in Chapters 15 and 22. **Metadata filtering**: when the question names a fund, keep only that fund’s chunks before ranking; reliable, but it requires recognising the fund in the question. **Context in every chunk**: add a header line (*Harbourline Euro Corporate Bond Fund — KID*) to each chunk, so that the fund name is in the cost section too; simple, but it lengthens every chunk. Filtering by metadata is the stronger of the two, because it does not rely on the ranking separating near-identical documents.

### Exercise 7.2

**What the question asks.** Fix the misses on Q01 and Q02 (*“What is the margin on the Class B/A notes?”*) without embeddings, in two ways, measure the hit rate at $k = 1$ for each, and choose.

**The plan.** (a) Add a keyword line to the chunk of section 2. (b) Rewrite *margin* in the question. For each, re-run the hit-rate loop of `ch07_retrieval_eval.py` at $k = 1$.

**Step by step.**

*Option (a) — enrich the chunk, at indexing.*

``` python
chunks = chunk_markdown(text, "LMF")
for c in chunks:
    if c["id"] == "LMF#2":
        c["text"] += "\nKeywords: margin, coupon, spread, interest rate"
index = BM25(chunks)
```

- The loop finds the chunk of section 2 (the notes table) and appends a keyword line **before** the index is built, so BM25 counts these words.

*Option (b) — rewrite the question, at search time.*

``` python
import re
SYNONYMS = {"margin": "interest rate margin"}
def rewrite(q):
    for word, repl in SYNONYMS.items():
        q = re.sub(rf"\b{word}\b", repl, q, flags=re.I)
    return q
```

Search with `index.search(rewrite(case["question"]), 1)` in the loop.

**Reading the result.**

|                             | Hit rate at $k=1$ | Missed        |
|-----------------------------|------------------:|---------------|
| Original                    |             14/17 | Q01, Q02, Q13 |
| \(a\) keywords in the chunk |         **16/17** | Q13           |
| \(b\) rewritten question    |             14/17 | Q01, Q02, Q13 |

Option (a) repairs both misses; option (b) repairs neither.

**Checking the answer.** See why (b) fails: the rewritten Q01, *“What is the interest rate margin on the Class B notes?”*, returns `LMF#10` (risk factors, 5.60), then `LMF#2` (5.28). *Interest* and *rate* appear in many sections, so BM25 gives them little weight, and the risk factors section mentions interest rates repeatedly. In (a), *margin* is rare in the index and now points to one chunk, which gives it a high weight.

**Mistakes to avoid.**

- Adding the keyword line after building the index: the index does not see it.
- Assuming a fix works because it is plausible. Option (b) looked reasonable and changed nothing; only the measurement showed it.

**Trade-offs.** Option (a) is applied once, at indexing, and is visible in the index, so a reviewer can read it; it must be redone when the document changes. Option (b) runs on every question and its list grows as users find new words. Both are vocabularies written by hand. Embeddings solve the same problem without lists, at the cost of a model call per chunk and per question. Teams combine them: a small, reviewed list of domain synonyms for the terms that matter most, and hybrid retrieval for the rest.

### Exercise 7.3

**What the question asks.** Compute by hand the reciprocal rank fusion score of `LMF#2` in Figure 7.3, then the scores of the other chunks, and check the fused order.

**The plan.** Apply the formula $\text{RRF}(d) = \sum_{\text{lists}} \frac{1}{60 + \text{rank}}$ to each chunk, summing over the lists in which it appears.

**Step by step.**

*Step 1 — Ranks of `LMF#2`.* Third in the BM25 list, first in the embedding list.

*Step 2 — Its score.* $\frac{1}{60+3} + \frac{1}{60+1} = 0.015873 + 0.016393 = 0.032266$.

*Step 3 — The other chunks.*

| Chunk     | BM25 rank | Embedding rank |                              Fused score |
|-----------|----------:|---------------:|-----------------------------------------:|
| `LMF#7`   |         1 |              2 | $\frac{1}{61} + \frac{1}{62} = 0.032522$ |
| `LMF#2`   |         3 |              1 | $\frac{1}{63} + \frac{1}{61} = 0.032266$ |
| `LMF#6.2` |         2 |              — |                $\frac{1}{62} = 0.016129$ |
| `LMF#8.1` |         — |              3 |                $\frac{1}{63} = 0.015873$ |

**Reading the result.** Fused order: `LMF#7`, `LMF#2`, `LMF#6.2`, `LMF#8.1`. With $k = 2$, both `LMF#7` and `LMF#2` are sent to the model, and the answer (in section 2) is reachable.

**Checking the answer.** Run `reciprocal_rank_fusion([["LMF#7", "LMF#6.2", "LMF#2"], ["LMF#2", "LMF#7", "LMF#8.1"]])` from `aie/retrieval.py`, the two lists of the figure: it returns `["LMF#7", "LMF#2", "LMF#6.2", "LMF#8.1"]`, the same order. Also check the property that matters: `LMF#2` and `LMF#7` are the only chunks found by both methods, and they are the only ones above 0.03.

**Mistakes to avoid.**

- Using the rank starting at 0: the formula uses rank 1 for the first item.
- Adding the BM25 and cosine **scores** instead of ranks. They are on different scales; fusing ranks avoids calibrating them.

**Trade-offs.** The constant 60 flattens the differences between ranks, so that being found by both methods counts more than being first in one. A smaller constant (10) rewards first places more; 60 is the value of the original paper and works well without tuning. Fusion also has a cost: two retrievals per question instead of one.

### Exercise 7.4

**What the question asks.** Write a versioned prompt that gives the model the retrieved chunks and requires a citation after every sentence, run it with your model on Q05 and Q10, and check the answers with `check_citations()`.

**The plan.** (1) Write the template with two placeholders. (2) Format the retrieved chunks with their identifiers. (3) Call the model. (4) Check citations and figures.

**Step by step.**

*Step 1 — `prompts/answer_with_citations_v1.txt`:*

``` text
You answer questions about a securitisation prospectus.
Use only the passages below. After every sentence, write the identifier
of the passage that supports it, in square brackets, for example [LMF#3].
Quote figures exactly as written in the passages.
If the passages do not contain the answer, write:
"The passages provided do not state this." and cite nothing.

PASSAGES:
{passages}

QUESTION: {question}
```

*Step 2 — Fill and call:*

``` python
template, version = load_prompt("answer_with_citations_v1")
retrieved = [c for c, _ in index.search(q, 3)]
passages = "\n\n".join(f"[{c['id']}]\n{c['text']}" for c in retrieved)
reply = chat([{"role": "user", "content":
               render(template, passages=passages, question=q)}])
print(reply["text"])
print(check_citations(reply["text"], retrieved))
```

- Each passage is preceded by its identifier in brackets, exactly as the model must cite it.
- `check_citations()` returns a list of problems: no citation, a citation to a passage not provided, or a figure absent from the cited passages. An empty list means grounded.

**Reading the result.** For Q05 a correct answer is *“The Reserve Fund Required Amount is £6,082,667.80, equal to 1.50% of the portfolio at the cut-off date \[LMF#3\].”*: the checker returns `[]`. For Q10, BM25 ranks section 5 first; a correct answer says recoveries are revenue receipts and cites `[LMF#5]`.

**Checking the answer.** Verify each citation by hand once: open the cited chunk and find the figure or the rule in it. Then make the checker fail on purpose: replace `[LMF#3]` by `[LMF#4]` in the answer; the checker reports that £6,082,667.80 is not in the cited passages.

**Mistakes to avoid.**

- Treating a refusal as a failure. A refusal cites nothing, so `check_citations()` reports *no citation*. Recognise the refusal sentence first and score it with the evaluation of Chapter 5.
- Formatting identifiers differently in the passages and in the instruction (`LMF#3` versus `[LMF 3]`): the model copies what it sees.

**Trade-offs.** A citation after every sentence makes answers heavier to read, but each sentence becomes checkable. For an internal tool, citations per paragraph may be enough; for answers to investors, keep them per sentence. Citations prove where a figure came from, not that the passage was the right one (Exercise 7.1): retrieval quality still needs its own measurement.

### Exercise 7.5

**What the question asks.** Explain the second problem reported for Answer B (correct figure, no citation) and decide whether it is a false fail.

**The plan.** Run the checker on the answer and follow its code for an answer with no citation.

**Step by step.** Answer B: *“The Reserve Fund Required Amount is £6,082,667.80.”* The checker:

``` python
cited = CITATION.findall(answer)          # [] : no [ID#n] in the answer
if not cited:
    problems.append("no citation")
cited_text = " ".join(by_id[c]["text"] for c in cited if c in by_id)   # ""
source_values = {... for f in extract_figures(cited_text)}             # empty set
for f in extract_figures(CITATION.sub("", answer)):
    if (f.unit, round(f.value * f.scale, 2)) not in source_values:
        problems.append(f"figure {f.raw} not found in the cited passages")
```

**Reading the result.**

``` text
['no citation', 'figure £6,082,667.80 not found in the cited passages']
```

With no citation, the cited text is empty, so no figure can be found in it: the second problem is a **consequence** of the first.

**Checking the answer.** Add `[LMF#3]` to the answer and run again: both problems disappear together, which confirms that they had one cause.

**Mistakes to avoid.**

- Counting this answer as two errors in a report. It has one root cause.
- Calling it a false fail because the figure is correct. The rule is that a client-facing answer must be traceable; correct and untraceable fails.

**Trade-offs.** It is not a false fail, but the second message is misleading: it suggests the figure may be wrong. A small improvement is to return early when nothing is cited:

``` python
if not cited:
    return ["no citation"]
```

The report becomes clearer; the cost is that, for uncited answers, you no longer learn whether the figures would have been found in the retrieved passages. For diagnosis, keep that information in the log rather than in the user-facing message.
