# 12. Structured Finance: Checking a Received Loan Tape

## Exercises

**Exercise 12.1.** Write a consistency rule that compares the original LTV (`RREC16`) with the original balance divided by the original valuation (`RREL29 / RREC17`). Choose a tolerance, run it on the received tape, and report what it flags.

**Exercise 12.2.** Write a month-on-month rule: a repayment loan (`FRXX`) whose current balance is higher than in the previous month’s tape. Run it with the August 2026 rows of the original tape as the previous month.

**Exercise 12.3.** Run `draft_email()` with Ollama, check the draft, and print the result. If the check fails, show how the application falls back to the template.

**Exercise 12.4.** Classify the twelve rules by severity: *blocking* (the waterfall cannot run until fixed), *material* (fix before the investor report), *minor* (fix in the next tape). Justify three of your choices.

**Exercise 12.5.** A colleague suggests asking the model, for each flagged loan, *“is this a real problem?”* and dropping the flags it says are not. Give your opinion.

## Corrections

### Exercise 12.1

**What the question asks.** Write a rule that checks three fields against each other: the original LTV (`RREC16`) must equal the original balance (`RREL29`) divided by the original valuation (`RREC17`). Choose a tolerance, run the rule on the received tape, and explain what it flags.

**The plan.** (1) Write the identity and decide how far apart the two sides may be. (2) Add the rule in Python and R. (3) Run it on the received tape. (4) Read each flagged loan, then measure the rule against the injected errors.

**Step by step.**

*Step 1 — The tolerance.* If the fields agree, $100 \times \text{RREL29} / \text{RREC17} = \text{RREC16}$ up to rounding. On the received tape the median difference is 0.007 points and the 75th percentile 0.012: the tape rounds the inputs, not the logic. A tolerance of 0.5 points is forty times the usual gap and still far below any real error.

*Step 2 — The rule.*

``` python
RULES["ltv_inconsistent"] = (
    "Original LTV (RREC16) disagrees with original balance / original "
    "valuation (RREL29 / RREC17) by more than 0.5 points",
    lambda t, d: (100 * t["RREL29"] / t["RREC17"] - t["RREC16"]).abs() > 0.5)
```

- A rule is a description (used in the servicer email) and a function of the tape `t` and the cut-off date `d` returning `True` for each breaching row.
- `.abs() > 0.5` flags a gap in either direction.

``` r
dq_rules$ltv_inconsistent <- list(
  "Original LTV (RREC16) disagrees with original balance / original valuation (RREL29 / RREC17) by more than 0.5 points",
  function(t, d) abs(100 * t$RREL29 / t$RREC17 - t$RREC16) > 0.5)
```

**Reading the result.** Two loans:

**What you should see**

``` text
     RREL2     RREL29    RREC17  RREC16
LMF25-01890  1679000.0  260000.0   64.59
LMF25-01941   136900.0  277000.0   98.50
```

`LMF25-01890` is the typo the twelve rules missed: £1,679,000 on a £260,000 property is an LTV of 646%, against 64.59% recorded. `LMF25-01941` is the loan whose original LTV was changed to 98.5%: its balance and valuation give 49.4%. The rule finds both, whichever field was mistyped.

**Checking the answer.** Measure the rule against `injected_errors.json`, as `ch12_dq_check.py` does. If the rule is named `original_balance_typo` (the name used in the truth file), the results become 13 true positives, 1 false positive, 0 false negatives: recall 13/13, precision 13/14. The “false positive” is `LMF25-01941`, recorded in the truth under `original_ltv_above_95`: a second, valid view of an error already flagged, not a false alarm in substance.

**Mistakes to avoid.**

- A tolerance of zero: rounding in the source fields would flag hundreds of correct loans.
- Writing the rule as `RREL29 / RREC17 > RREC16 / 100` (one direction only): an LTV recorded too high would pass.

**Trade-offs.** Consistency rules catch errors whatever field is wrong, but they do not say *which* field. The query to the servicer must therefore name all three fields and their values, and let the servicer say which is wrong. Field-level rules (*original LTV above 95%*) point to the field but miss errors that keep each field plausible on its own; use both kinds.

### Exercise 12.2

**What the question asks.** Write a rule that compares each loan with the previous month: a repayment loan (`RREL35 = FRXX`) whose balance rose since August 2026. Run it with the August rows of the original tape as the previous month.

