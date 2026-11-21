# 21. The Structured Finance Agent

## Exercises

**Exercise 21.1.** Run the evaluation with Ollama, in Python and R. Fill the release-criteria table with your results and decide whether the agent can be released.

**Exercise 21.2.** Add a case to the evaluation set: *“What share of the pool’s arrears balance was three months or more in arrears at 30 September 2026?”* What is the expected answer, and which tool or tools should the agent call?

**Exercise 21.3.** Write two more guard tests: one question that must be refused and one that must not, chosen to sit close to the boundary of the scope guard.

**Exercise 21.4.** An analyst asks the agent: *“Draft the commentary for the September 2026 investor report.”* Should the agent do it? Propose a design that reuses Chapter 14.

**Exercise 21.5.** Write the *Known limitations* section of the SF agent’s model card.

## Corrections

### Exercise 21.1

**What the question asks.** Run the SF agent’s evaluation with your model in Python and R, fill the release-criteria table, and decide whether the agent can be released.

**The plan.** (1) Run both evaluation scripts. (2) Read the three measures. (3) Fill the table. (4) Decide, and plan the fixes for any gap.

**Step by step.** With Ollama running and the mock stopped:

``` bash
python agents/python/evaluate_agent.py sf
Rscript agents/r/evaluate_agent.R sf
```

For each of the twelve cases, the script asks the `Assistant("sf")`, records the answer, the status and the tools called, and then:

- scores the answers with `run_eval()` (the scorers of Chapter 5);
- counts `right_tool`: the case’s `expected_tool` is among the tools called (cases without an expected tool count as right);
- prints the status counts, the tokens, and each failure with its reason and tools.

**Reading the result.** Fill the table from the printed lines:

| Criterion                | Target            | Your result                               | Met? |
|--------------------------|-------------------|-------------------------------------------|------|
| Correct answers          | ≥ 11 of 12        | `correct answers` line                    |      |
| Right tool on tool cases | 10 of 10          | `right tool used` line, minus A11 and A12 |      |
| Refusals declined        | A11, A12 declined | declined (by the guards)                  | yes  |
| No `stopped` status      | 0                 | `status` line                             |      |

A11 and A12 are declined by the guards on every run, whatever the model. The other ten depend on your model.

**Checking the answer.** For each failure, check the answer and the trace by hand, as in Exercise 9.1: call the expected tool yourself and compare. A05 (excess spread of the collection period ending 31 August 2026, paid on 20 September) must be £412,990.44 from `waterfall_summary("2026-08-31")`; if the agent answered with September’s £692,429.96, the trace shows `cutoff_date` 2026-09-30, a date error, not a tool error.

**Mistakes to avoid.**

- Releasing on 11 of 12 when the failure is A07 or A09, which state a rule of the structure. Read *which* case failed, as Chapter 10’s criteria did for Q10 and Q14.
- Fixing several things at once after one run.

**Trade-offs.** Typical gaps with a small model: A05 and A06 (the period ending 31 August 2026) answered with September’s figures because the model did not change the date; A10 (October 2026) answered with a September figure instead of saying the data ends. Fix one at a time: for dates, an example in the system prompt (*“for ‘August 2026’ use cutoff_date 2026-08-31”*); re-run. The Python and R agents share prompts, tools and data; in the run printed in Step 2 they made the same calls and agreed on eleven cases of twelve, and the one difference (A10) disappeared in a second run. Investigate any case that passes in one language and fails in the other on every run: then the difference is in how the two languages build the messages.

### Exercise 21.2

**What the question asks.** Add the case *“What share of the pool’s arrears balance was three months or more in arrears at 30 September 2026?”*: compute the expected answer and say which tools the agent should call.

**The plan.** (1) Get the bucket balances. (2) Compute the share. (3) Decide where the computation belongs. (4) Write the case.

**Step by step.**

``` python
from aie.tools import arrears_buckets
b = arrears_buckets("2026-09-30")["buckets"]
three_plus = sum(x["balance_gbp"] for x in b if x["bucket"] in ("3 months", "4-5 months"))
total = sum(x["balance_gbp"] for x in b)
print(three_plus, total, round(100 * three_plus / total, 2))
```

- The buckets of 3 months and 4–5 months together are *three months or more* (6 months and more are defaulted loans, not in arrears).
- The total of the four buckets is the arrears balance.

**Reading the result.** £452,041.82 + £528,615.73 = £980,657.55; arrears balance £2,721,210.68; share $980{,}657.55 / 2{,}721{,}210.68 = 36.04\%$.

**Checking the answer.** The arrears balance from the buckets equals `pool_summary("2026-09-30")["arrears_balance_gbp"]`, £2,721,210.68: the two tools agree. And the share must be below 100% and above the 3-month bucket’s share alone (16.61%).

**Mistakes to avoid.**

- Dividing by the pool balance instead of the arrears balance: 0.30%, the answer to a different question.
- Expecting the agent to compute 36.04% and pass verification. The figure is in no tool result; the verifier of Chapter 9 flags it, and the status is `needs_review`.

**Trade-offs.** `arrears_buckets` alone gives both numerator and denominator, but the share is a **computation**, which the agent must not do itself. Two designs: add to each bucket the share of the arrears balance in that bucket *or a longer one* (`this_or_longer_share_of_arrears_pct`), so that 36.04% is computed by code and verifiable; or accept that the question cannot be answered with verified figures and expect `needs_review`. A share per bucket alone is not enough: the model would still add 16.61% and 19.43% itself, and the verifier would flag the sum. Add the case with `answer_type` `number`, expected 36.04, tolerance 0.005, `expected_tool` `arrears_buckets`, and record the design you chose. This case tests the rule of Chapter 1 at its most tempting: a simple division the model *could* do.

**On GitHub.** The companion repository goes further: complete scripts in Python and R that compute the share, run both checks, show the verifier’s decision for each design, and write the evaluation set with case A13, in `solutions/ch21_corrections.md`.

#### Going further on GitHub: the complete computation, both designs tested, and the new case

