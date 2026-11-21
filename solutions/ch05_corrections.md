# 5. Evaluation: Knowing Whether It Works

## Exercises

**Exercise 5.1.** Print run A’s failures with their reasons, in Python and R. Confirm the two explanations given in the applied example.

**Exercise 5.2.** Fix the false fail on Q08 by making `numbers_in()` recognise the numbers one to twelve written in words. Re-run both runs. What are the new pass rates?

**Exercise 5.3.** Find a false pass. Write an answer to Q10 that is wrong but passes the `text` scorer. Then propose a change to the case or to the scorer that makes it fail.

**Exercise 5.4.** Compute the Wilson interval for run A after the fix of Exercise 5.2. Is run A significantly better than run B?

**Exercise 5.5.** Write four new cases for the evaluation set: one number, one text, one ordered, one not-in-document. Use sections of the prospectus that the set covers least.

**Exercise 5.6.** With Ollama, run `ch05_live_eval.py` (or `.R`). Read every failure and classify it as a model error, a retrieval error (not applicable here, since the whole excerpt is sent) or a scorer error.

## Corrections

### Exercise 5.1

**What the question asks.** List run A’s failed cases with the scorer’s reason, in Python and R, and confirm by reading the answers that one is a false fail and one a true fail.

**The plan.** (1) Filter run A’s results on `passed == False`. (2) Print the id and reason. (3) Read the two answers and judge them against the prospectus.

**Step by step.** In `ch05_score_runs.py`, after the loop:

``` python
print(results["a"][~results["a"].passed][["id", "reason"]]
      .to_string(index=False))
```

- `results["a"]` is run A’s result table, one row per case.
- `~results["a"].passed` inverts the boolean column: `True` for failed cases.
- `[["id", "reason"]]` keeps two columns; `to_string(index=False)` prints without row numbers.

In R:

``` r
print(results$a[!results$a$passed, c("id", "reason")], row.names = FALSE)
```

- `!` inverts the logical column; `c("id", "reason")` selects the two columns.

**Reading the result.**

**What you should see**

``` text
 id                          reason
Q08    expected 6, found []
Q18  answered instead of declining
```

Now read the answers in `evals/candidates/prospectus_qa_run_a.csv`. Q08: *“A loan becomes a Defaulted Loan when six or more monthly payments are due and unpaid.”* Correct, but the scorer found no number (`found []`) because *six* is written in words: a **false fail**. Q18: *“The Class A notes are rated AAA.”* The prospectus contains no rating: the answer is invented, and the scorer was right to fail it: a **true fail**.

**Checking the answer.** The run prints *18/20 passed*; two failures listed, so nothing is hidden. Q08’s answer agrees with Section 4 of the prospectus word for word; Q18’s case has type `not_in_document`, so the only correct answer is a refusal.

**Mistakes to avoid.**

- Counting the pass rate as the quality of the model. Run A’s real quality on these cases is 19/20: one failure is the scorer’s.
- Fixing the case instead of the scorer for Q08. The answer is right; changing `expected` would hide the scorer’s bug.

**Trade-offs.** Reading every failure takes time, but it is the only way to find scorer errors. `found []` is a typical signature of a false fail: the scorer found nothing to compare, which says more about the scorer than about the answer. On large sets, read every failure whose reason contains `found []`, and a sample of the others.

### Exercise 5.2

**What the question asks.** Make the number scorer read the words *one* to *twelve* as numbers, so that Q08 passes, and give the new pass rates of both runs.

**The plan.** (1) In `numbers_in()`, replace number words by digits before extracting numbers. (2) Do the same in R. (3) Re-run both runs. (4) Look for side effects on other cases.

**Step by step.**

``` python
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
         "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
         "twelve": 12}

def numbers_in(text):
    for word, value in WORDS.items():
        text = re.sub(rf"\b{word}\b", str(value), text, flags=re.I)
    return [float(n.replace(",", "")) for n in NUMBER.findall(text)
            if any(ch.isdigit() for ch in n)]
```

- `WORDS` maps each word to its value.
- `rf"\b{word}\b"` is a pattern with word boundaries: it replaces *six* but not the *six* inside *sixty*. `flags=re.I` ignores case, so *Six* is replaced too.
- The last line is the original extraction: `NUMBER` finds numbers with commas and decimals; commas are removed before `float()`.