**The plan.** (1) Load the August balances. (2) Join them to the received tape by loan identifier. (3) Keep repayment loans whose balance rose by more than £1. (4) Explain why the rule adds something to the existing ones.

**Step by step.**

``` python
prev = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
prev = prev[prev["RREL6"] == "2026-08-31"][["RREL2", "RREL30"]]
m = tape.merge(prev, on="RREL2", how="left", suffixes=("", "_prev"))
rose = m[(m["RREL35"] == "FRXX") & (m["RREL30"] > m["RREL30_prev"] + 1)]
print(rose[["RREL2", "RREL30", "RREL30_prev", "RREL69"]])
```

- `prev` keeps each loan’s identifier and current balance at 31 August 2026.
- `merge(..., how="left")` keeps every loan of the received tape and adds its August balance as `RREL30_prev`; `suffixes` names the second balance column.
- `RREL35 == "FRXX"` selects repayment loans (1,493 of 1,695 rows; the 202 others are interest-only, `BLLT`).
- `+ 1` is a £1 tolerance for rounding.

In R:

``` r
prev <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
prev <- prev[prev$RREL6 == "2026-08-31", c("RREL2", "RREL30")]
names(prev)[2] <- "RREL30_prev"
m <- merge(tape, prev, by = "RREL2", all.x = TRUE)
print(m[m$RREL35 == "FRXX" & !is.na(m$RREL30_prev) & m$RREL30 > m$RREL30_prev + 1,
        c("RREL2", "RREL30", "RREL30_prev", "RREL69")])
```

**Reading the result.** One loan: `LMF25-00766`, £311,985.00 in September against £201,738.57 in August, status `PERF`.

**Checking the answer.** `LMF25-00766` is the loan whose balance was set to 1.35 times its original in the injected errors, already flagged by `balance_above_original`. The new rule agrees with an existing one on the one real case, and flags nothing else among 1,493 repayment loans.

**Mistakes to avoid.**

- An inner join: loans new to the tape would disappear silently. With the left join they have no previous balance, and the comparison is false for them, which is correct.
- Applying the rule to interest-only loans: their balance stays flat, but a capitalised arrangement fee could raise it legitimately.

**Trade-offs.** The month-on-month rule catches increases that stay below 110% of the original balance, which `balance_above_original` cannot see: a repayment balance rising by £5,000 is impossible without a further advance, and further advances are not allowed in this pool. Its cost is a dependency on the previous tape. Some servicing systems capitalise arrears, which raises the balance legitimately: check the servicer’s practice and add a documented exception if needed.

### Exercise 12.3

**What the question asks.** Ask your model to draft the servicer query email, check the draft, and show how the application falls back to the template when the check fails.

**The plan.** (1) Run the rules. (2) Draft with the model. (3) Check the draft. (4) Use it if it passes, the template otherwise. (5) Force a failure to see the fallback.

**Step by step.**

``` python
found = run_rules(tape, "2026-09-30")
draft, version = draft_email(found, "30 September 2026", "7 October 2026")
problems = check_email(draft, found)
email = draft if not problems else template_email(
    found, "30 September 2026", "7 October 2026")
print(problems or "draft accepted")
print(email)
```

- `draft_email()` fills the versioned prompt with the list of issues and calls the model at temperature 0.2, for natural wording.
- `check_email()` compares the loan identifiers written in the email with the flagged loans: none missing, none extra, none repeated.
- The conditional expression keeps the draft only if the list of problems is empty.

**Reading the result.** With twelve loans, a clean draft is common, and the script prints *draft accepted*. With a small model, the most frequent problems are a loan left out of the list and an identifier mis-copied.

**Checking the answer.** Force the failure path: in the template email, replace `LMF25-00766` by `LMF25-00767` and check it:

``` text
['loan LMF25-00767 is not in the issue list', 'loan LMF25-00766 is missing from the email']
```

Both errors of a mis-copied identifier are reported. And the template itself always passes: `check_email(template_email(...), found)` returns `[]`.

**Mistakes to avoid.**

- Sending the draft and logging the problems afterwards. The check must run before the email leaves.
- Hiding the fallback. Log every fallback with the prompt version: a rising fallback rate is the first sign that a model or prompt change went wrong.

**Trade-offs.** The analyst always receives an email that lists exactly the flagged loans; the only difference between draft and template is style. A further step removes the risk entirely: ask the model to write only the opening and closing paragraphs, and insert the list of issues in code between them. The identifiers are then never written by the model, and the check passes by construction, at the price of an email whose list is less fluent.

