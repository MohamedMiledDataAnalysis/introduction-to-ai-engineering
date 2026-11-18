# 22. The Asset Management Agent

## Exercises

**Exercise 22.1.** Call `fund_characteristics` for the three funds. Why does only HECB have no equity sectors in its top three, and why does HBMA have a bond duration?

**Exercise 22.2.** Ask the agent: *“Which has the lower ongoing costs, HGEF or HECB?”* Which tool calls do you expect, and what must the answer contain to be verified?

**Exercise 22.3.** Turn the past-performance instruction into a check: any answer that contains a return and does not contain the warning gets status `needs_review`. Write it in Python and R.

**Exercise 22.4.** A distributor asks: *“Is HGEF an Article 8 fund, and did it meet its sustainability commitments last year?”* Trace the steps the agent should take, and the answer it should give, with citations.

**Exercise 22.5.** Run the evaluation with Ollama and compare the AM agent’s results with the SF agent’s. Which agent has the harder tasks, and why?

## Corrections

### Exercise 22.1

**What the question asks.** Call `fund_characteristics` for the three funds, and explain why HECB’s top sectors contain no equity sectors and why HBMA reports a bond duration.

**The plan.** (1) Call the tool for each fund. (2) Compare the fields returned. (3) Relate them to what each fund holds. (4) Find the field whose meaning is easy to misstate.

**Step by step.**

``` python
import sys; sys.path.insert(0, ".")
from aie.tools import fund_characteristics
for f in ("HGEF", "HECB", "HBMA"):
    print(fund_characteristics(f))
```

In R: `for (f in c("HGEF", "HECB", "HBMA")) cat(run_tool(list(name = "fund_characteristics", arguments = list(fund_code = f))), "\n")`.

The tool computes, from the holdings of 30 September 2026 joined to the security master: the number of holdings, the cash weight, weighted ESG score and carbon intensity, the top three sectors, and, **only if the fund holds bonds**, the duration and the BBB share computed on the bonds alone.

**Reading the result.**

|                    | HGEF                          | HECB              | HBMA              |
|--------------------|-------------------------------|-------------------|-------------------|
| Holdings           | 50                            | 45                | 45                |
| Cash               | 1.5%                          | 2.0%              | 5.0%              |
| Top sector         | Information Technology 16.32% | Financials 35.44% | Financials 26.67% |
| Bond duration      | —                             | 5.82 years        | 6.11 years        |
| BBB share of bonds | —                             | 53.42%            | 60.49%            |

HECB holds only corporate bonds: its “sectors” are the sectors of the bond **issuers** (banks, technology companies, industrial companies), taken from the security master. HGEF holds only equities, so the bond fields are absent. HBMA holds both, so it reports issuer sectors and a duration computed on its bond sleeve.

**Checking the answer.** Check HBMA’s mix in the holdings file: at 30 September 2026, 55.0% equities, 40.0% fixed income and 5.0% cash. The bond fields describe the 40%. Check HECB’s duration against Chapter 11: S04’s reference query returns 5.8227 years, which the tool rounds to 5.82.

**Mistakes to avoid.**

- Reading HECB’s *Financials 35.44%* as a holding of bank shares. It is bonds issued by financial companies.
- Writing *“HBMA has a duration of 6.11 years”*. The fund’s 55% in equities has no duration in this sense; the correct statement is *“HBMA’s bonds have a modified duration of 6.11 years”*.

**Trade-offs.** The field name says *bond* (`bond_modified_duration_years`); the model may still drop the word. Two fixes, both cheap: a sentence in the system prompt (*“quote the meaning of each field, not only its value; for HBMA, duration and rating shares describe the bonds only”*) and an evaluation case, *“What is HBMA’s duration?”*, whose keywords require *bonds*. A meaning error cannot be caught by the figure check, because the value is in the tool result; only a test written by someone who knows the domain catches it.

### Exercise 22.2

**What the question asks.** For *“Which has the lower ongoing costs, HGEF or HECB?”*, predict the tool calls and say what the answer must contain to be verified.

