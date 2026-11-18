# 16. Structured Finance: Reading Servicer Reports in PDF

## Exercises

**Exercise 16.1.** Extract the text of the September report in Python and in R. Print the line or lines containing *Prepayments* in each. Explain why a regular expression written for one output would fail on the other.

**Exercise 16.2.** Run `extract_report()` with Ollama on the three reports and reconcile each. How many fields were extracted correctly?

**Exercise 16.3.** The September discrepancy is £12,000.00. Using the tape and the cash flows, list the redemptions of September and propose how the servicer may have reached its figure. What would you write to the servicer?

**Exercise 16.4.** Add a third check that needs no loan data: the report’s own arithmetic. Which identities can you check inside the September report alone?

**Exercise 16.5.** Write the rule the production follows when `reconcile_report()` finds a reporting discrepancy above a tolerance. Who is informed, what is blocked, and what is logged?

## Corrections

### Exercise 16.1

**What the question asks.** Extract the text of the September servicer report in Python and R, print the line or lines with *Prepayments*, and explain why a regular expression written for one output could fail on the other.

**The plan.** (1) Extract the text with each language’s PDF library. (2) Find *Prepayments* and print what surrounds it. (3) Compare the two layouts. (4) Test a pattern on both.

**Step by step.**

``` python
import sys; sys.path.insert(0, ".")
from aie.servicer_pdf import pdf_text

text = pdf_text("data/sf/rmbs/servicer_reports/servicer_report_2026_09.pdf")
lines = text.split("\n")
i = next(k for k, l in enumerate(lines) if "Prepayments" in l)
print(lines[i:i + 2])
```

- `pdf_text()` extracts the text of every page with `pypdf`.
- `next(...)` returns the index of the first line containing *Prepayments*; `lines[i:i + 2]` prints that line and the next.

``` r
source("aie_r/servicer_pdf.R")
lines <- strsplit(pdf_text_all(
  "data/sf/rmbs/servicer_reports/servicer_report_2026_09.pdf"), "\n")[[1]]
print(grep("Prepayments", lines, value = TRUE))
```

- `pdf_text_all()` uses the `pdftools` package (built on the Poppler library) and joins the pages.

**Reading the result.**

``` text
Python: ['Prepayments and redemptions', 'GBP 4,358,814.19']
R:      "   Prepayments and redemptions          ...          GBP 4,358,814.19"
```

Python’s library writes each table cell on its own line; Poppler keeps the row on one line, with spaces for the column gap.

**Checking the answer.** Test two patterns on both texts:

- `Prepayments and redemptions\s+GBP ([\d,.]+)` matches both, because `\s` matches spaces **and** line breaks.
- `Prepayments and redemptions +GBP ([\d,.]+)` (spaces only) matches the R text and fails on the Python text.

**Mistakes to avoid.**

- Writing a pattern against one library’s output and assuming the PDF “says” that. The PDF stores positioned characters; each library rebuilds lines its own way.
- Upgrading the PDF library without re-running the extraction tests. A new version can change line breaks.

**Trade-offs.** Rules on extracted text are fast and exact while the layout and the library stay fixed; small details of the tool decide whether they work. A model reads both layouts without change, at the cost of a model call and of the checks of this chapter. If you write rules, use `\s+` between label and value, and test on the output of each library you use.

### Exercise 16.2

**What the question asks.** Extract the three servicer reports with your model, reconcile each, and count the fields extracted correctly.

**The plan.** (1) For each month, extract with `extract_report()`. (2) Reconcile with `reconcile_report()`. (3) Count the verdicts. (4) Interpret each verdict that is not *agrees*.

**Step by step.**

``` python
for cutoff in ("2026-07-31", "2026-08-31", "2026-09-30"):
    path = ("data/sf/rmbs/servicer_reports/"
            f"servicer_report_{cutoff[:7].replace('-', '_')}.pdf")
    obj, schema_errors, version = extract_report(path)
    table = reconcile_report(obj, pdf_text(path), cutoff)
    print(cutoff, schema_errors or "schema ok")
    print(table.verdict.value_counts().to_string())
```