``` r
number_words <- c(one = 1, two = 2, three = 3, four = 4, five = 5, six = 6,
                  seven = 7, eight = 8, nine = 9, ten = 10, eleven = 11,
                  twelve = 12)
numbers_in <- function(text) {
  for (w in names(number_words))
    text <- gsub(paste0("\\b", w, "\\b"), number_words[[w]], text,
                 ignore.case = TRUE, perl = TRUE)
  n <- regmatches(text, gregexpr("-?\\d[\\d,]*\\.?\\d*", text, perl = TRUE))[[1]]
  as.numeric(gsub(",", "", n))
}
```

- `gsub()` replaces every occurrence; `perl = TRUE` makes `\\b` behave as in Python.
- `gregexpr()` finds all matches; `regmatches()` extracts them as strings.

**Reading the result.** Run A: **19/20 (95%)**; the only failure left is Q18. Run B: **16/20**, unchanged, because its Q08 answer already used the digit: *“After 6 unpaid monthly payments.”*

**Checking the answer.** Look for side effects: *one* is now read as 1 everywhere, so *“one of the classes”* adds a 1 to the numbers found. That can create a false pass only on a `number` case whose expected value is 1 within tolerance. The set’s number cases expect values such as 0.15 (Q11) and 1,500 (Q12); none expects 1, and the re-run shows no new pass or fail other than Q08.

**Mistakes to avoid.**

- Replacing without word boundaries: *often* contains *ten*, and *often* would become *of10*.
- Changing the scorer and re-running only the case you meant to fix. Every scorer change must be re-run on **every** case, and the failures read again: scorers are code and have bugs.

**Trade-offs.** Handling more forms (*twenty-five*, *a half*, *a dozen*) reduces false fails and adds complexity. Another fix is on the prompt side: *“Write all numbers in digits.”* Do both: the prompt makes digits likely, and the tolerant scorer handles the answers that ignore it.

### Exercise 5.3

**What the question asks.** Write a wrong answer to Q10 that the `text` scorer accepts (a false pass), then change the case or the scorer so that it fails.

**The plan.** (1) Read how the `text` scorer decides. (2) Write a wrong answer containing the keyword. (3) Score it. (4) Design a stricter case.

**Step by step.**

*Step 1 — The scorer.* For a `text` case, `score_one()` passes the answer if it contains any of the case’s keywords as a whole word. Q10’s keyword is `revenue`.

*Step 2 — The wrong answer.* *“Recoveries are not revenue receipts; they are principal receipts.”* It contradicts Section 5 but contains *revenue*.

*Step 3 — Score it.* The answer passes: a **false pass**.

*Step 4 — A `choice` scorer.* Add to `score_one()`:

``` python
if kind == "choice":
    options = [o.strip().lower() for o in str(case["keywords"]).split("|")]
    present = [o for o in options if o in answer.lower()]
    ok = present == [case["expected"].lower()]
    return ok, "choice correct" if ok else f"found {present}"
```

- `options` is the list of possible answers, written in the `keywords` column as `revenue|principal`.
- `present` keeps the options that appear in the answer.
- The answer passes only if **exactly** the expected option appears, and no other.

Change Q10’s row to `answer_type` `choice`, `expected` `revenue`, `keywords` `revenue|principal`.

**Reading the result.** The wrong answer now contains both options: `present` is `['revenue', 'principal']`, and the case fails with *found \[‘revenue’, ‘principal’\]*. Run A’s answer, *“Recoveries on Defaulted Loans are revenue receipts.”*, contains only *revenue*: it passes.

**Checking the answer.** Score three answers: the wrong one (fails), run A’s (passes), and *“They are principal receipts.”* (fails, `found ['principal']`). The scorer distinguishes the three as a reader would.

**Mistakes to avoid.**

- Fixing the false pass by adding *not* to a list of forbidden words. Answers can be wrong without *not* (*“they go to principal”*).
- Using a substring check for short options: *principal* would match *principally*. For one-word options it is acceptable; for others, use word boundaries.

