# 13. Asset Management: Drafting the Factsheet Commentary

> © 2026 Mohamed Miled. All rights reserved. This text is part of the book *Introduction to AI Engineering* and may not be copied, republished or sold. The code blocks are under the MIT licence (see `LICENSE`); the explanations are not (see `LICENSE-TEXT.md`).

## Exercises

**Exercise 13.1.** Verify the attribution identity for September 2026: the sum of allocation, selection and interaction over all rows equals the fund’s gross return minus the benchmark’s return. Show the computation in Python and R, including the fee adjustment.

**Exercise 13.2.** Draft 1 says *“Stock selection and sector allocation both detracted.”* There is no figure in that sentence, so the checker does not examine it. Verify it from the file, and propose a way to check sentences that make claims without figures.

**Exercise 13.3.** Run `draft_commentary()` five times with Ollama. Count how many drafts pass all checks. For the failures, classify the problems as value, label or direction.

**Exercise 13.4.** Write `facts_for_prompt()` for the Euro Corporate Bond Fund, which has no sector attribution in the repository. Which facts can you compute from the files, and which would you need from the performance team?

**Exercise 13.5.** The portfolio manager edits the approved commentary and adds *“We expect real estate to recover in the fourth quarter.”* What should the workflow do?

## Corrections

### Exercise 13.1

**What the question asks.** Show that the attribution effects add up: the sum of allocation, selection and interaction over all sectors equals HGEF’s gross return minus the benchmark’s for September 2026, after adding back the monthly fee to the net return.

**The plan.** (1) Sum the three effects over every row of the attribution file. (2) Read the net return and the benchmark return. (3) Add one month of the ongoing charge to the net return. (4) Compare.

**Step by step.**

`chapters/ch13/python/solutions/ex13_1_attribution_identity.py`

``` python
import pandas as pd
attr = pd.read_csv("data/am/hgef_attribution_2026_09.csv")
total_active = (attr.allocation + attr.selection + attr.interaction).sum()

nav = pd.read_csv("data/am/fund_nav_monthly.csv")
net = nav[(nav.fund_code == "HGEF") & (nav.month_end == "2026-09-30")].net_return.iloc[0]
gross = net + 0.0075 / 12
bench = pd.read_csv("data/am/benchmark_returns_monthly.csv").set_index("month_end").loc["2026-09-30", "HGEF"]
print(round(100 * total_active, 4), round(100 * (gross - bench), 4))
```

- The attribution file has one row per sector, plus a *Cash* row; the three effect columns are decimals.
- The NAV return is **net** of the ongoing charge of 0.75% a year. One month of it is $0.0075 / 12 = 0.000625$, or 0.0625%. Adding it back gives the gross return, which is what the holdings earned.
- `set_index("month_end").loc["2026-09-30", "HGEF"]` reads the benchmark’s return for that month.

`chapters/ch13/r/solutions/ex13_1_attribution_identity.R`

``` r
attr <- read.csv("data/am/hgef_attribution_2026_09.csv")
total_active <- sum(attr$allocation + attr$selection + attr$interaction)
nav <- read.csv("data/am/fund_nav_monthly.csv")
net <- nav$net_return[nav$fund_code == "HGEF" & nav$month_end == "2026-09-30"]
bm  <- read.csv("data/am/benchmark_returns_monthly.csv")
bench <- bm$HGEF[bm$month_end == "2026-09-30"]
cat(round(100 * total_active, 4), round(100 * (net + 0.0075 / 12 - bench), 4), "\n")
```

**Reading the result.** Both languages print `-0.4374 -0.4374`. The effects explain the gross relative return exactly: −0.4374%, or −43.74 basis points.

**Checking the answer.** Compute the net relative return too: $100 \times (\text{net} - \text{bench}) = -0.4999\%$. The difference between −0.4999% and −0.4374% is 0.0625%, exactly one month of the fee. Both identities hold, so the attribution file and the NAV file agree.

**Mistakes to avoid.**

- Comparing the effects with the net relative return and concluding that the attribution is wrong by 6 basis points.
- Dropping the *Cash* row before summing: cash has an allocation effect too, and the identity then fails.

**Trade-offs.** Attribution is computed on holdings before fees because fees are not a sector decision; the price is that the effects never match the published (net) relative return. A commentary saying *“sector effects explain the 0.50% underperformance”* would be wrong by the fee. The facts given to the model must state which return the effects explain, or the commentary must mention the fee separately.

### Exercise 13.2

**What the question asks.** Check the sentence *“Stock selection and sector allocation both detracted”* against the attribution file, although it contains no figure, and propose a way to check such claims automatically.

**The plan.** (1) Sum each effect. (2) Compare signs with the sentence. (3) Explain why the checker missed it. (4) Design a check for figure-less claims.

**Step by step.**

`chapters/ch13/python/solutions/ex13_2_both_detracted.py` (extract)

``` python
print(100 * attr.allocation.sum(), 100 * attr.selection.sum(),
      100 * attr.interaction.sum())
```