This part is in the companion repository only. It gives two complete scripts, one in Python and one in R. Each computes the share, checks it, shows the verifier’s decision for each design, and writes the evaluation set with the new case.

**The complete script, in Python.**

`chapters/ch21/python/solutions/ex21_2_arrears_share.py`

``` python
# Exercise 21.2 - Share of the arrears balance three months or more in arrears, and the new evaluation case
# Run from the root of the repository:  python chapters/ch21/python/solutions/ex21_2_arrears_share.py
import csv
import json
import sys

sys.path.insert(0, ".")
from aie.agent import Agent
from aie.tools import arrears_buckets, pool_summary

CUT = "2026-09-30"

# 1. The figures, from the tool the agent would call
result = arrears_buckets(CUT)
buckets = result["buckets"]
total = sum(x["balance_gbp"] for x in buckets)
three_plus = sum(x["balance_gbp"] for x in buckets if x["bucket"] in ("3 months", "4-5 months"))
share = round(100 * three_plus / total, 2)
for x in buckets:
    print(f"{x['bucket']:<11}{x['loans']:>3} loans  £{x['balance_gbp']:>14,.2f}")
print(f"Three months or more: £{three_plus:,.2f} of £{total:,.2f} = {share:.2f}%")

# 2. Checks: the two tools agree, and the share sits where it must
assert round(total, 2) == pool_summary(CUT)["arrears_balance_gbp"], "buckets and pool_summary disagree"
share_3m_only = round(100 * buckets[2]["balance_gbp"] / total, 2)
assert share_3m_only < share < 100
print(f"Checks passed: buckets total = pool_summary arrears balance; {share_3m_only:.2f}% < {share:.2f}% < 100%")

# 3. Design A: the tool as it is. A model that divides writes a figure no tool returned
answer = f"At 30 September 2026, {share:.2f}% of the arrears balance was three months or more in arrears."
verifier = Agent("", [])
u = verifier._verify(answer, [("arrears_buckets", json.dumps(result))])
print("Design A, unsupported figures:", ", ".join(u) or "none")

# 4. Design B: the tool also returns the shares, computed by code
def arrears_buckets_with_shares(cutoff_date, cumulative=True):
    r = arrears_buckets(cutoff_date)
    tot = sum(x["balance_gbp"] for x in r["buckets"])
    for i, x in enumerate(r["buckets"]):
        x["share_of_arrears_pct"] = round(100 * x["balance_gbp"] / tot, 2)
        if cumulative:   # share of the arrears balance in this bucket or a longer one
            x["this_or_longer_share_of_arrears_pct"] = round(100 * sum(y["balance_gbp"] for y in r["buckets"][i:]) / tot, 2)
    return r

for cumulative in (False, True):
    r = arrears_buckets_with_shares(CUT, cumulative)
    label = "B2, with cumulative shares" if cumulative else "B1, shares per bucket only"
    u = verifier._verify(answer, [("arrears_buckets", json.dumps(r))])
    print(f"Design {label}, unsupported figures:", ", ".join(u) or "none")

# 5. The evaluation case, added to a copy of the evaluation set
rows = list(csv.DictReader(open("evals/sf_agent_eval.csv", encoding="utf-8")))
rows.append({"id": "A13",
             "question": "What share of the pool's arrears balance was three months or more in arrears at 30 September 2026?",
             "answer_type": "number", "expected": f"{share:.2f}", "tolerance": "0.005", "keywords": "",
             "expected_tool": "arrears_buckets"})
with open("evals/solutions/sf_agent_eval_ex21_2.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(f"evals/solutions/sf_agent_eval_ex21_2.csv: {len(rows)} cases, the last one A13 (expected {share:.2f})")
```

- **Section 1** calls `arrears_buckets()` directly, the function the agent would call. The bucket test `in ("3 months", "4-5 months")` uses the labels of the tool’s result, so it stays right if the order of the buckets ever changes.
- **Section 2** writes the two checks of the correction as `assert` statements: the script stops at the first broken one instead of printing a wrong share.
- **Section 3** builds the answer a model would write and passes it to the agent’s own verifier, `Agent._verify()`, with the tool result as the agent would have received it (a JSON string). An empty agent, `Agent("", [])`, is enough: `_verify()` uses only the answer and the results.
- **Section 4** builds Design B in two versions. B1 adds `share_of_arrears_pct` to each bucket; B2 also adds `this_or_longer_share_of_arrears_pct`, the share in this bucket or a longer one. `r["buckets"][i:]` is the slice from bucket `i` to the last one.
- **Section 5** copies the evaluation set and adds case A13 to the copy, in `evals/solutions/`, so that the set of Chapter 21 stays unchanged.

**Output**

``` text
1 month      5 loans  £    652,077.10
2 months     6 loans  £  1,088,476.03
3 months     3 loans  £    452,041.82
4-5 months   4 loans  £    528,615.73
Three months or more: £980,657.55 of £2,721,210.68 = 36.04%
Checks passed: buckets total = pool_summary arrears balance; 16.61% < 36.04% < 100%
Design A, unsupported figures: 36.04%
Design B1, shares per bucket only, unsupported figures: 36.04%
Design B2, with cumulative shares, unsupported figures: none
evals/solutions/sf_agent_eval_ex21_2.csv: 13 cases, the last one A13 (expected 36.04)
```

**Reading the result.** Design A flags 36.04%: no tool returned it. Design B1 flags it too: 16.61% and 19.43% are now verified, but their sum is still the model’s arithmetic. Only B2 makes 36.04% a figure that code computed, so only B2 lets the agent answer the question with status `verified`.

**The complete script, in R.**

`chapters/ch21/r/solutions/ex21_2_arrears_share.R`

