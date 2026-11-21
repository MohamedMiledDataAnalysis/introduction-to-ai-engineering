# 10. Structured Finance: A Prospectus Assistant with Citations

## Exercises

**Exercise 10.1.** For each of the eight baseline failures, say which level of Figure 10.2 failed (retrieval, or reading within a retrieved chunk), and whether a model can be expected to fix it.

**Exercise 10.2.** The baseline declines when the best BM25 score is below `min_score = 4.0`. Run it with thresholds 0, 2, 4, 6 and 8. Report the pass rate and explain the shape of the result.

**Exercise 10.3.** Run the model-based assistant with Ollama. Compare it with the baseline case by case: which cases did the model fix, and did it break any case the baseline passed?

**Exercise 10.4.** An investor asks: *“Will the Class A notes be repaid in full?”* Explain what the assistant should answer and why. Add the question to the evaluation set with an appropriate answer type.

**Exercise 10.5.** Write the one-page design note you would give the head of the cash management team before the assistant goes live: what it does, what it does not do, how answers are checked, who approves them, and the evaluation results.

## Corrections

### Exercise 10.1

**What the question asks.** For each of the baseline’s eight failures, decide whether the failure is in retrieval (the wrong chunk) or in reading (the right chunk, the wrong sentence), and whether a model can be expected to fix it.

**The plan.** (1) For each failure, print the chunk the baseline used and its score. (2) Compare the chunk with the case’s `source_section`. (3) If the chunk is right, look at the sentence chosen. (4) Classify.

**Step by step.**

``` python
fails = ["Q01", "Q02", "Q03", "Q04", "Q07", "Q08", "Q13", "Q16"]
for c in cases[cases.id.isin(fails)].to_dict("records"):
    best, score = index.search(c["question"], 1)[0]
    out = answer_extractive(c["question"], index)
    print(c["id"], c["source_section"], best["id"], round(score, 2), out["answer"][:60])
```

- `index.search(question, 1)[0]` gives the best chunk and its BM25 score, the baseline’s only source.
- `answer_extractive()` returns the sentence or table row of that chunk sharing most words with the question, or the refusal if the score is below 4.0.

**Reading the result.**

| Case | Chunk used (score) | Level                                                                                           | Can a model fix it?                                           |
|------|--------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| Q01  | `LMF#2` (5.02)     | reading: the reserve fund sentence was chosen                                                   | yes: relating *margin* to the interest rate column is reading |
| Q02  | `LMF#2` (3.93)     | refusal threshold: 3.93 is below 4.0                                                            | yes: the model receives the chunk whatever its score          |
| Q03  | `LMF#2` (7.26)     | reading: the table’s header row was chosen                                                      | yes: picking a table row is reading                           |
| Q04  | `LMF#2` (9.66)     | reading: header row again                                                                       | yes                                                           |
| Q07  | `LMF#3` (7.57)     | reading: the right chunk, but the answer is a conclusion it implies, not a sentence it contains | yes: drawing the conclusion is reading                        |
| Q08  | `LMF#4` (12.25)    | scorer: *six* written as a word                                                                 | the answer is correct; fix the scorer (Exercise 5.2)          |
| Q13  | `LMF#3` (10.29)    | retrieval at $k=1$: item (l) is in `LMF#6.2`                                                    | yes, with $k=3$, which brings `LMF#6.2` second                |
| Q16  | `LMF#8.2` (5.80)   | reading: the title line was chosen                                                              | yes                                                           |

**Checking the answer.** For Q13, run `index.search(question, 3)`: `LMF#3` (10.29), `LMF#6.2` (5.16), `LMF#6.1` (4.27). The right chunk is second, so the model with $k = 3$ receives it. For the reading cases, open `LMF#2` and find the expected values (1.10, 0.55, £16,220,447.45, 7.00) in the notes table: the information was in the chunk the baseline used.

**Mistakes to avoid.**

- Blaming retrieval for every failure. Six of eight failures had the right chunk.
- Counting Q08 as a failure of the assistant. The scorer is wrong; with the fix of Exercise 5.2 the baseline scores 13/20.

**Trade-offs.** One failure is retrieval at $k = 1$, one the refusal threshold, five reading within the right chunk, one the scorer. A model given three chunks addresses the first seven; the scorer needs its own fix. The classification tells you where to spend effort: here on reading, which is what a language model is for, not on retrieval.

### Exercise 10.2

**What the question asks.** Run the baseline with refusal thresholds 0, 2, 4, 6 and 8, report the pass rate for each, and explain the shape.