**The plan.** (1) Find where costs are stated. (2) Work out the calls the filter forces. (3) Write the expected answer. (4) Check what verification can and cannot catch.

**Step by step.** Costs are in each fund’s KID (and in its factsheet’s key facts). `search_fund_documents` takes one `fund_code`, required by its schema, so the agent needs **two** calls:

``` python
run_tool({"name": "search_fund_documents",
          "arguments": {"query": "ongoing costs", "fund_code": "HGEF"}})
run_tool({"name": "search_fund_documents",
          "arguments": {"query": "ongoing costs", "fund_code": "HECB"}})
```

The first returns `HGEF-KID#7` first, the second `HECB-KID#21`: each fund’s cost section, and nothing from the other fund.

**Reading the result.** The expected answer: *“HECB has the lower ongoing costs: 0.46% a year, of which 0.40% management and operating costs and 0.06% transaction costs \[HECB-KID#21\], against 0.86% for HGEF, of which 0.75% and 0.11% \[HGEF-KID#7\].”* In a PRIIPs KID, *ongoing costs taken each year* are the sum of two lines: management fees and other administrative or operating costs, and transaction costs. The fund master’s `ocf` (ongoing charges figure) holds only the first, 0.40% and 0.75%.

**Checking the answer.** Every figure is in the retrieved passages (the *Annual cost impact* line gives 0.86% and 0.46%, the two cost lines give 0.75% and 0.11% in HGEF’s KID and 0.40% and 0.06% in HECB’s), so `passage_facts()` supports them and the status is `verified`. The management and operating costs also match the fund master: `ocf` 0.0075 and 0.0040 in `funds.csv`.

**Mistakes to avoid.**

- Accepting *“HECB is cheaper”* without figures. It contains no figure, so the figure check passes it by default. Add to the system prompt *“in comparisons, quote each figure”*, and add the case to the evaluation set with keywords for both figures.
- One call without a fund filter: the schema refuses it, because `fund_code` is required.

**Trade-offs.** If the model makes a single call for one fund, it cannot cite the other’s figure, and verification flags any figure it invents for it. The design makes the wrong answer hard to produce and easy to detect, at the cost of two tool calls for every comparison. For frequent comparisons, a dedicated tool (`compare_costs(fund_codes)`) returning both figures from the fund master would be faster and verifiable in one step.

### Exercise 22.3

**What the question asks.** Turn the instruction *“quote returns with the past-performance warning”* into a check: an answer that contains a return and no warning gets status `needs_review`. Write it in Python and R.

**The plan.** (1) Define *contains a return*: a percentage and a performance word. (2) Define *contains the warning*. (3) Write the check. (4) Call it in `Assistant.ask()`. (5) Test it on four sentences.

**Step by step.**

``` python
import re
from aie.factcheck import extract_figures

WARNING = re.compile(r"past performance (does not|is not a reliable)", re.I)
RETURN_WORDS = re.compile(r"\b(return(ed)?|performance|gained|lost)\b", re.I)

def missing_warning(answer):
    has_figure = any(f.unit == "percent" for f in extract_figures(answer))
    return bool(has_figure and RETURN_WORDS.search(answer)
                and not WARNING.search(answer))
```

- `extract_figures()` (Chapter 6) finds the figures; a return is quoted as a percentage.
- `RETURN_WORDS` looks for words that introduce a performance figure.
- `WARNING` accepts the two usual wordings, *does not predict* and *is not a reliable indicator*.

In `Assistant.ask()`, after the forbidden-phrase check:

``` python
if self.domain == "am" and missing_warning(result["answer"]):
    result["status"] = "needs_review"
    result["unsupported"].append("past performance warning missing")
```

In R:

``` r
missing_warning <- function(answer) {
  figs <- extract_figures(answer)
  any(figs$unit == "percent") &&
    grepl("\\b(return(ed)?|performance|gained|lost)\\b", answer, ignore.case = TRUE, perl = TRUE) &&
    !grepl("past performance (does not|is not a reliable)", answer, ignore.case = TRUE)
}
```

**Reading the result.**

| Answer                                                                    | `missing_warning`    |
|---------------------------------------------------------------------------|----------------------|
| *HGEF returned 6.46% over one year to 30 September 2026.*                 | `True`: needs review |
| *HGEF returned 6.46% … Past performance does not predict future returns.* | `False`              |
| *HECB’s ongoing costs are 0.40%.*                                         | `False`              |
| *Ongoing costs of 0.40% reduce the return each year.*                     | `True`: a false fail |

Python and R give the same four results.

**Checking the answer.** The fourth sentence has a percentage and the word *return* but quotes no performance: a false fail. It is visible (the analyst sees *past performance warning missing* on an answer about costs) and harmless (`needs_review`, not a refusal). Count false fails on the AM evaluation set’s answers: if they are frequent, narrow the check.

**Mistakes to avoid.**

- Requiring the exact warning sentence. Compliance may approve several wordings; list them in the pattern.
- Appending the warning automatically to every answer. It hides whether the model followed the instruction, and adds a warning to answers about costs.

**Trade-offs.** Narrow the check by requiring a figure that matches a `fund_performance` result in the trace: the check then fires only on returns actually quoted, at the cost of passing the trace to the check. Broad checks are simple and over-flag; narrow checks are precise and depend on more of the system. Here, over-flagging costs a minute of review; under-flagging puts an incomplete fund communication in front of a distributor.

**On GitHub.** The companion repository goes further: the check in Python and R, the narrow version of the trade-off, both tested on eight labelled answers, and the integration in the assistant, in `solutions/ch22_corrections.md`.

#### Going further on GitHub: the check in both languages, broad and narrow, measured

This part is in the companion repository only. It gives the book’s check and the narrow check of the trade-off, both in Python and R. Both are measured on eight labelled answers, and the integration in the assistant is shown.

**The complete script, in Python.**

`chapters/ch22/python/solutions/ex22_3_missing_warning.py`

``` python
# Exercise 22.3 - The past-performance warning as a check, broad and narrow
# Run from the root of the repository:  python chapters/ch22/python/solutions/ex22_3_missing_warning.py
import json
import re
import sys

sys.path.insert(0, ".")
from aie.agent import facts_from_results
from aie.factcheck import check_text, extract_figures
from aie.tools import fund_performance

WARNING = re.compile(r"past performance (does not|is not a reliable)", re.I)
RETURN_WORDS = re.compile(r"\b(return(ed)?|performance|gained|lost)\b", re.I)


def missing_warning(answer):
    """The book's check: a percentage, a performance word, and no warning."""
    has_figure = any(f.unit == "percent" for f in extract_figures(answer))
    return bool(has_figure and RETURN_WORDS.search(answer)
                and not WARNING.search(answer))


def missing_warning_narrow(answer, results):
    """The trade-off of the book: fire only if the answer quotes a return that a fund_performance call returned."""
    returns = {k: v for k, v in facts_from_results(results).items() if k.endswith("return_pct")}
    quotes_a_return = any(hits for _, hits in check_text(answer, returns))
    return bool(quotes_a_return and not WARNING.search(answer))


def apply_warning_check(result, domain="am"):
    """What Assistant.ask() does after the forbidden-phrase check (the book's integration)."""
    if domain == "am" and missing_warning(result["answer"]):
        result["status"] = "needs_review"
        result["unsupported"].append("past performance warning missing")
    return result


# 1. The four sentences of the book
book = ["HGEF returned 6.46% over one year to 30 September 2026.",
        "HGEF returned 6.46% over one year to 30 September 2026. Past performance does not predict future returns.",
        "HECB's ongoing costs are 0.40%.",
        "Ongoing costs of 0.40% reduce the return each year."]
print("The four sentences of the book:")
for s in book:
    print(f"  {str(missing_warning(s)):<6} {s}")

# 2. A larger set of answers, each labelled with the right decision, and the trace the agent would have
perf = [("fund_performance", json.dumps(fund_performance("HGEF", 12))),
        ("fund_performance", json.dumps(fund_performance("HECB", 12)))]
labelled = [  # (answer, a warning is required?)
    ("HGEF returned 6.46% over one year, against 7.86% for its benchmark.", True),
    ("HGEF returned 6.46% over one year. Past performance is not a reliable indicator of future results.", False),
    ("HGEF trailed its benchmark by 1.40% over one year.", True),
    ("HECB's ongoing costs are 0.40%.", False),
    ("Ongoing costs of 0.40% reduce the return each year.", False),
    ("The fund's largest holding is 4.2% of the portfolio.", False),
    ("HGEF's performance fee is 0%; there is none.", False),
    ("Information technology is 16.08% of HGEF, against 17.34% for the benchmark.", False),
]
print("\nBroad and narrow check on labelled answers:")
broad_err = narrow_err = 0
for answer, required in labelled:
    b, n = missing_warning(answer), missing_warning_narrow(answer, perf)
    broad_err += b != required
    narrow_err += n != required
    print(f"  required {str(required):<5} broad {str(b):<5} narrow {str(n):<5} {answer[:70]}")
print(f"Wrong decisions: broad {broad_err} of {len(labelled)}, narrow {narrow_err} of {len(labelled)}")

# 3. The integration: an agent result before and after the check
r = apply_warning_check({"answer": book[0], "status": "verified", "unsupported": []})
print("\nAfter the check:", r["status"], r["unsupported"])
```

- `missing_warning()` is the check of the book.
- `missing_warning_narrow()` keeps from the agent’s facts only the returns (`fund_return_pct`, `benchmark_return_pct`, `relative_return_pct`) and fires only when the answer quotes one of them without the warning. `facts_from_results()` builds the facts exactly as the agent’s verifier does.
- `perf` holds two calls of `fund_performance`, HGEF and HECB, as the trace would after a comparison question.
- `labelled` pairs each answer with the right decision, so that the script counts wrong decisions instead of printing results to read by eye.

**Output**

``` text
The four sentences of the book:
  True   HGEF returned 6.46% over one year to 30 September 2026.
  False  HGEF returned 6.46% over one year to 30 September 2026. Past performance does not predict future returns.
  False  HECB's ongoing costs are 0.40%.
  True   Ongoing costs of 0.40% reduce the return each year.

Broad and narrow check on labelled answers:
  required True  broad True  narrow True  HGEF returned 6.46% over one year, against 7.86% for its benchmark.
  required False broad False narrow False HGEF returned 6.46% over one year. Past performance is not a reliable 
  required True  broad False narrow True  HGEF trailed its benchmark by 1.40% over one year.
  required False broad False narrow False HECB's ongoing costs are 0.40%.
  required False broad True  narrow False Ongoing costs of 0.40% reduce the return each year.
  required False broad False narrow False The fund's largest holding is 4.2% of the portfolio.
  required False broad True  narrow True  HGEF's performance fee is 0%; there is none.
  required False broad False narrow False Information technology is 16.08% of HGEF, against 17.34% for the bench
Wrong decisions: broad 3 of 8, narrow 1 of 8

After the check: needs_review ['past performance warning missing']
```

**Reading the result.** The broad check makes three wrong decisions out of eight, of two kinds:

- It misses *“trailed its benchmark by 1.40%”*: no word of `RETURN_WORDS` appears.
- It flags *“Ongoing costs of 0.40% reduce the return each year”* (the false fail of the book) and *“performance fee is 0%”*.

The narrow check makes one wrong decision. It catches the trailing sentence, because 1.40% is HGEF’s relative return, and it passes the costs sentence. It still flags *“0%”*: a figure written with no decimals matches any return that rounds to 0, and HECB’s relative return, −0.48%, does. A figure without decimals carries little information, and the matching cannot do better than the figure.

**The complete script, in R.**

`chapters/ch22/r/solutions/ex22_3_missing_warning.R`

``` r
# Exercise 22.3 - The past-performance warning as a check, broad and narrow
# Run from the root of the repository:  Rscript chapters/ch22/r/solutions/ex22_3_missing_warning.R
suppressPackageStartupMessages(source("aie_r/agent.R"))

missing_warning <- function(answer) {
  # the book's check: a percentage, a performance word, and no warning
  figs <- extract_figures(answer)
  any(figs$unit == "percent") &&
    grepl("\\b(return(ed)?|performance|gained|lost)\\b", answer, ignore.case = TRUE, perl = TRUE) &&
    !grepl("past performance (does not|is not a reliable)", answer, ignore.case = TRUE)
}

missing_warning_narrow <- function(answer, results) {
  # the trade-off of the book: fire only if the answer quotes a return that a fund_performance call returned
  f <- facts_from_results(results)
  returns <- f[endsWith(names(f), "return_pct")]
  quotes_a_return <- any(vapply(check_text(answer, returns), function(r) length(r$hits) > 0, TRUE))
  quotes_a_return && !grepl("past performance (does not|is not a reliable)", answer, ignore.case = TRUE)
}

apply_warning_check <- function(result, domain = "am") {
  # what ask_assistant() does after the forbidden-phrase check (the book's integration)
  if (domain == "am" && missing_warning(result$answer)) {
    result$status <- "needs_review"
    result$unsupported <- c(result$unsupported, "past performance warning missing")
  }
  result
}

# 1. The four sentences of the book
book <- c("HGEF returned 6.46% over one year to 30 September 2026.",
          "HGEF returned 6.46% over one year to 30 September 2026. Past performance does not predict future returns.",
          "HECB's ongoing costs are 0.40%.",
          "Ongoing costs of 0.40% reduce the return each year.")
cat("The four sentences of the book:\n")
for (s in book) cat(sprintf("  %-6s %s\n", if (missing_warning(s)) "True" else "False", s))

# 2. A larger set of answers, each labelled with the right decision, and the trace the agent would have
as_result <- function(code) list(name = "fund_performance",
  result = as.character(toJSON(fund_performance(code, 12), auto_unbox = TRUE, digits = NA)))
perf <- list(as_result("HGEF"), as_result("HECB"))
labelled <- data.frame(stringsAsFactors = FALSE,
  answer = c("HGEF returned 6.46% over one year, against 7.86% for its benchmark.",
             "HGEF returned 6.46% over one year. Past performance is not a reliable indicator of future results.",
             "HGEF trailed its benchmark by 1.40% over one year.",
             "HECB's ongoing costs are 0.40%.",
             "Ongoing costs of 0.40% reduce the return each year.",
             "The fund's largest holding is 4.2% of the portfolio.",
             "HGEF's performance fee is 0%; there is none.",
             "Information technology is 16.08% of HGEF, against 17.34% for the benchmark."),
  required = c(TRUE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE))
labelled$broad <- vapply(labelled$answer, missing_warning, TRUE)
labelled$narrow <- vapply(labelled$answer, missing_warning_narrow, TRUE, results = perf)
cat("\nBroad and narrow check on labelled answers:\n")
for (i in seq_len(nrow(labelled)))
  cat(sprintf("  required %-5s broad %-5s narrow %-5s %s\n", labelled$required[i], labelled$broad[i],
              labelled$narrow[i], substr(labelled$answer[i], 1, 70)))
cat(sprintf("Wrong decisions: broad %d of %d, narrow %d of %d\n", sum(labelled$broad != labelled$required),
            nrow(labelled), sum(labelled$narrow != labelled$required), nrow(labelled)))

# 3. The integration: an agent result before and after the check
r <- apply_warning_check(list(answer = book[1], status = "verified", unsupported = character(0)))
cat("\nAfter the check:", r$status, r$unsupported, "\n")
```

**Output**

``` text
The four sentences of the book:
  True   HGEF returned 6.46% over one year to 30 September 2026.
  False  HGEF returned 6.46% over one year to 30 September 2026. Past performance does not predict future returns.
  False  HECB's ongoing costs are 0.40%.
  True   Ongoing costs of 0.40% reduce the return each year.

Broad and narrow check on labelled answers:
  required TRUE  broad TRUE  narrow TRUE  HGEF returned 6.46% over one year, against 7.86% for its benchmark.
  required FALSE broad FALSE narrow FALSE HGEF returned 6.46% over one year. Past performance is not a reliable 
  required TRUE  broad FALSE narrow TRUE  HGEF trailed its benchmark by 1.40% over one year.
  required FALSE broad FALSE narrow FALSE HECB's ongoing costs are 0.40%.
  required FALSE broad TRUE  narrow FALSE Ongoing costs of 0.40% reduce the return each year.
  required FALSE broad FALSE narrow FALSE The fund's largest holding is 4.2% of the portfolio.
  required FALSE broad TRUE  narrow TRUE  HGEF's performance fee is 0%; there is none.
  required FALSE broad FALSE narrow FALSE Information technology is 16.08% of HGEF, against 17.34% for the bench
Wrong decisions: broad 3 of 8, narrow 1 of 8

After the check: needs_review past performance warning missing 
```

- `vapply(labelled$answer, missing_warning_narrow, TRUE, results = perf)` calls the narrow check once per answer and passes the same trace each time.
- `f[endsWith(names(f), "return_pct")]` keeps the returns from the facts, as the dictionary comprehension does in Python.

Python and R give the same decisions.

**A correction to the library found by this exercise.** Before this exercise, a second call of the same tool overwrote the facts of the first in `facts_from_results()`, because both were named `fund_performance.fund_return_pct`. HGEF’s 6.46% was then *unsupported* in an answer comparing HGEF and HECB. The functions in `aie/agent.py` and `aie_r/agent.R` now name the facts of a second call `fund_performance#2.fund_return_pct`. The facts of a single call keep their names, so every result printed in the book is unchanged.

**More mistakes to avoid.**

- Testing a check only on the sentences that motivated it. The labelled set shows a miss (*trailed*) that the four sentences of the book could not reveal.
- Using the narrow check where no trace exists, for example on a commentary written by hand: there are no tool results to match, and it never fires.

**More trade-offs.** Use the broad check where text arrives without a trace, and the narrow one inside the agent, where the trace is always there. Both can run: an answer flagged by either goes to review. That costs a few more reviews and catches more missing warnings, and that is the right balance for a fund communication.

### Exercise 22.4

**What the question asks.** For *“Is HGEF an Article 8 fund, and did it meet its sustainability commitments last year?”*, trace the agent’s steps and write the answer it should give, with citations.

**The plan.** (1) Search HGEF’s documents. (2) Read the passages returned. (3) Write the answer from them. (4) Check each figure and claim.

**Step by step.**

``` python
run_tool({"name": "search_fund_documents",
          "arguments": {"query": "Is HGEF an Article 8 fund? sustainability characteristics met",
                        "fund_code": "HGEF", "k": 3}})
```

The three passages returned are `HGEF-SFDR#44` (the two characteristics and the indicators table), `HGEF-SFDR#51` (the disclosure’s key facts: *Periodic disclosure for the financial products referred to in Article 8 …*, reference period 1 October 2025 to 30 September 2026) and `HGEF-SFDR#46` (the proportion of investments aligned with the characteristics). The factsheet’s key facts, `HGEF-factsheet#48`, also state *SFDR classification: Article 8*; it comes second, after `HGEF-SFDR#51`, for the shorter query *“Is HGEF an Article 8 fund?”*.

**Reading the result.** The answer: *“HGEF is classified as an Article 8 fund \[HGEF-SFDR#51\]. Over the reference period 1 October 2025 to 30 September 2026 it promoted two characteristics: excluding companies deriving more than 10% of revenue from thermal coal, and a weighted average carbon intensity below its benchmark’s. Both were met: no excluded holdings, and a WACI of 144.9 against 160.1 tCO2e per EUR million of revenue \[HGEF-SFDR#44\].”*

**Checking the answer.** 10%, 144.9 and 160.1 are all in `HGEF-SFDR#44`, so verification passes. *Met* is a word, not a figure: the disclosure’s table says *Yes* for both indicators, which a reviewer sees in the cited passage. And 144.9 matches `fund_characteristics("HGEF")["weighted_carbon_intensity"]`: the disclosure and the holdings agree.

This exercise found a gap in the index. In the first version of `search_fund_documents`, the factsheet’s key facts table and the disclosure’s title sat before the first `##` heading, and `chunk_markdown()` indexes sections only: *Article 8* was in no indexed passage, and the agent could not cite it. The repository’s `_fund_docs_index()` (and `.fund_docs()` in R) now adds one *Key facts* chunk per factsheet and for the disclosure, appended after the other chunks so that existing identifiers such as `HECB-KID#21` are unchanged.

**Mistakes to avoid.**

- Characterising the fund (*“HGEF is a sustainable fund”*, *“has a low carbon footprint”*). These are claims beyond the disclosure, and sustainability claims are themselves regulated (anti-greenwashing rules in the UK and the EU). Quote the disclosure; do not characterise the fund.
- Assuming that a fact in a document is retrievable. Test retrieval for every fact the evaluation asks about.

**Trade-offs.** Adding the key-facts chunks makes the classification, ISIN, costs and risk indicator retrievable from the factsheets too, so the same figure can now come from two passages (KID and factsheet). That is harmless while the documents agree, and Chapter 15’s checks catch them when they do not. The alternative, changing `chunk_markdown()` for every document, would renumber every chunk of the book and invalidate earlier evaluation results: append, do not renumber.

### Exercise 22.5

**What the question asks.** Run the AM evaluation with your model, compare its three measures with the SF agent’s, and say which agent has the harder tasks and why.

**The plan.** (1) Run both evaluations. (2) Put the three measures side by side. (3) Compare the failures by type. (4) Decide what follows.

**Step by step.**

``` bash
python agents/python/evaluate_agent.py sf
python agents/python/evaluate_agent.py am
```

The scripts are identical; only the domain changes the assistant, the tools and the evaluation file (`evals/sf_agent_eval.csv`, twelve cases; `evals/am_agent_eval.csv`, eleven cases).

**Reading the result.**

| Measure         | SF target  | AM target  | SF result                     | AM result |
|-----------------|------------|------------|-------------------------------|-----------|
| Correct answers | ≥ 11 of 12 | ≥ 10 of 11 | 8 of 12 scored; 12 of 12 read | 10 of 11  |
| Right tool      | 10 of 10   | 8 of 8     | 10 of 10                      | 8 of 8    |
| Stopped         | 0          | 0          | 0                             | 0         |

The results are those of the Python run with `qwen3.5:4b` printed in Chapters 21 and 22. Refusals (A11–A12, B09–B11) are declined by the guards in both.

**Checking the answer.** Classify each failure by the step that failed: fund or date choice, finding a figure in a tool result, quoting, verification, or the scorer. In this run, all four SF failures are the scorer’s (numbers in words, a decline in other words, a keyword missing), and the agent’s one imprecision is a sentence without a figure (A07). The AM failure is the agent’s: a wrong one-year return for HGEF (B01), which verification flagged `needs_review`. The AM tasks are harder for two reasons: the agent must choose among three funds before any tool call, and its answers carry regulatory duties (costs as the KID states them, the past-performance warning) that the SF answers do not. Your results will differ in detail; the classification tells you where the difficulty lies.

**Mistakes to avoid.**

- Comparing pass rates on 11 and 12 cases as if they were precise: both intervals are wide (Chapter 5).
- Concluding that the AM model is “worse”. The same model faces harder tasks.

**Trade-offs.** The AM agent usually has the harder tasks: document questions need a fund choice and a table lookup, whereas most SF questions map to one tool with one date. Equal targets for both agents can mean more prompt work on the AM side, or a larger model for it alone. In the service of Chapter 18 that is a small change: give each domain’s `Agent` its own model name instead of the single `AIE_MODEL`. Decide with the evaluation, and record the choice in each model card.