- `extract_report()` sends the report’s text to the model with the schema of seven fields and validates the reply.
- `reconcile_report()` checks each field twice: is the extracted value written in the report (otherwise *extraction error*), and does it agree with the figure computed from the loan data (otherwise *REPORT DISAGREES WITH LOAN DATA*)?

**Reading the result.** Three reports × seven fields = 21 checks. With a faithful extraction, 20 read *agrees* and one, September’s prepayments, reads *REPORT DISAGREES WITH LOAN DATA* (£4,358,814.19 against £4,346,814.19). Any *extraction error* is a model error to add to the evaluation set.

**Checking the answer.** Run `ch16_reconcile_reports.py`, which uses prepared extractions: August’s scheduled principal was extracted as £642,967.23, a figure absent from the report (which says £542,967.23), and the table reads *extraction error: value not in the report*. The two kinds of failure are told apart: the model misread the report in August; the servicer misreported in September.

**Mistakes to avoid.**

- Counting September’s prepayments as an extraction error. The model read the report correctly; the report is wrong.
- Comparing extraction with loan data only. Without the first check, a model error and a servicer error look the same.

**Trade-offs.** With the one-cell-per-line text, small models occasionally attach an amount to the next label (scheduled principal read as prepayments). The first check does not catch a swap, because both values are in the report. The second does: the two swapped fields disagree with the loan data in the same month, by amounts that mirror each other. A pair of discrepancies of opposite sign is the signature of a swap. Adding the label to each value in the prompt’s output format (`"label": ..., "amount": ...`) reduces swaps at the cost of a longer schema.

### Exercise 16.3

**What the question asks.** Use the tape and the cash flows to list September’s prepayments, propose how the servicer could have reached a figure £12,000.00 higher, and write the query to the servicer.

**The plan.** (1) Sum the loan-level prepayments of September. (2) Split full redemptions from partial prepayments. (3) Reason about the difference. (4) Draft the query.

**Step by step.**

``` python
cf = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_cashflows.csv")
sep = cf[(cf.cutoff == "2026-09-30") & (cf.prepayment > 0)]
print(len(sep), round(sep.prepayment.sum(), 2))

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
redeemed = tape[(tape.RREL6 == "2026-09-30") & (tape.RREL69 == "REDM")].RREL2
full = sep[sep.loan.isin(redeemed)]
print(len(full), round(full.prepayment.sum(), 2), round(sep.prepayment.sum() - full.prepayment.sum(), 2))
```

- `prepayment > 0` keeps the loans that paid more than their scheduled principal.
- The tape’s status `REDM` identifies full redemptions; the other prepayments are partial.

**Reading the result.** 50 loans prepaid in September, £4,346,814.19 in total: 20 full redemptions of £3,933,571.59 and 30 partial prepayments of £413,242.60.

**Checking the answer.** The total agrees with the loan-data figure of the reconciliation, £4,346,814.19, and the 20 full redemptions agree with the report’s own sentence *“20 loans redeemed in full during the period”*. The difference with the report is $4{,}358{,}814.19 - 4{,}346{,}814.19 = 12{,}000.00$.

**Mistakes to avoid.**

- Asking the servicer to “fix the report” without both figures. The servicer needs the figure you computed and how.
- Assuming the loan data is right. It usually is, because it is loan by loan, but the query should ask which figure is correct.

**Trade-offs.** A round difference of exactly £12,000.00 is not what rounding produces; it is typical of a partial prepayment recorded but not received (a bounced payment), a redemption statement issued but not paid, or a payment booked to the wrong deal. The query: *“Your servicer report for September 2026 states prepayments and redemptions of £4,358,814.19. The loan-level data for the same period gives £4,346,814.19 (20 full redemptions of £3,933,571.59 and 30 partial prepayments of £413,242.60). Could you identify the £12,000.00 difference and confirm which figure is correct by 5 October 2026, so that the waterfall can be finalised?”* Facts, both figures, the difference, a deadline, no accusation. The model can draft it, with the check of Chapter 12 extended to require both figures and the difference exactly.

