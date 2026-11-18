# 1. What an AI Engineer Does

## Exercises

**Exercise 1.1.** In Python and in R, count the Larkfield loans by account status (`RREL69`) at 30 September 2026. Use the data dictionary to give the meaning of each status.

**Exercise 1.2.** Compute the arrears ratio of the Larkfield pool at 30 September 2026: the current balance of loans with status `ARRE`, divided by the total pool balance.

**Exercise 1.3.** Compute the one-year return of the Harbourline Euro Corporate Bond Fund (HECB) and of its benchmark to 30 September 2026, from the NAV and benchmark files. Compare the relative return with the factsheet in `data/am/documents/hecb_factsheet_2026_09.md`.

**Exercise 1.4.** For each task below, use Figure 1.3 to decide whether it calls for plain code, a model with automatic checks, or a model whose draft a person approves. Justify each answer in one sentence.

\(a\) Computing the Class B interest due on the next interest payment date.

\(b\) Answering an investor’s email asking how the Larkfield reserve fund can be used.

\(c\) Extracting the ongoing charges figure from each of 400 Key Information Documents into a table.

\(d\) Writing the manager’s commentary for the HGEF factsheet.

\(e\) Deciding whether a loan meets the eligibility criteria of the prospectus, given its fields in the tape.

\(f\) Replying to a regulator’s request for information about the fund’s sustainability characteristics.

**Exercise 1.5.** Section 4 of the Larkfield prospectus excerpt (`data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md`) defines a *Defaulted Loan*. Find the definition, then check in the tape that every row with status `DFLT` respects it.

**Exercise 1.6.** Extend the applied example: reconcile notes, PDL and pool for **every** month in the tape, not only September 2026. Report the largest absolute difference.

## Corrections

### Exercise 1.1

**What the question asks.** How many Larkfield loans are in each account status on the last cut-off date, 30 September 2026, and what each status code means. The aim is to read a regulatory loan tape for the first time: one row per loan per month, coded fields.

**The plan.** (1) Read the tape. (2) Keep the rows of 30 September 2026 only. (3) Count the values of the status field `RREL69`. (4) Look up each code in `docs/data_dictionary.md`.

**Step by step.**

**Python**

`chapters/ch01/python/solutions/ex1_1_status_counts.py`

``` python
import pandas as pd

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep = tape[tape["RREL6"] == "2026-09-30"]
print(sep["RREL69"].value_counts())
```

- `import pandas as pd` loads pandas under its usual short name.
- `pd.read_csv(...)` reads the whole tape: sixteen monthly cut-offs, one row per loan still in the pool at each.
- `tape["RREL6"] == "2026-09-30"` compares the cut-off date field with the date, row by row, and gives a column of `True`/`False`; `tape[...]` keeps the `True` rows. The date is compared as text, which works because the file writes dates as `YYYY-MM-DD`.
- `sep["RREL69"].value_counts()` counts each distinct value and sorts the counts from largest to smallest.

**R**

`chapters/ch01/r/solutions/ex1_1_status_counts.R`

``` r
tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep  <- tape[tape$RREL6 == "2026-09-30", ]
print(sort(table(sep$RREL69), decreasing = TRUE))
```

- `tape[condition, ]` keeps the rows where the condition is `TRUE`; the empty place after the comma keeps every column.
- `table()` counts each value; `sort(..., decreasing = TRUE)` orders the counts as pandas does.

**Reading the result.**

**What you should see**

``` text
PERF    1621
RNAR      21
REDM      20
ARRE      18
DFLT      14
```

From the data dictionary: `PERF` performing; `RNAR` restructured, no arrears (the borrower fell behind, then caught up under an arrangement); `REDM` redeemed in full during September, so these loans disappear from the October tape; `ARRE` in arrears; `DFLT` defaulted. 96% of the loans in the tape (1,621 of 1,694) are performing.