**The plan.** (1) Loop over the thresholds. (2) Score each run. (3) Look at the scores of the questions that change verdict. (4) Explain why the best threshold is where it is.

**Step by step.**

``` python
for t in (0, 2, 4, 6, 8):
    answers = {c["id"]: answer_extractive(c["question"], index, t)["answer"]
               for c in cases.to_dict("records")}
    res = run_eval(cases, answers)
    print(t, res.passed.sum(), res[~res.passed].id.tolist())
```

- The third argument of `answer_extractive()` is `min_score`: below it, the baseline declines.
- `run_eval()` scores the twenty answers; the failures are listed so you can see which cases move.

**Reading the result.**

| Threshold | Passed | What changes                                                                                                               |
|-----------|-------:|----------------------------------------------------------------------------------------------------------------------------|
| 0         |      9 | never declines: Q18, Q19, Q20 fail                                                                                         |
| 2         |     10 | declines Q19 (1.49); Q18 (2.97) and Q20 (3.81) still fail                                                                  |
| 4         |     12 | declines Q18 to Q20 correctly; also declines Q02 (3.93), which the baseline answered wrongly anyway                        |
| 6         |     10 | also declines Q12 (4.36) and Q14 (4.97), which it answered correctly; Q01 (5.02) is declined too, but it was already wrong |
| 8         |     10 | same failures as 6                                                                                                         |

The eight failures common to every threshold (Q01 to Q04, Q07, Q08, Q13, Q16) are the baseline’s reading errors of Exercise 10.1: no threshold fixes them.

**Checking the answer.** Print the top BM25 score of every question. The three unanswerable questions score 2.97 (Q18), 1.49 (Q19) and 3.81 (Q20); the lowest answerable scores are 3.93 (Q02), 4.36 (Q12) and 4.97 (Q14). A threshold between 3.81 and 3.93 declines exactly the three unanswerable questions. 4.0, the default, also declines Q02; Q02 fails at every threshold, so the pass count is the same, 12.

**Mistakes to avoid.**

- Choosing the threshold that maximises the pass rate and calling it tuned. On 20 cases, a gap of 0.12 between 3.81 and 3.93 is luck.
- Expecting monotonic behaviour. Raising the threshold first helps (it declines the unanswerable questions), then hurts (it declines answerable ones): the curve rises, then falls.

**Trade-offs.** Too low a threshold answers questions the document cannot answer; too high refuses questions it can. A threshold tuned on 20 cases is fragile: one new question can fall on the wrong side. Prefer the model’s own refusal, measured by the not-in-document cases, and keep the threshold as a safety net for the fallback mode without a model.

### Exercise 10.3

**What the question asks.** Run the model-based assistant with your model, compare it case by case with the baseline, and list what the model fixed and what it broke.

**The plan.** (1) Answer the twenty questions with both methods. (2) Score both. (3) Compare with `compare_runs()`. (4) Read every regression and apply the release criteria.

**Step by step.**

``` python
base = run_eval(cases, {c["id"]: answer_extractive(c["question"], index)["answer"]
                        for c in cases.to_dict("records")})
model = run_eval(cases, {c["id"]: answer_llm(c["question"], index)["answer"]
                         for c in cases.to_dict("records")})
print(compare_runs(base, model))
```

- `answer_llm()` retrieves three chunks, fills the citation prompt of Chapter 7, calls the model, and checks the citations.
- `compare_runs(a, b)` returns the regressions (passed by `a`, failed by `b`) and the fixes (failed by `a`, passed by `b`).

**Reading the result.** Expect fixes among Q01 to Q04, Q13 and Q16, the reading cases, and Q08 if the model writes *6*. Typical regressions with small models: a not-in-document case (Q18 to Q20) answered instead of declined, or a sentence case where the model rewords a clause and drops the keyword the scorer needs.

**Checking the answer.** For each regression, read the answer against the prospectus: an invented rating is a real error; *“principal is applied in order of seniority”* for Q14 (keyword *sequential*) is a correct answer that the scorer rejects. Then apply the release criteria of Section 10.4 one by one: at least 18 of 20 correct with Q10 and Q14 passing, every non-refusal answer grounded, all three not-in-document cases declined, at least 4 cases better than the baseline.

**Mistakes to avoid.**

- Deciding on the overall rate. A model that fixes six cases and invents a rating fails the criteria.
- Running the model and the baseline on different evaluation files: compare like with like.

