# 2. How Language Models Work

## Exercises

**Exercise 2.1.** Using the tiny next-word model, compute by hand the probability of *“b”* after *“class”* at $T = 0.5$. Check it against the output.

**Exercise 2.2.** Change the context word from *“class”* to *“reserve”*. Which word is most likely to follow it, and with what probability? Explain why in terms of the prospectus.

**Exercise 2.3.** In the similarity program, replace the question with *“What happens when a borrower misses six payments?”*. Which section comes first? Is it the right one? Explain the result.

**Exercise 2.4.** In the token program, count the tokens for the Harbourline HGEF factsheet (`data/am/documents/hgef_factsheet_2026_09.md`) and for all three Key Information Documents together. Would the three KIDs fit in a window of 8,000 tokens with room for an answer of 500 tokens?

**Exercise 2.5.** With Ollama running, send the HGEF factsheet to your model with the question *“What is the fund’s one-year return?”*, by adapting the request of `chapters/ch00/python/check_setup.py` (Chapter 0). Read `prompt_eval_count` in Ollama’s reply: the real number of input tokens. How far is it from the estimate of Exercise 2.4?

## Corrections

### Exercise 2.1

**What the question asks.** Compute, with pencil and paper, the probability that the tiny next-word model picks *“b”* after *“class”* at temperature $T = 0.5$, and confirm it with the program’s output. The aim is to see exactly what temperature does to probabilities.

**The plan.** (1) Write the counts of the words that follow *“class”*. (2) Raise each count to the power $1/T$. (3) Divide by the new total. (4) Compare with the program.

**Step by step.**

*Step 1 — The counts.* The program prints the four most frequent followers; the full list, from `follow["class"]`, is: *a* 10, *b* 7, *c* 5, *d* 5, and five other words (*initial*, *is*, *accrues*, *of*, *first*) once each. Total: $10 + 7 + 5 + 5 + 5 = 32$.

*Step 2 — Apply the power $1/T$.* The function `with_temperature()` in the program does three things:

`chapters/ch02/python/ch02_next_word.py` (extract)

``` python
logits = {w: math.log(p) / t for w, p in probs.items()}   # log-probability divided by T
expd = {w: math.exp(v - m) for w, v in logits.items()}   # back to the original scale
return {w: v / s for w, v in expd.items()}                # rescale so the total is 1
```

Dividing a logarithm by $T$ and taking the exponential raises the probability to the power $1/T$: $\exp(\log p / T) = p^{1/T}$. The `- m` subtracts the largest value before `exp` to avoid overflow; it cancels in the rescaling. With $T = 0.5$, $1/T = 2$, so we square. We can square the **counts** instead of the probabilities, because the common factor $1/32$ disappears when we rescale: $10^2 = 100$, $7^2 = 49$, $5^2 = 25$, $5^2 = 25$, and $1^2 = 1$ five times.

*Step 3 — Rescale.* The new total is $100 + 49 + 25 + 25 + 5 = 204$. The probability of *“b”* is $49 / 204 = 0.2402$.

**Reading the result.** The program’s table shows, in the row *b*, column *T=0.5*: **0.240**. The hand computation and the program agree.

**Checking the answer.** Check the whole column, not one cell: $100/204 = 0.490$ for *a*, $25/204 = 0.123$ for *c* and *d*, matching the program’s 0.490, 0.123, 0.123. And the five rare words share $5/204 = 0.025$: the four printed probabilities plus 0.025 add up to 1.001, which is 1 after rounding.

**Mistakes to avoid.**

- Multiplying the probabilities by $1/T$ instead of raising them to the power $1/T$: $0.219 \times 2 = 0.438$ is not a probability once rescaled with the others in the same wrong way.
- Forgetting the five rare words in the total: $49/199 = 0.246$, the wrong answer.

**Trade-offs.** Temperature below 1 helps the frequent choices and hurts the rare ones: *“b”* rose from 0.219 to 0.240 while each word seen once fell from $1/32 = 0.031$ to $1/204 = 0.005$. Low temperature gives stable, predictable text; high temperature gives variety and more mistakes. At $T = 0$, only *“a”* would ever be chosen. This book uses $T = 0$ for extraction and checking, where stability matters, and leaves higher values for drafting.

### Exercise 2.2