In R: `colSums(attr[, c("allocation", "selection", "interaction")]) * 100`.

**Reading the result.** Allocation −0.149% (−14.9bp), selection −0.262% (−26.2bp), interaction −0.0265% (−2.65bp). Allocation and selection are both negative: the sentence is true.

**Checking the answer.** The three totals sum to −0.4374%, the gross relative return of Exercise 13.1: the figures used to judge the sentence are consistent with the rest of the file.

**Mistakes to avoid.**

- Judging the sentence from the largest sectors only. *Allocation detracted* is a claim about the total over all sectors.
- Assuming a sentence without figures is safe. It passes the checker unseen, which makes it riskier, not safer.

**Trade-offs.** Two ways to check such claims. **Word facts**: turn each checkable claim type into a fact with a word value (`allocation total: detracted`, `selection total: detracted`), list the claim patterns (*(allocation\|selection) … (contributed\|detracted)*), and compare the verb with the fact. This handles a small closed set of claims and costs a pattern per claim type. **Figures everywhere**: instruct the model to attach a figure to every claim (*“selection detracted 26.2bp”*), so that every claim becomes checkable by the existing checker; the price is a heavier text. Open claims (*“driven by defensive positioning”*) remain for the manager either way.

### Exercise 13.3

**What the question asks.** Generate five commentaries with your model, count how many pass all checks, and classify each failure as a value, label or direction problem.

**The plan.** (1) Call `draft_commentary()` five times. (2) Collect the problems of each draft. (3) Classify each problem by reading the figure and its clause.

**Step by step.**

`chapters/ch13/python/solutions/ex13_3_five_drafts.py` (extract)

``` python
results = [draft_commentary() for _ in range(5)]
for text, report, version in results:
    problems = [(fig, p) for fig, _, p in report if p]
    print("PASS" if not problems else problems)
```

- `draft_commentary()` builds the facts, fills the prompt with `facts_for_prompt()` (figures already rounded, words already chosen), calls the model at temperature 0.3, and checks the draft with `check_commentary()`.
- Each report line is `(figure, matched facts, problem)`; `problem` is `None` when the figure is supported.

**Reading the result.** Each problem message names its type. *No fact with this value and label*: look at the figure; if the number appears nowhere in the facts it is a **value** problem; if it is a correct number in a clause that names another sector, a **label** problem. *Says positive, … is negative*: a **direction** problem.

**Checking the answer.** For each failed draft, find the figure in the prompt’s fact list by hand: a value problem has no line with that number; a label problem has the number on another sector’s line. Your classification must agree with that lookup.

**Mistakes to avoid.**

- Counting a draft as failed because its wording differs from the facts. Only figures, labels and directions are checked.
- Raising the temperature to get more variety. Variety adds label errors without adding facts.

**Trade-offs.** With pre-worded facts, direction errors become rare; label problems remain the most frequent, typically a figure placed in a clause that names a different sector. When a draft fails, regenerate once; if it fails again, send the manager the facts with the failed draft, never a draft marked as checked. Each regeneration costs a model call; at five drafts a month, that cost is negligible against a corrected factsheet.

### Exercise 13.4

**What the question asks.** Write the list of facts for an HECB commentary from the repository’s files, and say what would be needed from the performance team.

**The plan.** (1) List what the files give for a bond fund. (2) Write the function with the tools and queries already met: `fund_performance()` (Chapter 8) and the guarded SQL of Chapter 11. (3) Identify the missing explanation.

**Step by step.**

`chapters/ch13/python/solutions/ex13_4_hecb_facts.py` (extract)

``` python
from aie.sqlguard import run_sql
from aie.tools import fund_performance

HECB = "h.fund_code = 'HECB' AND h.month_end = '2026-09-30'"

def one(sql):
    return run_sql(sql)["rows"][0][0]           # the single value of a one-cell result

def hecb_facts_for_prompt():
    p = fund_performance("HECB", 1)
    duration = one(f"""SELECT SUM(h.weight * s.modified_duration) / SUM(h.weight)
                       FROM holdings h JOIN securities s ON h.isin = s.isin
                       WHERE {HECB}""")
    bbb = one(f"""SELECT SUM(h.weight) FROM holdings h JOIN securities s
                  ON h.isin = s.isin WHERE {HECB}
                  AND s.rating IN ('BBB+', 'BBB', 'BBB-')""")
    cash = one(f"SELECT SUM(h.weight) FROM holdings h WHERE {HECB} AND h.isin = 'CASH-EUR'")
    return "\n".join([
        f"- Fund return: {p['fund_return_pct']:.2f}%",
        f"- Benchmark return: {p['benchmark_return_pct']:.2f}%",
        f"- Relative return: {p['relative_return_pct']:+.2f}%",
        f"- Modified duration of the bonds: {duration:.2f} years",
        f"- Share of the bonds rated BBB+ to BBB-: {100 * bbb / (1 - cash):.2f}%",
        f"- Cash: {100 * cash:.2f}%"])

print(hecb_facts_for_prompt())
```