**Trade-offs.** Stricter scorers produce more false fails: *“revenue, not principal”* is a correct answer and now fails, because both words appear. The alternative is to change the question: *“Into which receipts are recoveries paid: revenue or principal? Answer with one word.”*, scored by exact match. Either way, prefer the direction of false fails: they are visible when you read failures; false passes are not.

### Exercise 5.4

**What the question asks.** The 95% Wilson interval for run A after the fix (19/20), and whether run A is significantly better than run B (16/20).

**The plan.** (1) Compute both intervals with `wilson_interval()`. (2) Compare them. (3) Compare the runs case by case, with a test that uses the pairing.

**Step by step.**

*Step 1 — The intervals.*

``` python
from aie.evals import wilson_interval
print(wilson_interval(19, 20))
print(wilson_interval(16, 20))
```

`wilson_interval(k, n)` returns the lower and upper bounds of the interval for a proportion of $k$ successes out of $n$, at 95% by default. In R, `wilson_interval(19, 20)` from `aie_r/evals.R`.

*Step 2 — The cases that changed.* The script of the chapter lists them: B fails four cases that A passes (Q05, Q10, Q14, Q16) and passes one that A fails (Q18). After the fix of Exercise 5.2 both pass Q08. The fifteen other cases give the same result in both runs and say nothing about which run is better.

*Step 3 — The paired test.* If A and B were equally good, each of the five changed cases would be equally likely to go either way, like a coin. The exact test (McNemar’s test) asks how surprising a split of 4 to 1 or more extreme is under that assumption:

``` python
from math import comb
a_only, b_only = 4, 1                      # cases only A passes, only B passes
n = a_only + b_only
p = 2 * sum(comb(n, k) for k in range(min(a_only, b_only) + 1)) / 2 ** n
print(n, round(min(p, 1.0), 3))
```

``` r
binom.test(1, 5)$p.value    # 1 case for B out of 5 changed cases
```

- `comb(n, k)` counts the ways to choose $k$ cases out of $n$; the sum is the probability of 1 or 0 wins for B out of 5 under a fair coin, and the factor 2 counts the opposite tail.
- `binom.test()` in R computes the same exact probability.

**Reading the result.** Run A: (0.764, 0.991). Run B: (0.584, 0.919). The intervals overlap between 76.4% and 91.9%. The paired test prints `5 0.375`: a split of 4 to 1 or more extreme happens 37.5% of the time when the two runs are equally good. **No: on 20 cases, run A is not significantly better than run B**, by the intervals or by the paired test. What the paired comparison does give is the list of regressions to read: B misstates the waterfall in Q14, which is a reason to reject B whatever the statistics.

**Checking the answer.** Check A’s interval by hand with the Wilson formula: $\hat p = 0.95$, $n = 20$, $z = 1.96$; centre $= (\hat p + z^2/2n)/(1 + z^2/n) = (0.95 + 0.096)/1.192 = 0.877$; half-width $= z\sqrt{\hat p(1-\hat p)/n + z^2/4n^2}/(1 + z^2/n) = 1.96 \times 0.0691 / 1.192 = 0.114$; interval $(0.764, 0.991)$. It matches.

**Mistakes to avoid.**

- Reading 95% versus 80% as *A is 15 points better*. With 20 cases, one answer is worth 5 points; the uncertainty is larger than the gap.
- Comparing two independent intervals when the runs answered the **same** cases. That throws away the pairing.

**Trade-offs.** Two decisions use the same cases differently. *Is A better on average?* needs more cases: with five changed cases no split can be significant at 5%: even 5 to 0 gives p = 0.0625. A set of 20 can rarely separate two good versions. *Can B be released?* needs only the regressions: one misstatement of the waterfall on a case that matters is enough to stop B. A larger set narrows the intervals too; 100 cases at 95% would give (0.888, 0.978).

### Exercise 5.5

**What the question asks.** Add four cases, one of each type, drawn from the prospectus sections the set covers least.

**The plan.** (1) Count cases per section. (2) Write one case per type for the weakest sections. (3) Check each case against the whole document, not only its section.

**Step by step.**

*Step 1 — Coverage.*

``` python
cases = pd.read_csv("evals/sf_prospectus_qa.csv")
print(cases.source_section.value_counts().sort_index())
```

Sections 1 (overview) and 10 (risk factors) have no case; sections 5, 7 and 9 have one each.