### Exercise 16.4

**What the question asks.** Find identities that can be checked inside the September report alone (with the previous month’s report), without loan data.

**The plan.** (1) List relations between the report’s figures. (2) Compute each. (3) Interpret the one that fails.

**Step by step.** Three identities:

- **Arrears table.** The four bucket balances sum to the arrears balance: $652{,}077.10 + 1{,}088{,}476.03 + 452{,}041.82 + 528{,}615.73 = 2{,}721{,}210.68$.
- **Loans.** Last month’s loans minus loans redeemed in full minus new defaults: $1{,}680 - 20 - 0 = 1{,}660$, the number reported.
- **Pool balance.** Last month’s balance minus scheduled principal, prepayments and new defaults:

$$327{,}600{,}033.97 - 535{,}453.20 - 4{,}358{,}814.19 - 0 = 322{,}705{,}766.58$$

against £322,717,766.58 reported.

**Reading the result.** The first two identities hold. The pool identity misses by exactly £12,000.00: the report contradicts itself, since its own prepayments do not explain its own change in balance.

**Checking the answer.** Replace the reported prepayments by the loan-data figure, £4,346,814.19: $327{,}600{,}033.97 - 535{,}453.20 - 4{,}346{,}814.19 = 322{,}717{,}766.58$, exactly the reported balance. The balance is right and the prepayment figure is wrong.

**Mistakes to avoid.**

- Subtracting recoveries from the balance. Recoveries are cash received on loans already written off; they do not reduce the current balance.
- Using the August balance from the tape instead of the August report: the identity is meant to use the reports only.

**Trade-offs.** Internal identities need only the reports, so they work on deals where you receive no tape. Alone, they show that something is inconsistent but not which figure; combined with the tape check, they identify the wrong figure. They cost a few lines each, and they test the servicer’s own arithmetic, which a model-based extraction cannot do.

### Exercise 16.5

**What the question asks.** Write the rule the production follows when `reconcile_report()` finds a discrepancy above the tolerance: who is informed, what is blocked, what is logged, and who may override.

**The plan.** Define four things in order: the tolerance, the block, the people informed, the log; then the override.

**Step by step.**

1.  **Tolerance.** Differences up to £0.01 per field (rounding) are ignored; anything larger is a discrepancy.
2.  **Block.** The waterfall for the period cannot be finalised while a discrepancy on a cash field (collections, recoveries, prepayments) is open.
3.  **Inform.** The cash management analyst receives the reconciliation table; the servicer receives the query of Exercise 16.3, approved by the analyst.
4.  **Log.** The extraction, the report’s hash, the reconciliation table, the query, the servicer’s answer and the resolution are stored with the period.
5.  **Override.** Only a named person, with a recorded reason (for example, the servicer confirmed that the tape is right and will reissue the report); the override itself is logged.

**Reading the result.** For September 2026: the prepayments discrepancy of £12,000.00 blocks the waterfall, the analyst sees the table, the servicer receives the query, and everything is stored with the period.

**Checking the answer.** Walk through two months with the rule. August: the reconciliation (with a correct extraction) shows no discrepancy, so nothing is blocked. September: one cash field disagrees, so the waterfall waits. The rule gives a clear outcome in both cases, with no judgement left implicit.

**Mistakes to avoid.**

- Blocking on any field, including `loans_outstanding`: a count error does not change the cash and need not stop payments.
- An override without a named person: nobody is accountable for the decision.

**Trade-offs.** Blocking protects noteholders from payments computed on wrong figures, at the risk of a late payment date if the servicer answers slowly; the deadline in the query and the override with a recorded reason manage that risk. This is the governance of Chapter 20 applied to one control: a rule, an owner, a log.
