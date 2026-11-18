# 21. The Structured Finance Agent

## Exercises

**Exercise 21.1.** Run the evaluation with Ollama, in Python and R. Fill the release-criteria table with your results and decide whether the agent can be released.

**Exercise 21.2.** Add a case to the evaluation set that needs two tools: *“What share of the pool’s arrears balance was three months or more in arrears at 30 September 2026?”* What is the expected answer, and which tools should be called?

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

**Checking the answer.** For each failure, check the answer and the trace by hand, as in Exercise 9.1: call the expected tool yourself and compare. A05 (excess spread in August 2026) must be £412,990.44 from `waterfall_summary("2026-08-31")`; if the agent answered with September’s £692,429.96, the trace shows `cutoff_date` 2026-09-30, a date error, not a tool error.

**Mistakes to avoid.**

- Releasing on 11 of 12 when the failure is A07 or A09, which state a rule of the structure. Read *which* case failed, as Chapter 10’s criteria did for Q10 and Q14.
- Fixing several things at once after one run.

**Trade-offs.** Typical gaps with a small model: A05 and A06 (August 2026) answered with September’s figures because the model did not change the date; A10 (October 2026) answered with a September figure instead of saying the data ends. Fix one at a time: for dates, an example in the system prompt (*“for ‘August 2026’ use cutoff_date 2026-08-31”*); re-run. The Python and R agents share prompts, tools and data; with the same model at temperature 0 they usually make the same calls. Investigate any case that passes in one language and fails in the other: the difference is in how the two `chat()` functions build messages.

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

**Trade-offs.** `arrears_buckets` alone gives both numerator and denominator, but the share is a **computation**, which the agent must not do itself. Two designs: add a field `share_of_arrears_pct` to each bucket, so that the figure is computed by code and verifiable (one more field, every question of this kind answerable); or accept that the question cannot be answered with verified figures and expect `needs_review`. Add the case with `answer_type` `number`, expected 36.04, tolerance 0.005, `expected_tool` `arrears_buckets`, and record the design you chose. This case tests the rule of Chapter 1 at its most tempting: a simple division the model *could* do.

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

**Reading the result.** The first question contains *HGEF*, *factsheet*, *HECB* and *KID*, and no SF word: refused. The second contains *fund*, which is not an AM word on its own, and *Larkfield* and *reserve fund*, which are SF words: accepted. Both tests pass: 9/9.

**Checking the answer.** Probe the boundary further: *“What is the bond fund duration?”* is refused (*bond fund* is an AM word); *“Which notes does the reserve fund protect?”* is accepted. If you add *fund* alone to `AM_WORDS`, the second test fails at once: the test protects the boundary against a well-meant change.

**Mistakes to avoid.**

- Testing only obvious cases (*“What is HGEF’s return?”*). Boundary tests are the ones that catch regressions.
- Writing the tests in one language only: the R guard has its own word lists, and they can drift.

**Trade-offs.** Keyword guards are cheap, instant and testable, and they miss unusual phrasings (*“the euro credit product”*). Every miss found in production becomes a new test and, if needed, a new word. A model-based classifier would catch more phrasings at the cost of a model call and of its own evaluation; keep the keyword guard first either way, since it is free and certain on the cases it covers.

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
    "interest payment date, after the reconciliations pass. The draft must be "
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

**Trade-offs.** The agent becomes a front door to the workflow: the analyst asks in words, the workflow does the fixed steps, the analyst approves. The answer carries status `needs_review` by construction. The cost is one more tool in the agent’s list, which lengthens its tool descriptions; keep the description precise so that the agent calls it only for commentary requests.

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