**What the question asks.** Change the context word to *“reserve”*, read the most likely next word and its probability, and explain it from the prospectus.

**The plan.** Change one line, run, then search the prospectus for the phrase.

**Step by step.** In Python change `context = "class"` to:

`chapters/ch02/python/solutions/ex2_2_reserve.py` (extract)

``` python
context = "reserve"
```

In R, `context <- "reserve"`. The rest of the program is unchanged: `follow[context]` now returns the counter of words that follow *“reserve”*.

**Reading the result.**

**What you should see**

``` text
Words that follow 'reserve' (8 occurrences):
  fund         8   p = 1.000
```

One line only: every occurrence of *reserve* in the excerpt is followed by *fund*. The probability is 1, and temperature changes nothing: $1^{1/T} = 1$.

**Checking the answer.** Search the excerpt (`Ctrl+F` for *reserve*): every occurrence is in *reserve fund* or *Reserve Fund Required Amount*, which lower-cases to *reserve fund required amount*, still followed by *fund*. Eight occurrences, eight times *fund*.

**Mistakes to avoid.**

- Typing `"Reserve"` with a capital. The program lower-cases the text, so `follow["Reserve"]` is empty: the program prints *0 occurrences* and then stops with a `ValueError` from `max()` on an empty list of probabilities.

**Trade-offs.** A model trained on all of English gives *fund* a high probability after *reserve*, but not 1: it has also seen *reserve bank*, *reserve price*, *reserve a table*. A small corpus produces a confident but narrow model. The same happens, at a larger scale, when a model has seen few documents of a niche field: strong habits, little nuance. This is why later chapters give the model the documents it needs instead of trusting what it learnt.

### Exercise 2.3

**What the question asks.** Ask the similarity program which prospectus section is closest to *“What happens when a borrower misses six payments?”*, judge whether the top section is right, and explain the score.

**The plan.** Replace the question, run, check the top section’s text, then look at which words the question and the section share.

**Step by step.**

`chapters/ch02/python/solutions/ex2_3_six_payments.py` (extract)

``` python
question = "What happens when a borrower misses six payments?"
```

The program then works in four steps:

1.  It splits the prospectus into sections (`re.split(r"\n## ", text)`).
2.  It turns each section and the question into word counts without common words (`tokens()` removes the `STOP` list).
3.  It weights each word by its rarity across sections (`idf`).
4.  It compares the question with each section by cosine similarity (`cosine()`): 1 means the same direction, 0 nothing in common.

**Reading the result.**

**What you should see**

``` text
  0.112  4. Principal deficiency ledger
  0.073  9. Selected eligibility criteria
  0.037  10. Selected risk factors
```

Section 4 comes first, and it is the right one: it defines a Defaulted Loan as one with *six or more monthly payments due and unpaid*, and says what happens next (the loss is recorded in the principal deficiency ledger). But the score is low: 0.112, against 0.642 for the reserve fund question of the applied example.

**Checking the answer.** Print the question’s words after the stop list: `what, happens, when, borrower, misses, six, payments`. Section 4 says *six or more monthly payments are due and unpaid*. Only *six* and *payments* appear in both: two words out of seven. That explains the low score; the section came first because no other section contains both.

**Mistakes to avoid.**

- Trusting a ranking without looking at the score. 0.112 is first place, but a weak first place: with one more section mentioning *payments*, the order could change.
- Concluding that the method found the meaning. It found two shared words.

**Trade-offs.** TF-IDF only matches identical words; it does not know that *misses* and *unpaid* express the same idea. An embedding model does, and gives a clearer score, but it can miss exact labels such as *Class B* or *item (l)* that word counts catch. Chapter 7 combines both methods for this reason.

### Exercise 2.4

**What the question asks.** Estimate the tokens of the HGEF factsheet and of the three KIDs, then decide whether the three KIDs and a 500-token answer fit in an 8,000-token window.

**The plan.** (1) Read the four files. (2) Estimate tokens with the rule of the chapter: one token per four characters. (3) Add the answer’s 500 tokens and compare with 8,000.

**Step by step.** Add to the token program:

`chapters/ch02/python/solutions/ex2_4_fund_documents.py` (extract)