**Checking the answer.** The counts add up to 1,621 + 21 + 20 + 18 + 14 = 1,694. The pool had 2,000 loans at closing, so 306 must have left before September. Count them independently: the loans with status `REDM` in any tape before 30 September 2026 number exactly 306. The two numbers agree, so no row is missing or duplicated. A second check: `sep["RREL2"].nunique()` (or `length(unique(sep$RREL2))`) also gives 1,694, so each loan appears once at this date.

**Mistakes to avoid.**

- Counting the whole tape without filtering on the date. You then count each loan once per month, and `PERF` exceeds 25,000.
- Assuming that 2,000 loans are still in the pool. A redeemed loan leaves the tape the month after its `REDM` row.
- Reading `RNAR` as a bad status. It is a loan that was in difficulty and is now up to date; investors watch it because restructured loans fall back into arrears more often than others.

**Trade-offs.** Filtering by a text comparison of dates is simple and exact here. If the file mixed date formats (`30/09/2026` and `2026-09-30`), the comparison would miss rows silently; converting the column with `pd.to_datetime()` or `as.Date()` first costs one line and protects you. Chapter 12 checks date formats as part of data quality.

### Exercise 1.2

**What the question asks.** The arrears ratio at 30 September 2026: the current balance of loans in arrears divided by the current balance of the whole pool. It is the first figure an RMBS investor reads in a monthly report.

**The plan.** (1) Keep the September rows. (2) Sum the current balance `RREL30` of rows with status `ARRE`. (3) Sum `RREL30` over all rows. (4) Divide.

**Step by step.**

**Python**

`chapters/ch01/python/solutions/ex1_2_arrears_ratio.py`

``` python
import pandas as pd

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep = tape[tape["RREL6"] == "2026-09-30"]
arrears = sep.loc[sep["RREL69"] == "ARRE", "RREL30"].sum()
pool = sep["RREL30"].sum()
print(f"Balance in arrears: GBP {arrears:,.2f}")
print(f"Pool balance:       GBP {pool:,.2f}")
print(f"Arrears ratio:      {arrears / pool:.2%}")
```

- `sep.loc[rows, column]` selects at once the rows where the status is `ARRE` and the column `RREL30`; `.sum()` adds them.
- `sep["RREL30"].sum()` adds the current balance of every loan at the date: the pool balance.
- In the f-strings, `:,.2f` prints a number with thousands separators and two decimals; `:.2%` multiplies by 100 and adds the percent sign.

**R**

`chapters/ch01/r/solutions/ex1_2_arrears_ratio.R`

``` r
tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep  <- tape[tape$RREL6 == "2026-09-30", ]
arrears <- sum(sep$RREL30[sep$RREL69 == "ARRE"])
pool    <- sum(sep$RREL30)
cat(sprintf("Balance in arrears: GBP %s\n",
            format(arrears, big.mark = ",", nsmall = 2)))
cat(sprintf("Pool balance:       GBP %s\n",
            format(pool, big.mark = ",", nsmall = 2)))
cat(sprintf("Arrears ratio:      %.2f%%\n", 100 * arrears / pool))
```

- `sep$RREL30[sep$RREL69 == "ARRE"]` keeps the balances whose status is `ARRE`; `sum()` adds them.
- `format(x, big.mark = ",", nsmall = 2)` prints thousands separators and at least two decimals.
- In `sprintf`, `%.2f` prints two decimals and `%%` prints a literal percent sign.

**Reading the result.**

**What you should see**

``` text
Balance in arrears: GBP 2,721,210.68
Pool balance:       GBP 322,717,766.58
Arrears ratio:      0.84%
```

Eighteen loans in arrears (Exercise 1.1) carry £2.72 million out of £322.72 million: 0.84% of the pool.

**Checking the answer.** Three checks. (1) By hand: 2,721,210.68 / 322,717,766.58 = 0.00843, which is 0.84%. (2) Against the pool total of the applied example, which reconciled the pool with the notes: same £322,717,766.58. (3) Against Chapter 14, where `month_figures("2026-09-30")` computes the same ratio for the investor report: 0.84%.