**Trade-offs.** The model fixes reading failures and introduces new risks (invention, rewording). The release criteria were written before the run precisely so that the decision does not bend to the result. If the model misses the criteria on one case, the options are a better prompt, a larger model, or a narrower scope; each is measured again on the same set.

### Exercise 10.4

**What the question asks.** Decide what the assistant should answer to *“Will the Class A notes be repaid in full?”*, and add the question to the evaluation set with a suitable answer type.

**The plan.** (1) Search the prospectus for anything that answers it. (2) Identify what kind of question it is. (3) Write the expected answer. (4) Write the evaluation case.

**Step by step.**

*Step 1 — What the document says.* Nothing in the excerpt promises repayment. Section 7 repays the notes sequentially from principal receipts; Section 4 allocates losses through the principal deficiency ledger; Section 2 gives the Class A credit enhancement at closing, 12.00%; Section 10 describes risks.

*Step 2 — The kind of question.* *Will* and *in full* ask for a prediction about the future. The assistant describes the structure; it does not forecast.

*Step 3 — The expected answer.* *“The prospectus does not guarantee repayment. The notes are repaid from collections on the mortgage loans, with principal applied sequentially, Class A first \[LMF#7\]. At closing, the Class A notes had credit enhancement of 12.00%: the classes below them absorb losses on the pool first \[LMF#2\].”*

*Step 4 — The case.* Until a dedicated scorer exists, add it as a `text` case (Q21 to Q24 were used in Exercise 5.5):

``` text
Q25,Will the Class A notes be repaid in full?,text,does not guarantee,,does not guarantee|not guaranteed|no guarantee,7
```

**Reading the result.** The answer explains the mechanism with citations and contains no prediction. An answer saying *“Yes, the Class A notes will be repaid in full”* fails the case and is flagged by the forbidden-phrase checker if it uses *guaranteed* or *certain to*.

**Checking the answer.** Check each figure and claim against the prospectus: 12.00% is in Section 2’s table; sequential repayment in Section 7. Then score two answers: the expected one passes (it contains *does not guarantee*); *“They will be repaid in full.”* fails.

**Mistakes to avoid.**

- Making it a `not_in_document` case. The document does contain relevant information (the structure); the assistant should explain it, not only decline.
- Writing an expected answer that hints at likelihood (*“likely to be repaid”*). That is still a prediction.

**Trade-offs.** A `text` case with keywords catches the main error (a prediction) but passes an answer that says *“not guaranteed”* and nothing else. A dedicated `no_prediction` answer type, failing on affirmative predictions and requiring a citation, would be stricter; it costs a new scorer and its own tests. Start with the keyword case and write the scorer when such questions become frequent.

### Exercise 10.5

**What the question asks.** Write a one-page design note for the head of the cash management team before go-live: what the assistant does and does not do, how answers are checked, who approves them, and the evaluation results.

**The plan.** (1) Fix six headings a manager can read in two minutes. (2) Fill each with facts from the chapter. (3) Check every claim against the code and the evaluation.

**Step by step.** Six headings:

1.  **Purpose.** Draft answers to investors’ questions about Larkfield 2025-1 from the prospectus, for analyst approval.
2.  **Scope.** The prospectus excerpt only; no deal performance figures (those come from the reporting tools of Chapter 14); no predictions; no other deals.
3.  **How it works.** Retrieval of three passages; drafting by the model with a citation after every sentence; automatic checks (each citation provided, each figure present in the cited passages); review queue.
4.  **Controls.** Every answer approved by an analyst before sending; failed checks shown to the analyst; forbidden phrases flagged; all drafts, sources and approvals logged.
5.  **Evaluation.** Baseline 12/20 (95% interval 39% to 78%); the assistant’s results on retrieval, correctness and grounding (from Exercise 10.3); the release criteria and whether each is met; the date, the model and the prompt version.
6.  **Limits and next steps.** A 20-case set gives wide intervals; questions outside the excerpt are declined; questions from real investor emails are added to the set each month.

**Reading the result.** A page with no adjectives about quality: every claim is a fact the reader can check (a number, a rule, a name).

**Checking the answer.** For each sentence, name its evidence: the code (`answer_llm()`, `check_citations()`), the evaluation output, or the process (the review queue). A sentence without evidence is either removed or turned into a next step.

**Mistakes to avoid.**

- Writing *“accurate”* or *“reliable”* without a number.
- Leaving out what the assistant does not do. A manager needs the limits more than the features.

**Trade-offs.** One page leaves out detail; that is the point. The detail lives in the evaluation output and the code, referenced by name. The note is also the first draft of the model documentation of Chapter 20: write it so that it can be reused there.