``` python
docs = {name: open(f"data/am/documents/{name}", encoding="utf-8").read()
        for name in ["hgef_factsheet_2026_09.md", "hgef_kid.md",
                     "hecb_kid.md", "hbma_kid.md"]}
for name, s in docs.items():
    print(f"{name:<28} {len(s):>6,} characters  ~{len(s) / 4:>6,.0f} tokens")
kids = sum(len(s) for n, s in docs.items() if n.endswith("kid.md")) / 4
print(f"Three KIDs together: ~{kids:,.0f} tokens")
```

- The dictionary comprehension reads each file into a string, keyed by its name.
- `len(s)` counts characters; dividing by 4 applies the budgeting rule.
- `n.endswith("kid.md")` selects the three KIDs for the total.

**Reading the result.**

**What you should see**

``` text
hgef_factsheet_2026_09.md     2,031 characters  ~   508 tokens
hgef_kid.md                   4,153 characters  ~ 1,038 tokens
hecb_kid.md                   4,188 characters  ~ 1,047 tokens
hbma_kid.md                   4,001 characters  ~ 1,000 tokens
Three KIDs together: ~3,086 tokens
```

$3{,}086 + 500 = 3{,}586$ tokens, less than half of 8,000. The three KIDs fit, with room for instructions.

**Checking the answer.** Exercise 2.5 measures the real count with the model; until then, check the arithmetic: $(4{,}153 + 4{,}188 + 4{,}001) / 4 = 3{,}085.5$, printed as 3,086.

**Mistakes to avoid.**

- Forgetting the instructions and the answer in the budget. The window holds everything: system prompt, documents, question **and** reply.
- Treating the four-characters rule as exact. It is a budgeting rule for English prose; tables and numbers use more tokens per character.

**Trade-offs.** Fitting is not the same as working well. In Chapter 15 we send one KID at a time although three fit: the model then cannot mix up the costs of two funds, the most frequent error in multi-document extraction. The price is three calls instead of one.

### Exercise 2.5

**What the question asks.** Send the HGEF factsheet and a question to your model, read the real input token count, and compare it with the estimate of Exercise 2.4.

**The plan.** Adapt the request of Chapter 0’s check script, run it, read `prompt_eval_count`, and check the answer’s figure against the factsheet.

**Step by step.** In a copy of `chapters/ch00/python/check_setup.py`, keep the `payload` and replace the message’s content by the factsheet followed by the question:

`chapters/ch02/python/solutions/ex2_5_factsheet_question.py` (extract)

``` python
factsheet = open("data/am/documents/hgef_factsheet_2026_09.md",
                 encoding="utf-8").read()
payload["messages"] = [{"role": "user", "content": factsheet
    + "\n\nQuestion: What is the fund's one-year return?"}]
reply = requests.post(OLLAMA_URL, json=payload, timeout=300).json()
print(reply["message"]["content"])
print("Input tokens:", reply["prompt_eval_count"],
      "| output tokens:", reply["eval_count"])
```

- `payload["messages"] = ...` replaces the test message of Chapter 0 by the document and the question in one user message.
- `reply["prompt_eval_count"]` is the number of input tokens the model read; `reply["eval_count"]` the number it wrote. Chapter 3’s `chat()` function reports the same two counts as `input_tokens` and `output_tokens`.

**Reading the result.** Your count will be above the factsheet’s estimate of 508, for two reasons: the count includes the question and the few tokens the model’s chat template adds around every message, and tables and percentages use more tokens per character than prose. Write down the difference as a percentage of the estimate: it is your model’s correction factor for documents of this kind.

**Checking the answer.** Two checks. (1) The figure in the reply: the factsheet’s 1-year line reads *6.46% \| 7.86% \| −1.40%*, so the fund’s return is **6.46%**; 7.86% is the benchmark’s. (2) The token count: run the same script with an empty document; the difference between the two counts is the factsheet’s real token count, without the instructions.

**Mistakes to avoid.**

- Accepting 7.86% because it is in the document. It is in the same row as the right figure: a model reading a table can take the neighbouring cell. Chapter 6 detects this automatically, by checking the figure’s label as well as its value.
- Comparing the estimate with `input_tokens` without removing the instructions.

**Trade-offs.** The four-characters rule is for budgeting before you build; the count returned by the model is the figure you log and pay for. Measure once per document type and adjust your rule.