``` r
# Exercise 21.2 - Share of the arrears balance three months or more in arrears, and the new evaluation case
# Run from the root of the repository:  Rscript chapters/ch21/r/solutions/ex21_2_arrears_share.R
suppressPackageStartupMessages(source("aie_r/agent.R"))
cut <- "2026-09-30"

# 1. The figures, from the tool the agent would call
result <- arrears_buckets(cut)
bal <- vapply(result$buckets, `[[`, 0, "balance_gbp")
lab <- vapply(result$buckets, `[[`, "", "bucket")
total <- sum(bal); three_plus <- sum(bal[lab %in% c("3 months", "4-5 months")])
share <- round(100 * three_plus / total, 2)
for (i in seq_along(bal))
  cat(sprintf("%-11s%3d loans  £%14s\n", lab[i], result$buckets[[i]]$loans, formatC(bal[i], format = "f", digits = 2, big.mark = ",")))
cat(sprintf("Three months or more: £%s of £%s = %.2f%%\n", formatC(three_plus, format = "f", digits = 2, big.mark = ","),
            formatC(total, format = "f", digits = 2, big.mark = ","), share))

# 2. Checks: the two tools agree, and the share sits where it must
stopifnot(round(total, 2) == pool_summary(cut)$arrears_balance_gbp)
share_3m_only <- round(100 * bal[3] / total, 2)
stopifnot(share_3m_only < share, share < 100)
cat(sprintf("Checks passed: buckets total = pool_summary arrears balance; %.2f%% < %.2f%% < 100%%\n", share_3m_only, share))

# 3. Design A: the tool as it is. A model that divides writes a figure no tool returned
answer <- sprintf("At 30 September 2026, %.2f%% of the arrears balance was three months or more in arrears.", share)
as_result <- function(r) list(list(name = "arrears_buckets", result = as.character(toJSON(r, auto_unbox = TRUE, digits = NA))))
u <- verify_answer(answer, as_result(result))
cat("Design A, unsupported figures:", if (length(u)) paste(u, collapse = ", ") else "none", "\n")

# 4. Design B: the tool also returns the shares, computed by code
arrears_buckets_with_shares <- function(cutoff_date, cumulative = TRUE) {
  r <- arrears_buckets(cutoff_date)
  b <- vapply(r$buckets, `[[`, 0, "balance_gbp"); tot <- sum(b)
  for (i in seq_along(b)) {
    r$buckets[[i]]$share_of_arrears_pct <- round(100 * b[i] / tot, 2)
    if (cumulative) r$buckets[[i]]$this_or_longer_share_of_arrears_pct <- round(100 * sum(b[i:length(b)]) / tot, 2)
  }
  r
}
for (cumulative in c(FALSE, TRUE)) {
  u <- verify_answer(answer, as_result(arrears_buckets_with_shares(cut, cumulative)))
  cat(sprintf("Design %s, unsupported figures: %s\n",
              if (cumulative) "B2, with cumulative shares" else "B1, shares per bucket only",
              if (length(u)) paste(u, collapse = ", ") else "none"))
}

# 5. The evaluation case, added to a copy of the evaluation set
ev <- read.csv("evals/sf_agent_eval.csv", stringsAsFactors = FALSE, colClasses = "character")
ev <- rbind(ev, data.frame(id = "A13",
  question = "What share of the pool's arrears balance was three months or more in arrears at 30 September 2026?",
  answer_type = "number", expected = sprintf("%.2f", share), tolerance = "0.005", keywords = "",
  expected_tool = "arrears_buckets"))
dir.create("evals/solutions", showWarnings = FALSE)
write.csv(ev, "evals/solutions/sf_agent_eval_ex21_2_r.csv", row.names = FALSE, na = "")
cat(sprintf("evals/solutions/sf_agent_eval_ex21_2_r.csv: %d cases, the last one A13 (expected %.2f)\n", nrow(ev), share))
```

**Output**

``` text
1 month      5 loans  £    652,077.10
2 months     6 loans  £  1,088,476.03
3 months     3 loans  £    452,041.82
4-5 months   4 loans  £    528,615.73
Three months or more: £980,657.55 of £2,721,210.68 = 36.04%
Checks passed: buckets total = pool_summary arrears balance; 16.61% < 36.04% < 100%
Design A, unsupported figures: 36.04% 
Design B1, shares per bucket only, unsupported figures: 36.04%
Design B2, with cumulative shares, unsupported figures: none
evals/solutions/sf_agent_eval_ex21_2_r.csv: 13 cases, the last one A13 (expected 36.04)
```

- `` vapply(result$buckets, `[[`, 0, "balance_gbp") `` extracts one field from each bucket into a numeric vector; the `0` declares the type of the result.
- `as_result()` turns a result into the JSON string `verify_answer()` expects, as `run_tool()` does in the agent.
- `colClasses = "character"` reads every column of the evaluation set as text, so that `0.005` and `36.04` are written back exactly as they were.

Python and R give the same figures and the same three decisions.

**More mistakes to avoid.**

- Adding the case to `evals/sf_agent_eval.csv` itself before you have chosen the design. With the tool as it is, A13 can only end in `needs_review`, and the release criteria of Chapter 21 then fall for a reason the agent cannot fix.
- Rounding the share before summing. 16.61% + 19.43% gives 36.04% here, but rounded parts do not add up to the rounded whole in general; compute from the balances, as the script does.

**More trade-offs.** Design B2 answers this question and its neighbours (*“two months or more”*, *“one month or more”*) with no new tool, at the cost of two fields per bucket in every result, which the model reads at every call. A dedicated tool, `arrears_share(cutoff_date, min_months)`, keeps `arrears_buckets` short, at the cost of one more tool for the agent to choose from.

### Exercise 21.3

**What the question asks.** Write two guard tests close to the boundary of the scope guard: one question that must be refused, one that must not.

**The plan.** (1) Read the guard’s rule. (2) Choose a question just outside the scope and one just inside that shares words with the other domain. (3) Add both to the tests in both languages. (4) Run.

**Step by step.** The SF guard in `aie/assistants.py` refuses a question if it contains an AM word **and** no SF word:

``` python
if self.domain == "sf" and AM_WORDS.search(question) and not SF_WORDS.search(question):
    return OUT_OF_SCOPE_SF
```

`AM_WORDS` holds Harbourline’s name, the fund codes and AM document names (*factsheet*, *KID*, *SFDR*, *equity fund*, *bond fund*); `SF_WORDS` holds Larkfield’s terms (*Larkfield*, *Class A–D*, *tape*, *waterfall*, *prospectus*, *reserve fund*, *arrears*, *CPR*).

The two tests, added to `tests/test_assistants.py`:

``` python
checks.append(("SF refuses an AM comparison",
    sf.guard_question("Compare the HGEF factsheet with the HECB KID.") == OUT_OF_SCOPE_SF))
checks.append(("SF accepts 'fund' in a Larkfield question",
    sf.guard_question("Which fund does the Larkfield reserve fund protect?") is None))
```

and to the `checks` vector of `tests/test_assistants.R`:

``` r
  "SF refuses an AM comparison" =
    identical(guard_question(sf, "Compare the HGEF factsheet with the HECB KID."), out_of_scope_sf),
  "SF accepts 'fund' in a Larkfield question" =
    is.null(guard_question(sf, "Which fund does the Larkfield reserve fund protect?")),
```

**Reading the result.** The first question contains *HGEF*, *factsheet*, *HECB* and *KID*, and no SF word: refused. The second contains *fund*, which is not an AM word on its own, and *Larkfield* and *reserve fund*, which are SF words: accepted. Both tests pass: 10/10.

**Checking the answer.** Probe the boundary further: *“What is the bond fund duration?”* is refused (*bond fund* is an AM word); *“Which notes does the reserve fund protect?”* is accepted. Adding *fund* alone to `AM_WORDS` changes nothing for the second question, because its SF words keep it in scope. Simplify the rule to *refuse any question with an AM word* as well, and the second test fails at once: the test protects the boundary against a well-meant change.

**Mistakes to avoid.**

- Testing only obvious cases (*“What is HGEF’s return?”*). Boundary tests are the ones that catch regressions.
- Writing the tests in one language only: the R guard has its own word lists, and they can drift.

**Trade-offs.** Keyword guards are cheap, instant and testable, and they miss unusual phrasings (*“the euro credit product”*). Every miss found in production becomes a new test and, if needed, a new word. A model-based classifier would catch more phrasings at the cost of a model call and of its own evaluation; keep the keyword guard first either way, since it is free and certain on the cases it covers.

**On GitHub.** The companion repository goes further: both test files with the two new tests (10/10), and a script in Python and R that probes the boundary and shows which change of the guard the second test catches, in `solutions/ch21_corrections.md`.

#### Going further on GitHub: the complete test files, and the boundary probed

This part is in the companion repository only. It gives the two test files with the new tests in place, and a script in each language that probes the boundary. The script shows which change of the guard the second test catches, and which change it does not catch.

**The test files.** `tests/solutions/test_assistants_ex21_3.py` and `tests/solutions/test_assistants_ex21_3.R` are copies of the tests of Chapter 21 with the two boundary tests added after *“SF keeps ‘reserve fund’ in scope”*. Run them from the repository root:

**Output**

``` text
PASS  SF refuses a fund question
PASS  AM refuses a Larkfield question
PASS  AM refuses advice
PASS  AM refuses a forecast
PASS  AM refuses reworded advice
PASS  SF refuses advice
PASS  SF keeps 'reserve fund' in scope
PASS  SF refuses an AM comparison
PASS  SF accepts 'fund' in a Larkfield question
PASS  SF scripted run is verified
10/10 checks passed
```

**Output**

``` text
PASS  SF refuses a fund question 
PASS  AM refuses a Larkfield question 
PASS  AM refuses advice 
PASS  AM refuses a forecast 
PASS  AM refuses reworded advice 
PASS  SF refuses advice 
PASS  SF keeps 'reserve fund' in scope 
PASS  SF refuses an AM comparison 
PASS  SF accepts 'fund' in a Larkfield question 
PASS  SF scripted run is verified 
10/10 checks passed
```

**The probe, in Python.** It runs five questions through the guard as shipped. It then runs them again after two changes a colleague could make.

`chapters/ch21/python/solutions/ex21_3_probe_boundary.py`

``` python
# Exercise 21.3 - Probe the boundary of the SF scope guard, and show the test protecting it
# Run from the root of the repository:  python chapters/ch21/python/solutions/ex21_3_probe_boundary.py
import re
import sys

sys.path.insert(0, ".")
import aie.assistants as A

sf = A.Assistant("sf")
probes = ["Compare the HGEF factsheet with the HECB KID.",
          "Which fund does the Larkfield reserve fund protect?",
          "What is the bond fund duration?",
          "Which notes does the reserve fund protect?",
          "What is the duration of the euro credit product?"]


def show(title):
    print(title)
    for q in probes:
        r = sf.guard_question(q)
        print(f"  {'refused ' if r == A.OUT_OF_SCOPE_SF else 'accepted'}  {q}")


show("Guard as shipped:")

# Change 1: add 'fund' on its own to the asset management words
shipped_words, shipped_guard = A.AM_WORDS, A.Assistant.guard_question
A.AM_WORDS = re.compile(shipped_words.pattern.replace("equity fund|bond fund", "equity fund|bond fund|fund"), re.I)
show("Change 1, 'fund' added to AM_WORDS:")


# Change 2: on top of change 1, simplify the rule to 'refuse any question with an AM word'
def simplified(self, question):
    if self.domain == "sf" and A.AM_WORDS.search(question):
        return A.OUT_OF_SCOPE_SF
    return shipped_guard(self, question)


A.Assistant.guard_question = simplified
show("Change 2, and the rule simplified:")
ok = sf.guard_question("Which fund does the Larkfield reserve fund protect?") is None
print("Test 'SF accepts fund in a Larkfield question':", "PASS" if ok else "FAIL")
A.AM_WORDS, A.Assistant.guard_question = shipped_words, shipped_guard
```

- `import aie.assistants as A` imports the module itself, so that the script can replace `A.AM_WORDS`: `guard_question()` reads the module’s variable each time it runs.
- `shipped.pattern.replace(...)` builds the new expression from the shipped one, so the change is exactly one word.
- `A.Assistant.guard_question = simplified` replaces the method for every assistant; `shipped_guard(self, question)` keeps the advice guard of the original for the other cases.
- The last line restores both, so that the probe leaves the module as it found it.

**Output**

``` text
Guard as shipped:
  refused   Compare the HGEF factsheet with the HECB KID.
  accepted  Which fund does the Larkfield reserve fund protect?
  refused   What is the bond fund duration?
  accepted  Which notes does the reserve fund protect?
  accepted  What is the duration of the euro credit product?
Change 1, 'fund' added to AM_WORDS:
  refused   Compare the HGEF factsheet with the HECB KID.
  accepted  Which fund does the Larkfield reserve fund protect?
  refused   What is the bond fund duration?
  accepted  Which notes does the reserve fund protect?
  accepted  What is the duration of the euro credit product?
Change 2, and the rule simplified:
  refused   Compare the HGEF factsheet with the HECB KID.
  refused   Which fund does the Larkfield reserve fund protect?
  refused   What is the bond fund duration?
  refused   Which notes does the reserve fund protect?
  accepted  What is the duration of the euro credit product?
Test 'SF accepts fund in a Larkfield question': FAIL
```

**Reading the result.** Change 1 alone changes no decision. *“Which fund does the Larkfield reserve fund protect?”* now contains an AM word (*fund*), but also SF words (*Larkfield*, *reserve fund*), and the rule refuses only when there is no SF word. Change 2 removes that condition, and the second test fails, as do the two other in-scope questions. The fifth question, *“the euro credit product”*, is accepted in every version: the miss the trade-off describes, which only a new word or a classifier would catch.

**The probe, in R.**

`chapters/ch21/r/solutions/ex21_3_probe_boundary.R`

``` r
# Exercise 21.3 - Probe the boundary of the SF scope guard, and show the test protecting it
# Run from the root of the repository:  Rscript chapters/ch21/r/solutions/ex21_3_probe_boundary.R
suppressPackageStartupMessages(source("aie_r/assistants.R"))
sf <- new_assistant("sf")
probes <- c("Compare the HGEF factsheet with the HECB KID.",
            "Which fund does the Larkfield reserve fund protect?",
            "What is the bond fund duration?",
            "Which notes does the reserve fund protect?",
            "What is the duration of the euro credit product?")
show <- function(title) {
  cat(title, "\n")
  for (q in probes)
    cat(sprintf("  %s  %s\n", if (identical(guard_question(sf, q), out_of_scope_sf)) "refused " else "accepted", q))
}
show("Guard as shipped:")

# Change 1: add 'fund' on its own to the asset management words
shipped_words <- am_words; shipped_guard <- guard_question
am_words <- sub("equity fund|bond fund", "equity fund|bond fund|fund", am_words, fixed = TRUE)
show("Change 1, 'fund' added to am_words:")

# Change 2: on top of change 1, simplify the rule to 'refuse any question with an AM word'
guard_question <- function(a, question) {
  if (a$domain == "sf" && grepl(am_words, question, ignore.case = TRUE, perl = TRUE)) return(out_of_scope_sf)
  shipped_guard(a, question)
}
show("Change 2, and the rule simplified:")
ok <- is.null(guard_question(sf, "Which fund does the Larkfield reserve fund protect?"))
cat("Test 'SF accepts fund in a Larkfield question':", if (ok) "PASS" else "FAIL", "\n")
am_words <- shipped_words; guard_question <- shipped_guard
```

**Output**

``` text
Guard as shipped: 
  refused   Compare the HGEF factsheet with the HECB KID.
  accepted  Which fund does the Larkfield reserve fund protect?
  refused   What is the bond fund duration?
  accepted  Which notes does the reserve fund protect?
  accepted  What is the duration of the euro credit product?
Change 1, 'fund' added to am_words: 
  refused   Compare the HGEF factsheet with the HECB KID.
  accepted  Which fund does the Larkfield reserve fund protect?
  refused   What is the bond fund duration?
  accepted  Which notes does the reserve fund protect?
  accepted  What is the duration of the euro credit product?
Change 2, and the rule simplified: 
  refused   Compare the HGEF factsheet with the HECB KID.
  refused   Which fund does the Larkfield reserve fund protect?
  refused   What is the bond fund duration?
  refused   Which notes does the reserve fund protect?
  accepted  What is the duration of the euro credit product?
Test 'SF accepts fund in a Larkfield question': FAIL 
```

- In R, `am_words` and `guard_question` are variables of the global environment; reassigning them changes the guard for the rest of the session, which is why the last line restores both.

**More mistakes to avoid.**

- Changing the shipped word lists to run a probe. Change a copy, or restore the original at the end, as the scripts do; otherwise the tests that follow run against a guard nobody shipped.
- Reading a passing test as proof that a change is safe. Change 1 passes every test and still changes the meaning of `AM_WORDS`; a new test for *“What is the fund’s duration?”* would record the intended decision for that case.

**More trade-offs.** Each boundary test fixes one decision. Twenty such tests make the guard slow to change; two make it easy to break. Keep one test per reason for the boundary: a word shared by both domains (*fund*), a document name (*factsheet*), a code (*HGEF*), a phrasing the guard misses on purpose.

### Exercise 21.4

**What the question asks.** Decide whether the agent should draft the September 2026 investor report commentary on request, and propose a design that reuses Chapter 14.

**The plan.** (1) Apply Chapter 9’s rule: fixed steps make a workflow. (2) Expose the workflow as a tool. (3) Decide the status of the answer. (4) Test the tool.

**Step by step.** The commentary is a monthly task with fixed steps; an agent would choose its own tools and might skip a figure. So the agent should not *compose* it; it should *call* the workflow. Register the Chapter 14 workflow as a draft tool:

``` python
import pandas as pd
from aie.investor_report import (TAPE, month_figures, reconcile,
                                 template_commentary, check_commentary)

DATES = sorted(pd.read_csv(TAPE)["RREL6"].unique())[1:]

def draft_investor_commentary(cutoff_date):
    if cutoff_date not in DATES:
        raise ValueError(f"no investor report for {cutoff_date}; "
                         f"reports run from {DATES[0]} to {DATES[-1]}")
    f = month_figures(cutoff_date)
    checks = reconcile(f)
    if not all(checks.values()):
        raise ValueError("reconciliation failed: " +
                         "; ".join(k for k, ok in checks.items() if not ok))
    text = template_commentary(f)          # or draft_commentary(f) of Exercise 14.2
    return {"cutoff_date": cutoff_date, "commentary": text,
            "unsupported_figures": [raw for raw, hits in check_commentary(text, f) if not hits],
            "approval_required": True}

REGISTRY["draft_investor_commentary"] = (
    draft_investor_commentary,
    "Draft the commentary of the Larkfield 2025-1 investor report for one "
    "collection period, after the reconciliations pass. The draft must be "
    "approved by an analyst before publication.",
    {"type": "object",
     "properties": {"cutoff_date": {"type": "string",
                                    "pattern": "20[0-9]{2}-[0-9]{2}-[0-9]{2}"}},
     "required": ["cutoff_date"], "additionalProperties": False})
```

- The date check gives the model a clear message for dates without a report.
- The reconciliation gate of Chapter 14 runs first; a failure becomes an error the model must report.
- `ValueError` is turned by `run_tool()` into `{"error": ...}`, which the model reads.
- `approval_required` tells the agent and the application that this draft is never final.

Add the tool to the SF assistant’s tool list.

**Reading the result.** `run_tool()` with `2026-09-30` returns the commentary (*“In the period ending 2026-09-30, principal receipts of £4.88 million …”*) with `unsupported_figures: []`. With `2026-10-31`: `{"error": "no investor report for 2026-10-31; reports run from 2025-07-31 to 2026-09-30"}`.

**Checking the answer.** Call the tool with `2025-06-30`, the closing date: the same clear error, where `month_figures()` alone would raise an unexplained `KeyError`. And break the notes file as in Exercise 14.4: the tool returns *reconciliation failed: notes - PDL = pool*, and no commentary.

**Mistakes to avoid.**

- Letting the agent call the three data tools and write the commentary itself. That is the unpredictable path Exercise 9.4 rejected.
- Returning the draft with status `verified`. A commentary for investors is always approved by a person (Chapter 20).

**Trade-offs.** The agent becomes a front door to the workflow: the analyst asks in words, the workflow does the fixed steps, the analyst approves. Give the answer status `needs_review` whenever this tool ran: three lines after `ask()`, which check the trace. The cost is one more tool in the agent’s list, which lengthens its tool descriptions; keep the description precise so that the agent calls it only for commentary requests.

**On GitHub.** The companion repository goes further: the complete tool in Python and R, its tests on three dates and on a broken notes file, the `needs_review` wrapper, a scripted run of the agent, and the figures the tool must return so that the agent’s answer can be verified, in `solutions/ch21_corrections.md`.

#### Going further on GitHub: the complete tool, tested, and the agent that uses it

This part is in the companion repository only. It gives the complete tool in Python and R, tested on three dates and on a broken notes file. It also gives the wrapper that gives the answer status `needs_review`, and a scripted run of the agent with the new tool. It adds one thing the book’s code lacks: the figures the tool must return, so that the agent’s answer can be verified.

**The complete script, in Python.** Start the mock model on the script of this exercise, then run it from the repository root:

``` bash
MOCK_SCRIPT=tools/scripts/ex21_4_commentary.json python tools/mock_ollama.py &
python chapters/ch21/python/solutions/ex21_4_commentary_tool.py
```

`chapters/ch21/python/solutions/ex21_4_commentary_tool.py`

``` python
# Exercise 21.4 - The investor report workflow of Chapter 14 as a tool of the SF agent
# Run from the root of the repository, with the mock model on the script of this exercise:
#   MOCK_SCRIPT=tools/scripts/ex21_4_commentary.json python tools/mock_ollama.py &
#   python chapters/ch21/python/solutions/ex21_4_commentary_tool.py
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, ".")
import pandas as pd

import aie.investor_report as ir
from aie.assistants import Assistant
from aie.investor_report import TAPE, check_commentary, facts, month_figures, reconcile, template_commentary
from aie.tools import REGISTRY, run_tool

DATES = sorted(pd.read_csv(TAPE)["RREL6"].unique())[1:]          # collection period ends: no report at closing
SUFFIX = {"money": "_gbp", "percent": "_pct", "number": ""}


def draft_investor_commentary(cutoff_date):
    if cutoff_date not in DATES:
        raise ValueError(f"no investor report for {cutoff_date}; "
                         f"reports run from {DATES[0]} to {DATES[-1]}")
    f = month_figures(cutoff_date)
    checks = reconcile(f)
    if not all(checks.values()):
        raise ValueError("reconciliation failed: " +
                         "; ".join(k for k, ok in checks.items() if not ok))
    text = template_commentary(f)          # or draft_commentary(f) of Exercise 14.2
    return {"cutoff_date": cutoff_date, "commentary": text,
            "unsupported_figures": [raw for raw, hits in check_commentary(text, f) if not hits],
            "approval_required": True,
            # Going further than the book: the figures the commentary may quote, named with the unit suffixes
            # the agent's verifier reads (_gbp, _pct), so that an answer quoting the draft can be verified.
            "figures": {name.replace(" ", "_") + SUFFIX[unit]: round(float(v), 4)
                        for name, (v, unit) in facts(f).items()}}


REGISTRY["draft_investor_commentary"] = (
    draft_investor_commentary,
    "Draft the commentary of the Larkfield 2025-1 investor report for one "
    "collection period, after the reconciliations pass. The draft must be "
    "approved by an analyst before publication.",
    {"type": "object",
     "properties": {"cutoff_date": {"type": "string",
                                    "pattern": "20[0-9]{2}-[0-9]{2}-[0-9]{2}"}},
     "required": ["cutoff_date"], "additionalProperties": False})


def ask_sf(assistant, question):
    """The SF assistant's answer, with the status forced to needs_review when the commentary tool ran."""
    r = assistant.ask(question)
    if any(step[0] == "draft_investor_commentary" for step in r["trace"]):
        r["status"] = "needs_review"
        r["unsupported"] = r["unsupported"] + ["investor commentary: approval required"]
    return r


# 1. The tool on its own, through run_tool() as the agent calls it
for date in ("2026-09-30", "2026-10-31", "2025-06-30"):
    out = json.loads(run_tool({"name": "draft_investor_commentary", "arguments": {"cutoff_date": date}}))
    print(date, "->", out.get("error") or out["commentary"][:70] + "...",
          "" if "error" in out else f"| unsupported: {out['unsupported_figures']}")

# 2. The reconciliation gate: break one note balance in a copy of the notes file
tmp = tempfile.mkdtemp()
broken = os.path.join(tmp, "notes.csv")
notes = pd.read_csv(ir.NOTES)
row = (notes["cutoff"] == "2026-09-30") & (notes["cls"] == "A")
notes.loc[row, "closing"] += 100.0
notes.to_csv(broken, index=False)
shipped, ir.NOTES = ir.NOTES, broken
out = json.loads(run_tool({"name": "draft_investor_commentary", "arguments": {"cutoff_date": "2026-09-30"}}))
print("broken notes ->", out)
ir.NOTES = shipped
shutil.rmtree(tmp)

# 3. The agent with the new tool, on the scripted model
sf = Assistant("sf")
sf.agent.tool_names = sf.agent.tool_names + ["draft_investor_commentary"]
r = ask_sf(sf, "Draft the commentary for the September 2026 investor report.")
print("agent tools used:", [step[0] for step in r["trace"]])
print("status:", r["status"], "| flags:", r["unsupported"])

# 4. Why the tool returns its figures: without them, the verifier cannot support the quoted commentary
from aie.agent import Agent
text = template_commentary(month_figures("2026-09-30"))
bare = json.dumps({"cutoff_date": "2026-09-30", "commentary": text, "approval_required": True})
print("without 'figures', unsupported:", Agent("", [])._verify(text, [("draft_investor_commentary", bare)]))
```

- `draft_investor_commentary()` is the code of the book with one more field, `figures`. `facts(f)` of Chapter 14 lists every figure the commentary may quote with its unit; the comprehension names each one with the suffix the verifier reads (`principal_receipts_gbp`, `arrears_ratio_pct`).
- `ask_sf()` is the three-line wrapper of the trade-off: if the trace contains the tool, the status becomes `needs_review` and the reason is added to the flags.
- **Section 2** breaks the reconciliation without touching the data. It writes a copy of the notes file with £100 added to the Class A closing balance of September 2026, points `aie.investor_report.NOTES` at the copy, runs the tool, and restores the path. `month_figures()` reads `NOTES` each time it runs, which is why replacing the module’s variable works.
- **Section 3** adds the tool to the SF agent’s tool list for this run only: `sf.agent.tool_names + [...]` builds a new list, and the shipped assistant is unchanged.
- **Section 4** removes `figures` from the result and runs the verifier again.

**Output**

``` text
2026-09-30 -> In the period ending 2026-09-30, principal receipts of £4.88 million w... | unsupported: []
2026-10-31 -> no investor report for 2026-10-31; reports run from 2025-07-31 to 2026-09-30 
2025-06-30 -> no investor report for 2025-06-30; reports run from 2025-07-31 to 2026-09-30 
broken notes -> {'error': 'reconciliation failed: notes - PDL = pool'}
agent tools used: ['draft_investor_commentary']
status: needs_review | flags: ['investor commentary: approval required']
without 'figures', unsupported: ['£4.88 million', '£4.88 million', '0.84%', '0.97%', '14.8%', '£6,082,667.80']
```

**Reading the result.** Section 1 gives the draft for September 2026 with no unsupported figure, and the same clear error for a date after the last report and for the closing date. Section 2 stops at the gate: *reconciliation failed: notes - PDL = pool*. Section 3 shows the agent calling the tool and the answer flagged for approval, and no other flag. Section 4 shows why the `figures` field is needed. Without it, all six figures of the commentary are unsupported, because the commentary is text and the verifier reads only numbers. The agent would then spend its one correction on figures that are right.

**The complete script, in R.**

`chapters/ch21/r/solutions/ex21_4_commentary_tool.R`

``` r
# Exercise 21.4 - The investor report workflow of Chapter 14 as a tool of the SF agent
# Run from the root of the repository, with the mock model on the script of this exercise:
#   MOCK_SCRIPT=tools/scripts/ex21_4_commentary.json python tools/mock_ollama.py &
#   Rscript chapters/ch21/r/solutions/ex21_4_commentary_tool.R
suppressPackageStartupMessages({source("aie_r/assistants.R"); source("aie_r/investor_report.R")})

dates <- sort(unique(read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")$RREL6))[-1]   # no report at closing

commentary_figures <- function(f) {
  # the figures the commentary may quote, named with the unit suffixes the verifier reads
  list(principal_receipts_gbp = f$principal, class_a_principal_paid_gbp = f$notes["A", "principal_paid"],
       arrears_ratio_pct = round(f$arrears_ratio, 4), previous_arrears_ratio_pct = round(f$prev_arrears_ratio, 4),
       cpr_pct = round(f$cpr, 4), reserve_fund_gbp = f$reserve, pool_balance_gbp = f$pool)
}

draft_investor_commentary <- function(cutoff_date) {
  if (!cutoff_date %in% dates)
    stop(sprintf("no investor report for %s; reports run from %s to %s", cutoff_date, dates[1], dates[length(dates)]))
  f <- month_figures(cutoff_date)
  checks <- reconcile(f)
  if (!all(checks)) stop("reconciliation failed: ", paste(names(checks)[!checks], collapse = "; "))
  text <- template_commentary(f)
  figs <- commentary_figures(f)
  facts <- lapply(names(figs), function(n)
    list(value = figs[[n]], unit = if (endsWith(n, "_gbp")) "money" else "percent"))
  names(facts) <- names(figs)
  unsupported <- vapply(Filter(function(r) !length(r$hits), check_text(text, facts)), function(r) r$figure$raw, "")
  list(cutoff_date = cutoff_date, commentary = text, unsupported_figures = I(unsupported),
       approval_required = TRUE, figures = figs)
}

registry$draft_investor_commentary <- list(fn = draft_investor_commentary,
  description = paste("Draft the commentary of the Larkfield 2025-1 investor report for one collection period,",
                      "after the reconciliations pass. The draft must be approved by an analyst before publication."),
  parameters = list(type = "object", properties = list(cutoff_date = date_rule),
                    required = list("cutoff_date"), additionalProperties = FALSE))

ask_sf <- function(a, question) {
  # the SF assistant's answer, with the status forced to needs_review when the commentary tool ran
  r <- ask_assistant(a, question)
  if (any(vapply(r$trace, function(s) identical(s$name, "draft_investor_commentary"), TRUE))) {
    r$status <- "needs_review"; r$unsupported <- c(r$unsupported, "investor commentary: approval required")
  }
  r
}

# 1. The tool on its own, through run_tool() as the agent calls it
for (d in c("2026-09-30", "2026-10-31", "2025-06-30")) {
  out <- fromJSON(run_tool(list(name = "draft_investor_commentary", arguments = list(cutoff_date = d))))
  cat(d, "->", if (!is.null(out$error)) out$error else
        paste0(substr(out$commentary, 1, 70), "... | unsupported: [", paste(out$unsupported_figures, collapse = ", "), "]"), "\n")
}

# 2. The reconciliation gate: break one note balance on the way in
shipped <- month_figures
month_figures <- function(cutoff) { f <- shipped(cutoff); f$notes["A", "closing"] <- f$notes["A", "closing"] + 100; f }
cat("broken notes ->", fromJSON(run_tool(list(name = "draft_investor_commentary",
                                              arguments = list(cutoff_date = "2026-09-30"))))$error, "\n")
month_figures <- shipped

# 3. The agent with the new tool, on the scripted model
sf <- new_assistant("sf"); sf$tools <- c(sf$tools, "draft_investor_commentary")
r <- ask_sf(sf, "Draft the commentary for the September 2026 investor report.")
cat("agent tools used:", vapply(r$trace, `[[`, "", "name"), "\n")
cat("status:", r$status, "| flags:", paste(r$unsupported, collapse = "; "), "\n")
```

**Output**

``` text
2026-09-30 -> In the period ending 2026-09-30, principal receipts of £4.88 million w... | unsupported: [] 
2026-10-31 -> no investor report for 2026-10-31; reports run from 2025-07-31 to 2026-09-30 
2025-06-30 -> no investor report for 2025-06-30; reports run from 2025-07-31 to 2026-09-30 
broken notes -> reconciliation failed: notes - PDL = pool 
agent tools used: draft_investor_commentary 
status: needs_review | flags: investor commentary: approval required 
```

- `stop()` plays the role of Python’s `ValueError`: `run_tool()` of `aie_r/tools.R` turns it into `{"error": ...}` for the model.
- `I(unsupported)` keeps an empty vector as an empty JSON list (`[]`) instead of dropping it.
- Section 2 breaks the gate differently from the Python script: it replaces `month_figures()` by a version that adds £100 to the Class A closing balance, because the R function reads its file paths inside the function.

**More mistakes to avoid.**

- Returning the commentary without its figures: the agent’s answer is flagged for six correct figures, and the analyst learns to ignore the flags.
- Adding the tool to the shipped assistant before the evaluation set has a case for it. Add a case (*“Draft the commentary for March 2026”*, expected tool `draft_investor_commentary`) first, then the tool.

**More trade-offs.** The agent now repeats a workflow that the application of Chapter 23 already runs on its Investor report tab. Two doors to one workflow are acceptable while both call the same function. They become a risk on the day someone changes one door and not the other, so keep the function in one place, `aie/investor_report.py`, and give both doors the same test.

### Exercise 21.5

**What the question asks.** Write the *Known limitations* section of the SF agent’s model card.

**The plan.** List what the evidence shows the agent cannot do or does unreliably: scope, data period, figures, evaluation size, model errors, guards. One fact per bullet.

**Step by step.** **Known limitations: SF agent (system prompt `b7e2474c23`).**

- Answers only about Larkfield 2025-1, from the prospectus excerpt and the data for month-ends from 30 June 2025 to 30 September 2026.
- Figures come from five tools (`pool_summary`, `note_balance`, `waterfall_summary`, `arrears_buckets`, `search_prospectus`); questions needing figures no tool provides (CPR, shares of totals, Exercise 21.2) end in `needs_review` or a statement that the figure is unavailable.
- The evaluation set has twelve cases; the interval around the pass rate is wide, and results are reported with it.
- Small local models confuse adjacent months and occasionally omit citations; both are caught by the checks, which raise the share of answers needing review.
- Scope and advice guards are keyword-based; they are tested (nine guard tests), but unusual phrasings can pass them. Answers are reviewed before any client receives them.

**Reading the result.** Five bullets, each a fact that a validator can check against the code, the evaluation set or the tests.

**Checking the answer.** Check each bullet against its source: the tool list in `aie/assistants.py`; the date range from `pool_summary("2026-10-31")`’s error message; the twelve rows of `evals/sf_agent_eval.csv`; the guard tests in `tests/test_assistants.py`. A bullet without a source is either removed or rewritten.

**Mistakes to avoid.**

- Writing limitations as reassurance (*“minor issues with dates”*). State the behaviour and its consequence.
- Omitting limitations already mitigated. *“Caught by the checks”* is the mitigation; the limitation still belongs on the card.

**Trade-offs.** A frank limitations section can slow approval, because it gives the validator questions to ask. It also defines what the agent may be used for, and it is the record that protects the team when a known limitation produces an error. Update it after every evaluation run.