### Exercise 12.4

**What the question asks.** Classify the twelve rules as *blocking* (the waterfall cannot run), *material* (fix before the investor report) or *minor* (fix in the next tape), and justify three choices.

**The plan.** (1) For each rule, ask what the error breaks: the cash calculation, a reported figure, or neither. (2) Classify. (3) Justify the cases that are not obvious. (4) Put the severity to work in the code.

**Step by step.** A rule is blocking if the error changes the amounts the waterfall pays; material if it changes a figure in the investor report but not the cash; minor otherwise.

| Severity | Rules                                                                                                                                                     |
|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Blocking | `negative_balance`, `balance_above_original`, `wrong_cutoff_date`, `duplicate_loan`                                                                       |
| Material | `default_without_180_days`, `arrears_without_balance`, `performing_with_days_in_arrears`, `rate_out_of_range`, `ltv_implausible`, `original_ltv_above_95` |
| Minor    | `maturity_before_origination`, `missing_region`                                                                                                           |

**Reading the result.** Three justifications:

- `duplicate_loan` is blocking: a duplicated loan is counted twice in the pool balance, so notes, PDL and pool no longer reconcile (Exercise 1.6) and the waterfall cannot be trusted.
- `default_without_180_days` is material: the default status drives the PDL debit, and the prospectus defines default precisely; but the cash collected is unaffected, so the waterfall can run once the status is confirmed.
- `missing_region` is minor for this month’s payments (no cash flow depends on it), but it matters for the stratification tables and regulatory reporting, so it is still queried.

**Checking the answer.** Test the blocking rules against the definition by computing the received tape’s pool balance at 30 September 2026: it is £806,704.49 below the £322,717,766.58 that the notes and the PDL require. The gap is exactly the sum of the four blocking errors: the sign flip of `LMF25-01521` (−£829,538.46), the inflated balance of `LMF25-00766` (+£110,569.04), the duplicated row of `LMF25-01629` (+£143,783.89), and the row of `LMF25-00778` dated 31 August, which drops out of the September pool (−£231,518.96). Correcting the region or the maturity date changes nothing in it. The classification follows from an observable effect, not from opinion.

**Mistakes to avoid.**

- Making everything blocking “to be safe”. The waterfall then never runs on time, and the team learns to override the block.
- Classifying by how surprising the error looks. A missing region looks careless and is minor; a default two weeks early looks small and moves money between noteholders.

**Trade-offs.** Severity changes what happens next, so it belongs in the code: add it to each rule’s definition, sort the servicer email by severity, and block the waterfall run while any blocking flag is open. Other teams may draw the line differently (some treat `rate_out_of_range` as blocking, because the interest collected depends on it); write the classification down and have the head of cash management approve it.

### Exercise 12.5

**What the question asks.** Give an opinion on asking the model, for each flagged loan, whether it is a real problem, and dropping the flags it rejects.

**The plan.** (1) State what a flag is. (2) Ask what the model’s opinion adds and what it can remove. (3) Propose what to do instead.

**Step by step.** Each flag is the result of a rule with a written reason: the balance is negative, the status contradicts the days in arrears. The model’s opinion that it is *“not a real problem”* adds no information about the loan; the model has not seen the servicer’s system, and it can only remove flags.

**Reading the result.** Opinion: **no**. A removed true flag is a missed error, a false negative, which this chapter measured as the more costly kind: a wrong figure in an investor report, or a waterfall run on wrong data.

**Checking the answer.** Measure the proposal before rejecting it on principle: on the received tape, each of the 12 flags is a true error (precision 100%). Any flag the model drops lowers recall and cannot raise precision, which is already perfect. On this data, the proposal can only make the check worse.

**Mistakes to avoid.**

- Accepting it because the model’s explanations sound reasonable. A fluent explanation is not evidence about a loan.
- Rejecting the colleague’s underlying concern. If analysts spend time on false flags, that is a real cost.

**Trade-offs.** If a rule produces many false positives, fix the rule (a tolerance, a documented exception) and measure precision again. Where judgement is needed, it belongs to the analyst, who can see the row, the rule and the loan’s history. The model can help the analyst by summarising the loan’s last six months from the tape, a writing task, with the figures checked as in Chapter 6: it speeds up the judgement without making it.