- `fund_performance("HECB", 1)` returns the one-month fund, benchmark and relative returns, already in percent.
- `one()` runs a query through `run_sql()` (Chapter 11) and returns its single value. The three queries are those of Chapter 11’s evaluation: the duration is case S04’s, the BBB query is case S08’s, and the cash query reads the `CASH-EUR` line.
- S08 gives the BBB share of the **fund**; dividing by the bonds’ share, `1 - cash`, gives the share of the **bonds**, the figure a bond fund reports.
- Each line is rounded and labelled, as in `facts_for_prompt()`: the model quotes, it never computes.

`chapters/ch13/r/solutions/ex13_4_hecb_facts.R`

``` r
source("aie_r/sqlguard.R"); source("aie_r/tools.R")
hecb <- "h.fund_code = 'HECB' AND h.month_end = '2026-09-30'"
one <- function(sql) run_sql(sql)$rows[[1]][1]      # the single value of a one-cell result
hecb_facts_for_prompt <- function() {
  p <- fund_performance("HECB", 1)
  duration <- one(paste("SELECT SUM(h.weight * s.modified_duration) / SUM(h.weight)",
                        "FROM holdings h JOIN securities s ON h.isin = s.isin WHERE", hecb))
  bbb <- one(paste("SELECT SUM(h.weight) FROM holdings h JOIN securities s ON h.isin = s.isin",
                   "WHERE", hecb, "AND s.rating IN ('BBB+', 'BBB', 'BBB-')"))
  cash <- one(paste("SELECT SUM(h.weight) FROM holdings h WHERE", hecb, "AND h.isin = 'CASH-EUR'"))
  paste(c(sprintf("- Fund return: %.2f%%", p$fund_return_pct),
          sprintf("- Benchmark return: %.2f%%", p$benchmark_return_pct),
          sprintf("- Relative return: %+.2f%%", p$relative_return_pct),
          sprintf("- Modified duration of the bonds: %.2f years", duration),
          sprintf("- Share of the bonds rated BBB+ to BBB-: %.2f%%", 100 * bbb / (1 - cash)),
          sprintf("- Cash: %.2f%%", 100 * cash)), collapse = "\n")
}
cat(hecb_facts_for_prompt(), "\n")
```

**Reading the result.** Both languages print:

``` text
- Fund return: -0.49%
- Benchmark return: -0.48%
- Relative return: -0.01%
- Modified duration of the bonds: 5.82 years
- Share of the bonds rated BBB+ to BBB-: 53.42%
- Cash: 2.00%
```

**Checking the answer.** Each figure matches an earlier result: the duration is S04’s 5.82 years and the BBB share of the fund is S08’s 0.523558 (Chapter 11); 0.523558 / 0.98 = 53.42%. The relative return −0.0099% rounds to −0.01%.

**Mistakes to avoid.**

- Quoting S08’s 52.36% as the share of the bonds. It is the share of the fund, cash included in the denominator.
- Asking the model to explain the relative return from these facts. Nothing in them explains it.

**Trade-offs.** A bond fund’s relative return is explained by duration, curve, credit spread and issuer selection effects: a fixed income attribution that the performance team produces with a dedicated model. Without it, the commentary can describe the return and the portfolio’s characteristics, not the causes. The honest prompt says so, and the commentary sticks to what the facts support; a shorter commentary is better than an invented explanation.

### Exercise 13.5

**What the question asks.** Decide what the workflow should do when the portfolio manager adds, after approval, the sentence *“We expect real estate to recover in the fourth quarter.”*

**The plan.** (1) Identify what kind of sentence it is. (2) Decide which checks apply to edited text. (3) Route the commentary.

**Step by step.** The sentence is a forecast. Factsheets are marketing communications: forecasts require a fair basis, balance and often a warning, and the firm’s compliance rules decide whether they are allowed at all. Extend the forbidden-phrase list of Chapter 6 with forecast patterns:

`chapters/ch13/python/solutions/ex13_5_forecast.py` (extract)

``` python
FORECAST = [r"\bwe expect\b", r"\bwill (recover|rebound|rise|fall)\b", r"\bis set to\b"]
```

and run every check again on the edited text.

**Reading the result.** The new sentence matches *we expect*: the commentary is flagged and goes to compliance review instead of publication. The figure checks still pass (the sentence has no figure).

**Checking the answer.** Run the checks on the approved text before the edit: no flag. Run them after: one flag, on the added sentence. The flag is caused by the edit alone.

**Mistakes to avoid.**

- Treating the manager’s approval as final. Approval covers the text approved, not later edits.
- Rewriting the manager’s sentence automatically into something compliant. The decision belongs to compliance and the manager, not to the pipeline.

**Trade-offs.** Running the checks after every edit costs a second review cycle when the manager changes the text; skipping them would publish unchecked text under a *checked* label. The version published must be the version that passed every check: log the edit, who made it, and the result of the checks on the final text.