*Step 2 — Four cases* (append to the CSV; columns `id, question, answer_type, expected, tolerance, keywords, source_section`):

``` text
Q21,What percentage of the portfolio by balance is interest-only?,number,13.06,0.001,,8
Q22,Has the issuer entered into an interest rate swap?,text,no,,not entered|no swap|has not,10
Q23,"In the principal priority of payments, which classes are repaid after Class B?",ordered,"C,D",,,7
Q24,What is the expected rating of the Class D notes?,not_in_document,,,,
```

**Reading the result.** Run the set with a candidate answer file containing answers to Q21–Q24: the counts by type now include the new cases, and sections 7, 8 and 10 have one more case each.

**Checking the answer.** Check each case against the document. Q21: Section 8’s table states *Interest-only loans (by balance) 13.06%*. Q22: Section 10 states *The issuer has not entered into an interest rate swap.* Q23: Section 7 repays A, then B, then C, then D. Q24: search the whole excerpt for *rat* — no rating anywhere.

A first draft of Q24 asked *“What is the final maturity date of the Class D notes?”*. Searching the whole document shows why it was rejected: Section 1 gives a final maturity date for the notes (*Interest payment date falling in June 2063*), which applies to every class. An assistant answering *June 2063* would be right and fail the case.

**Mistakes to avoid.**

- Writing a not-in-document case after checking only one section. The answer may be elsewhere.
- Putting the comma-containing `ordered` answer without quotes: the CSV reader would split `C,D` into two columns.

**Trade-offs.** Ambiguous cases are worse than no cases: they punish correct answers and teach you to distrust the evaluation. Spending ten minutes checking each new case against the whole document is the price of a set you can trust.

### Exercise 5.6

**What the question asks.** Run the live evaluation with your model, read every failure and classify it as a model error or a scorer error (retrieval errors cannot occur, as the whole excerpt is sent).

**The plan.** (1) Run the script. (2) Open the saved answers. (3) For each failure, judge the answer against the prospectus. (4) Report.

**Step by step.**

``` bash
python chapters/ch05/python/ch05_live_eval.py
```

The script sends the full excerpt and each question to the model at temperature 0, saves the answers in a timestamped CSV, scores them with `run_eval()`, and prints the pass rate, the Wilson interval and the failures.

**Reading the result.** For each failed `id`, read the answer in the CSV:

- wrong according to the prospectus: **model error**; note the kind (wrong table row, wrong rule, invented fact, a refusal where the document answers);
- right but failed: **scorer error**; fix the scorer as in Exercises 5.2 and 5.3.

One run with `qwen3.5:4b` printed:

**What you should see**

``` text
Live run: 17/20 passed; 95% interval 64% to 95%
 id                        reason
Q05 expected 6082667.80, found []
Q08          expected 6, found []
Q17         expected 95, found []
```

The saved answers classify the three failures. Q05: *“The document does not state this.”* Section 3 states the Reserve Fund Required Amount, £6,082,667.80: a **model error**, a refusal where the document answers. Q08: *“A loan becomes a **Defaulted Loan** when six or more monthly payments are due and unpaid.”* Right, written in words: a **scorer error**, the false fail of Exercise 5.2. Q17: the model declined (*“maximum original loan-to-value”*, 95% in Section 9): a second **model error** of the same kind as Q05. The three not-in-document cases (Q18 to Q20) were declined with the exact sentence of the prompt. The R script gave the same 17/20, with the same three failures. A small model told to decline when unsure sometimes declines too often; the pattern, not the single case, is the finding.

**Checking the answer.** For each model error, find the sentence of the prospectus that contradicts the answer, and write its section number next to the error. For each scorer error, re-score the corrected scorer and confirm the case now passes. An error you cannot point to in the document is not yet classified.

**Mistakes to avoid.**

- Classifying an answer as a model error because it is phrased differently from `expected`. Judge the meaning, then check whether the scorer should accept the phrasing.
- Changing the prompt after reading three failures. Read them all first: several failures may share one cause.

**Trade-offs.** Classifying failures by hand does not scale beyond a few hundred cases, but on a 20-case set it is the most informative ten minutes of the chapter. Write the result as: pass rate, interval, failures with their class, and the change you propose. That paragraph is the beginning of the model documentation of Chapter 20.