**Mistakes to avoid.**

- Counting loans instead of balances. 18 loans out of 1,694 is 1.06%, a different measure; reports use balances because a large loan in arrears matters more than a small one.
- Including `DFLT` loans in the numerator. Defaulted loans carry a current balance of zero in this tape (the loss has been recognised), so here they would add nothing; in other tapes they keep a balance and the ratio’s definition must say whether they count.
- Dividing by the balance at closing instead of the current pool balance.

**Trade-offs.** One ratio is easy to read but hides how far behind the borrowers are: a loan one month behind and a loan five months behind weigh the same. Investor reports therefore add a table by arrears bucket, built from days in arrears `RREL68`; Chapter 14 builds it. A precise definition, written in the report, matters more than the choice of definition.

### Exercise 1.3

**What the question asks.** The one-year return of HECB and of its benchmark to 30 September 2026, their difference, and whether it matches the factsheet.

**The plan.** (1) Take the last twelve monthly returns of the fund and of the benchmark. (2) Compound each: multiply the twelve values of (1 + monthly return) and subtract 1. (3) Subtract benchmark from fund. (4) Compare with the factsheet’s 1-year line.

**Step by step.**

**Python**

`chapters/ch01/python/solutions/ex1_3_hecb_one_year.py`

``` python
import pandas as pd

nav = pd.read_csv("data/am/fund_nav_monthly.csv")
bm = pd.read_csv("data/am/benchmark_returns_monthly.csv")

fund = nav[nav["fund_code"] == "HECB"].tail(12)["net_return"]
bench = bm.tail(12)["HECB"]
fund_1y = (1 + fund).prod() - 1
bench_1y = (1 + bench).prod() - 1
print(f"Fund 1 year:      {fund_1y:.2%}")
print(f"Benchmark 1 year: {bench_1y:.2%}")
print(f"Relative:         {fund_1y - bench_1y:+.2%}")
print(f"Relative from the rounded figures: "
      f"{round(fund_1y * 100, 2) - round(bench_1y * 100, 2):+.2f}%")
```

- `nav[nav["fund_code"] == "HECB"]` keeps HECB’s rows; `.tail(12)` keeps the last twelve, which are the months from October 2025 to September 2026 because the file is sorted by date.
- `bm.tail(12)["HECB"]` takes the same twelve months from the benchmark file, whose columns are named after the funds.
- `(1 + fund).prod() - 1` compounds: each month’s growth factor multiplied by the next.
- `:+.2%` prints the sign even when the number is positive.
- The last line subtracts the two figures *after* rounding them to two decimals, as a reader with a calculator would.

**R**

`chapters/ch01/r/solutions/ex1_3_hecb_one_year.R`

``` r
nav <- read.csv("data/am/fund_nav_monthly.csv")
bm  <- read.csv("data/am/benchmark_returns_monthly.csv")

fund  <- tail(nav$net_return[nav$fund_code == "HECB"], 12)
bench <- tail(bm$HECB, 12)
fund_1y  <- prod(1 + fund) - 1
bench_1y <- prod(1 + bench) - 1
cat(sprintf("Fund 1 year:      %.2f%%\n", 100 * fund_1y))
cat(sprintf("Benchmark 1 year: %.2f%%\n", 100 * bench_1y))
cat(sprintf("Relative:         %+.2f%%\n", 100 * (fund_1y - bench_1y)))
cat(sprintf("Relative from the rounded figures: %+.2f%%\n",
            round(100 * fund_1y, 2) - round(100 * bench_1y, 2)))
```

- `tail(x, 12)` keeps the last twelve values; `prod()` multiplies them.
- `%+.2f` prints the sign, as `:+.2%` does in Python.

**Reading the result.**

**What you should see**

``` text
Fund 1 year:      3.17%
Benchmark 1 year: 3.66%
Relative:         -0.48%
Relative from the rounded figures: -0.49%
```

The fund returned 3.17% net of fees, the benchmark 3.66%, so the fund was 0.48 percentage points behind. The factsheet’s 1-year line reads *3.17% \| 3.66% \| −0.48%*: the computation matches it exactly.

**Checking the answer.** (1) Confirm the period: the first and last dates of the twelve rows are 2025-10-31 and 2026-09-30, in both files. (2) Compute the fund’s return a second way, from prices: the NAV per share went from 105.8426 at 30 September 2025 to 109.2008 at 30 September 2026, and 109.2008 / 105.8426 − 1 = 3.17%. Compounded monthly returns and the ratio of prices agree, as they must for a fund that does not distribute.

**Mistakes to avoid.**

- **Adding the twelve returns instead of compounding.** The sum is 3.21%, four basis points too high: returns earned in one month earn returns in the following months.
- **Subtracting rounded figures.** 3.17 − 3.66 = −0.49, one basis point away from the factsheet. When a model later writes *“lagged by 0.49%”*, the figure looks derived from the data and is still wrong. Chapter 6’s checker compares figures at the precision they are written to catch exactly this.
- Taking `tail(12)` of the NAV file without filtering on the fund: you would get the last twelve rows of the file, which mix funds.

**Trade-offs.** `tail(12)` relies on the file being sorted by date and complete. It is short and correct here; selecting the months by date (`month_end > "2025-09-30"`) is longer but survives a file in another order. In production code, select by date.

### Exercise 1.4

**What the question asks.** For six everyday tasks, choose among plain code, a model with automatic checks, and a model whose draft a person approves, using Figure 1.3.

**The plan.** For each task ask two questions from the figure: *Is the input structured data and the answer a calculation?* If yes, code. If not, *can every figure and fact in the output be checked automatically, and does the output commit the firm?* The answers place the task.

**Step by step.** Take the tasks in order and place each one.

\(a\) **Plain code.** The interest is the Class B balance × the coupon × the day-count fraction: a formula on structured data. A model would add cost and a chance of error, and nothing else.

\(b\) **Model with automatic checks.** The question is in words and the answer is in a document (Section 3 of the prospectus). Retrieval finds the clause, the model writes the answer, and checks confirm that each cited clause exists and each figure (1.50%, £6,082,667.80) appears in it. Chapter 10 builds this. Because the email leaves the firm, many firms also require a person’s approval; the checks make that approval quick.

\(c\) **Model with automatic checks.** Finding a figure in 400 documents of different layouts is a reading task; whether the extracted value appears in the document’s cost table and lies in a plausible range is a code task. Chapter 15 does this for KIDs.

\(d\) **Model drafts, a person approves.** The figures in a commentary can be checked against the attribution file (Chapter 13), but the commentary also contains explanations (*why* the real estate underweight detracted) that the portfolio manager must own.

\(e\) **Plain code.** Each eligibility criterion is a rule on fields: *original LTV at most 95%* is `RREC16 <= 95`. The criteria were read once from the prospectus; from then on they are code.

\(f\) **Model drafts, a person approves.** A reply to a regulator is a formal statement of the firm; the model can assemble a draft from the SFDR disclosure and the ESG data; a named person signs it.

**Reading the result.**

| Task                                     | Approach               | Deciding reason                                                  |
|:-----------------------------------------|:-----------------------|:-----------------------------------------------------------------|
| \(a\) Class B interest                   | plain code             | a formula on structured data                                     |
| \(b\) investor email on the reserve fund | model with checks      | the answer is in a document; citations and figures are checkable |
| \(c\) ongoing charges from 400 KIDs      | model with checks      | reading varied layouts; each value checkable in its document     |
| \(d\) HGEF factsheet commentary          | model, person approves | explanations the portfolio manager must own                      |
| \(e\) loan eligibility                   | plain code             | each criterion is a rule on fields                               |
| \(f\) reply to a regulator               | model, person approves | a formal statement of the firm                                   |

Two tasks need no model at all, two use a model under automatic checks, and two need a person’s signature. The deciding question is never *“can a model do it?”* but *“can its output be checked, and who answers for it?”*.

**Checking the answer.** Apply the test in reverse: for each answer, imagine the alternative fails. If (a) used a model and the model wrote a wrong figure, an investor is paid the wrong interest: unacceptable for a task code does perfectly. If (f) were sent with automatic checks only, a statement nobody approved would reach a regulator: unacceptable whatever the checks. The reverse test confirms each choice.

**Mistakes to avoid.**

- Using a model for (e) because the criteria are written in English in the prospectus. The *reading* is a one-off; the *checking* runs on 2,000 loans every month and must be exact.
- Treating (c) as code because the KIDs are regulated documents. Their content is standardised; their layout is not.

**Trade-offs.** The boundary between (b) and (d) depends on the firm’s appetite for risk. An investor-relations team answering fifty emails a week may accept checked answers with sampling; a firm after a complaint will put a person on every one. The figure gives the starting point; the firm’s policy decides.

### Exercise 1.5

**What the question asks.** Find the prospectus’s definition of a Defaulted Loan, turn it into a rule, and check that every `DFLT` row in the tape satisfies it.

**The plan.** (1) Read Section 4 of the prospectus excerpt. (2) Translate the definition into a condition on a tape field. (3) Keep the `DFLT` rows. (4) Count the rows that break the condition.

**Step by step.** Section 4 states: *a loan becomes a Defaulted Loan when six or more monthly payments are due and unpaid*. The tape reports days in arrears in `RREL68`, counted at 30 days per month, so the rule is `RREL68 >= 180`.

**Python**

`chapters/ch01/python/solutions/ex1_5_default_rule.py`

``` python
import pandas as pd

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
defaulted = tape[tape["RREL69"] == "DFLT"]
print("Rows with status DFLT:       ", len(defaulted))
print("Distinct defaulted loans:    ", defaulted["RREL2"].nunique())
print("Minimum days in arrears:     ", defaulted["RREL68"].min())
print("Rows breaking the rule:      ", (defaulted["RREL68"] < 180).sum())
```

- `defaulted` keeps every `DFLT` row in **all** months, not only September: the rule must hold every month.
- `defaulted["RREL2"].nunique()` counts distinct loan identifiers.
- `(defaulted["RREL68"] < 180)` is `True` for each row that breaks the rule; `.sum()` counts the `True` values, because Python counts `True` as 1.

**R**

`chapters/ch01/r/solutions/ex1_5_default_rule.R`

``` r
tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
defaulted <- tape[tape$RREL69 == "DFLT", ]
cat("Rows with status DFLT:       ", nrow(defaulted), "\n")
cat("Distinct defaulted loans:    ", length(unique(defaulted$RREL2)), "\n")
cat("Minimum days in arrears:     ", min(defaulted$RREL68), "\n")
cat("Rows breaking the rule:      ", sum(defaulted$RREL68 < 180), "\n")
```

- `length(unique(x))` is R’s count of distinct values; `sum()` of a logical vector counts the `TRUE` values.

**Reading the result.**

**What you should see**

``` text
Rows with status DFLT:        87
Distinct defaulted loans:     14
Minimum days in arrears:      180
Rows breaking the rule:       0
```

No row breaks the rule. The minimum of 180 days shows that the servicer flags a loan as defaulted exactly when it reaches six months, not later.

**Checking the answer.** (1) The 14 distinct defaulted loans equal the 14 `DFLT` rows of September in Exercise 1.1: a defaulted loan stays in every later tape, so all defaults to date appear in September. (2) The 87 rows are the same 14 loans repeated over the months after each default. (3) Test the rule’s other direction with one more line: `tape[(tape.RREL68 >= 180) & (tape.RREL69 != "DFLT")]` must be empty, otherwise a loan meets the definition but was not flagged. It is empty.

**Mistakes to avoid.**

- Checking only one direction. *Every `DFLT` has ≥ 180 days* does not prove *every loan with ≥ 180 days is `DFLT`*; the check in step (3) does.
- Translating *six monthly payments* as `RREL68 > 180`. *Six or more* means *at least* 180 days: `>=`.
- Counting rows (87) as defaults. Investors count loans (14) and balances.

**Trade-offs.** Converting months to days at 30 days per month follows the tape’s convention; a servicer counting calendar days would report 181 or 184 days for six months. Write the convention next to the rule. This exercise is a small version of Chapter 12: **reading the rule is a language task, checking it is a code task**.

### Exercise 1.6

**What the question asks.** Repeat the applied example’s reconciliation (notes outstanding minus the principal deficiency ledger equal the pool balance) for every one of the sixteen months, and report the largest difference.

**The plan.** (1) Sum the pool balance by cut-off date. (2) Sum the notes’ closing balances by date. (3) Sum the PDL balances by date. (4) Compute notes − PDL − pool for each date and take the largest absolute value.

**Step by step.**

**Python**

`chapters/ch01/python/solutions/ex1_6_reconcile_all_months.py`

``` python
import pandas as pd

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
notes = pd.read_csv("data/sf/rmbs/larkfield_2025_1_notes.csv")

pool = tape.groupby("RREL6")["RREL30"].sum()
notes_out = notes.groupby("cutoff")["closing"].sum()
pdl = notes.groupby("cutoff")["pdl_balance"].sum()

check = (notes_out - pdl - pool).round(2)
print(check.to_string())
print("Largest absolute difference:", check.abs().max())
```

- `tape.groupby("RREL6")["RREL30"].sum()` gives one total per cut-off date: a series indexed by date.
- The notes file has one row per class (A to D) per date; `groupby("cutoff")` adds the four classes.
- `notes_out - pdl - pool` subtracts series **by matching their index**: pandas lines up the dates, whatever their order.
- `.round(2)` removes floating-point dust such as 1e-8; `.abs().max()` gives the largest difference.

**R**

`chapters/ch01/r/solutions/ex1_6_reconcile_all_months.R`

``` r
tape  <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
notes <- read.csv("data/sf/rmbs/larkfield_2025_1_notes.csv")

pool      <- tapply(tape$RREL30, tape$RREL6, sum)
notes_out <- tapply(notes$closing, notes$cutoff, sum)
pdl       <- tapply(notes$pdl_balance, notes$cutoff, sum)

check <- round(notes_out - pdl - pool, 2)
print(check)
cat("Largest absolute difference:", max(abs(check)), "\n")
```

- `tapply(values, groups, sum)` is R’s group-by: one sum per date, named by the date and sorted.
- `notes_out - pdl - pool` subtracts **by position**, not by name. It works here because all three vectors contain the same sixteen dates in the same sorted order.

**Reading the result.** The sixteen differences are all 0.00, and the script ends with:

**What you should see**

``` text
Largest absolute difference: 0.0
```

R prints `0`. In every month, the notes outstanding less the losses not yet covered equal the loans that back them: the deal’s balance sheet holds from closing to September 2026.

**Checking the answer.** Make the check fail on purpose, to prove it can. Change one balance in a copy of the tape (`tape.loc[0, "RREL30"] += 100`) and run again: the month of that row shows −100.00 and every other month 0.00. A check that has never failed has not been tested.

**Mistakes to avoid.**

- **Relying on positional alignment when a month is missing.** Drop one month from the notes and the two languages behave differently. Pandas aligns by date and returns `NaN` for the missing month: visible. R subtracts a 15-value vector from a 16-value vector by position, warns *longer object length is not a multiple of shorter object length*, and returns differences between **different months**: wrong numbers, with only a warning. In R, align by name first: `pool[names(notes_out)]`.
- Forgetting the PDL. Without it the reconciliation fails in the three months where the PDL carried a balance (December 2025, January 2026 and April 2026), and you might “fix” a correct deal.

**Trade-offs.** Group-by and subtract is three lines and enough when the sources are complete. A join on the date (Chapter 12) is longer but makes missing months explicit, as rows with an empty side; for a check that runs unattended every month, prefer the join.
