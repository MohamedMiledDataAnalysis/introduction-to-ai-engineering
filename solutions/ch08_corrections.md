# 8. Tools: Letting the Model Use Your Code

> © 2026 Mohamed Miled. All rights reserved. This text is part of the book *Introduction to AI Engineering* and may not be copied, republished or sold. The code blocks are under the MIT licence (see `LICENSE`); the explanations are not (see `LICENSE-TEXT.md`).

## Exercises

**Exercise 8.1.** Write a new tool `arrears_buckets(cutoff_date)` that returns, for the Larkfield pool, the number of loans and the balance in arrears of 1 month, 2 months, 3 months and 4–5 months (from `RREL68`). Register it with a description and schema, in Python and R, and run it for `2026-09-30`.

**Exercise 8.2.** Call `run_tool()` with `allowed=["fund_performance", "top_holdings"]` and the call `pool_summary(cutoff_date="2026-09-30")`. What happens, and why is this better than relying on the system prompt to tell the model not to use loan tools?

**Exercise 8.3.** Write `check_answer_against_tools(answer, trace)` that builds a fact table from the numeric values in the tool results of a trace and checks the answer’s figures with `check_text()` of Chapter 6. Test it with the scripted answer, and with the same answer where 0.8432% is replaced by 0.8342%.

**Exercise 8.4.** A colleague proposes a tool `send_investor_email(to, subject, body)` so that the assistant can answer investors directly. Write the review you would give, with the design you would accept instead.

**Exercise 8.5.** The question *“What was the balance in September?”* is ambiguous. List the tools and arguments a model could reasonably choose, and rewrite one tool description so that the model is more likely to ask the user which balance is meant.

## Corrections

### Exercise 8.1

**What the question asks.** Write a tool that returns the number of Larkfield loans and their balance in each arrears bucket (1, 2, 3 and 4–5 months), register it with a description and a schema in Python and R, and run it for 30 September 2026.

**The plan.** (1) Write the function: filter the date and the status `ARRE`, convert days to months, count and sum by bucket. (2) Register it: function, description, JSON schema. (3) Write the same in R. (4) Reconcile its totals with `pool_summary()`.

**Step by step.**

*Step 1 — The function.*

`aie/tools.py` (extract)

``` python
def arrears_buckets(cutoff_date):
    t = _tape()
    _check_date(cutoff_date, t["RREL6"])
    m = t[(t["RREL6"] == cutoff_date) & (t["RREL69"] == "ARRE")].copy()
    m["months"] = (m["RREL68"] // 30).clip(upper=4)
    labels = {1: "1 month", 2: "2 months", 3: "3 months", 4: "4-5 months"}
    return {"cutoff_date": cutoff_date,
            "buckets": [{"bucket": lab, "loans": int((m["months"] == k).sum()),
                         "balance_gbp": round(m.loc[m["months"] == k, "RREL30"].sum(), 2)}
                        for k, lab in labels.items()]}
```

- `_tape()` returns the loan tape, read once and kept in memory; `_check_date()` raises a clear error if the date is not a cut-off in the tape.
- The filter keeps loans in arrears at that date. `.copy()` avoids pandas’ warning when a column is added to a filtered table.
- `RREL68 // 30` turns days into whole months; `.clip(upper=4)` puts 4 and 5 months in one bucket. Six months and more are defaulted loans, status `DFLT`, already excluded by the filter.
- `int(...)` and `round(..., 2)` turn numpy numbers into plain Python numbers, which `json.dumps()` can write.
- The key `balance_gbp` ends with the unit: Chapter 9 relies on this convention.

*Step 2 — Register it.*

`aie/tools.py` (extract)

``` python
REGISTRY["arrears_buckets"] = (
    arrears_buckets,
    "Number of loans and current balance of the Larkfield 2025-1 loans in "
    "arrears at a month-end, by months in arrears: 1, 2, 3, and 4 to 5. "
    "Defaulted loans (6 months or more) are not included.",
    {"type": "object",
     "properties": {"cutoff_date": {"type": "string",
                    "pattern": "20[0-9]{2}-[0-9]{2}-[0-9]{2}"}},
     "required": ["cutoff_date"], "additionalProperties": False})
```

- The registry entry is a tuple: the function, the description the model reads, and the schema the dispatcher validates against.
- The `pattern` refuses dates such as `30/09/2026` before the function runs.

*Step 3 — R.*

`aie_r/tools.R` (extract)

``` r
arrears_buckets <- function(cutoff_date) {
  t <- .load("tape", "data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
  .check_date(cutoff_date, t$RREL6)
  m <- t[t$RREL6 == cutoff_date & t$RREL69 == "ARRE", ]
  months <- pmin(m$RREL68 %/% 30, 4)
  labels <- c("1 month", "2 months", "3 months", "4-5 months")
  list(cutoff_date = cutoff_date, buckets = lapply(1:4, function(k)
    list(bucket = labels[k], loans = sum(months == k),
         balance_gbp = round(sum(m$RREL30[months == k]), 2))))
}
registry$arrears_buckets <- list(fn = arrears_buckets,
  description = paste("Number of loans and current balance of the Larkfield",
    "2025-1 loans in arrears at a month-end, by months in arrears: 1, 2, 3,",
    "and 4 to 5. Defaulted loans (6 months or more) are not included."),
  parameters = list(type = "object",
    properties = list(cutoff_date = date_rule),
    required = list("cutoff_date"), additionalProperties = FALSE))
```

- `%/%` is integer division; `pmin(x, 4)` caps each value at 4, like `clip`.
- `lapply(1:4, ...)` builds one list per bucket; `sum(months == k)` counts the loans in bucket `k`.

The repository’s `aie/tools.py` and `aie_r/tools.R` already contain this tool, because the final project uses it; compare your version with them. `chapters/ch08/python/solutions/ex8_1_arrears_buckets.py` (and `.R`) calls it through `run_tool()` with a valid and an invalid date.

**Reading the result.**

**What you should see**

``` text
{"cutoff_date": "2026-09-30", "buckets": [
  {"bucket": "1 month", "loans": 5, "balance_gbp": 652077.1},
  {"bucket": "2 months", "loans": 6, "balance_gbp": 1088476.03},
  {"bucket": "3 months", "loans": 3, "balance_gbp": 452041.82},
  {"bucket": "4-5 months", "loans": 4, "balance_gbp": 528615.73}]}
```

**Checking the answer.** Reconcile with the existing tool: $5 + 6 + 3 + 4 = 18$ loans, the 18 `ARRE` loans of Exercise 1.1; $652{,}077.10 + 1{,}088{,}476.03 + 452{,}041.82 + 528{,}615.73 = 2{,}721{,}210.68$, the `arrears_balance_gbp` returned by `pool_summary()`. A new tool is always reconciled with an existing one before a model sees it.

**Mistakes to avoid.**

- Forgetting the defaulted loans in the description. A model asked *“how many loans are six months behind?”* would call this tool and answer 0. With the sentence, it knows the tool cannot answer.
- Returning numpy types: `json.dumps()` fails on `numpy.int64` with *Object of type int64 is not JSON serializable*.
- Bucketing with `round(RREL68 / 30)`: 45 days would become 2 months instead of 1.

**Trade-offs.** Fixed buckets are what investor reports use and what the model can quote directly; a tool returning every loan’s days in arrears would be more flexible, but the model would then have to count and sum, which is what tools are meant to spare it. Give models aggregated, labelled results.

### Exercise 8.2

**What the question asks.** Call `pool_summary` through the dispatcher with an allow-list that contains only the two fund tools, observe the result, and explain why this is better than a prompt instruction.

**The plan.** Run one call with `allowed=`, read the result, follow it in `run_tool()`.

**Step by step.**

`chapters/ch08/python/solutions/ex8_2_allowed_tools.py` (extract)

``` python
print(run_tool({"name": "pool_summary",
                "arguments": {"cutoff_date": "2026-09-30"}},
               allowed=["fund_performance", "top_holdings"]))
```

`chapters/ch08/r/solutions/ex8_2_allowed_tools.R` (extract)

``` r
cat(run_tool(list(name = "pool_summary", arguments = list(cutoff_date = "2026-09-30")),
             allowed = c("fund_performance", "top_holdings")))
```

The first lines of `run_tool()`:

`aie/tools.py` (extract)

``` python
if name not in REGISTRY or (allowed is not None and name not in allowed):
    return json.dumps({"error": f"unknown tool {name}"})
```

- The condition is true if the tool does not exist **or** if an allow-list is given and the tool is not in it. The function returns before validating arguments or running anything.

**Reading the result.**

``` text
{"error": "unknown tool pool_summary"}
```

The tool exists in the registry, but the call is refused.

**Checking the answer.** Run the same call without `allowed=`: it returns the pool summary (pool balance £322,717,766.58, arrears ratio 0.8432%). The only difference is the allow-list, so the refusal comes from it.

**Mistakes to avoid.**

- Filtering the tools shown to the model but not the tools the dispatcher runs. A model can name a tool it was not shown (from an earlier conversation, or an injected instruction); only the dispatcher’s check stops it.
- Returning *not allowed* instead of *unknown tool*. *Not allowed* tells the model the tool exists and invites it to insist; *unknown tool* reveals nothing about tools outside the application.

**Trade-offs.** A system prompt is a request the model usually follows; the allow-list is a rule it cannot break. Use instructions to guide behaviour and code to enforce limits. The cost is one list to maintain per application; in the final project, the asset management agent physically cannot read the loan tape.

### Exercise 8.3

**What the question asks.** Build, from the results of the tools a model called, a fact table, and check the answer’s figures against it with `check_text()`; test with the scripted answer and with an altered figure.

**The plan.** (1) Walk each JSON result and collect every number, named by its path. (2) Infer the unit from the key’s suffix. (3) Check the answer. (4) Alter one figure and check again.

**Step by step.**

`chapters/ch08/python/solutions/ex8_3_check_against_tools.py` (extract)

``` python
import json
from aie.factcheck import check_text

def facts_from_trace(trace):
    facts = {}
    def walk(obj, prefix):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{prefix}[{i}]")
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            unit = ("percent" if prefix.endswith("_pct") else
                    "money" if prefix.endswith("_gbp") else "number")
            facts[prefix] = (obj, unit)
    for name, _, result in trace:
        walk(json.loads(result), name)
    return facts

def check_answer_against_tools(answer, trace):
    return [(f.raw, hits) for f, hits in
            check_text(answer, facts_from_trace(trace))]
```

- The trace is the list of `(tool name, arguments, result)` filled by `ask_with_tools()`; each result is a JSON string.
- `walk()` is recursive: it goes into dictionaries and lists, and records each number under a path such as `pool_summary.arrears_ratio_pct`.
- `not isinstance(obj, bool)` is needed because Python treats `True` as the number 1.
- The unit comes from the key’s suffix: `_pct` is a percentage, `_gbp` money, anything else a plain number.

**Reading the result.** The two tools of the scripted run give 10 facts. For the scripted answer:

``` text
[('£274,056,424.22', ['note_balance.closing_gbp']), ('0.8432%', ['pool_summary.arrears_ratio_pct'])]
```

Both figures supported. With 0.8342%:

``` text
[('£274,056,424.22', ['note_balance.closing_gbp']), ('0.8342%', [])]
```

The transposed digits are caught.

**Checking the answer.** Print `facts_from_trace(trace)` and find the two values by eye: `note_balance.closing_gbp` is 274056424.22 and `pool_summary.arrears_ratio_pct` is 0.8432. The checker’s matches agree with what a person sees in the tool results.

**Mistakes to avoid.**

- Collecting facts from tools the model did **not** call. The check must compare the answer with what the model actually received.
- Using a flat walk that ignores lists: `arrears_buckets` returns its figures inside a list, and they would be lost.

**Trade-offs.** The fact table is built automatically from whatever tools the model called, so the check works for every question without writing facts by hand. It depends on the tools’ naming convention (`_gbp`, `_pct`): a small design decision with a large payoff, and a rule to enforce when anyone adds a tool. Chapter 9 turns this function into `facts_from_results()` in `aie/agent.py` and `aie_r/agent.R`.

### Exercise 8.4

**What the question asks.** Review a proposed tool, `send_investor_email(to, subject, body)`, and propose a design you would accept.

**The plan.** (1) Classify the tool with Figure 8.4 (read, compute, act). (2) List what can go wrong. (3) Write the decision. (4) Propose a safer design that keeps the benefit.

**Step by step.**

*Step 1 — Classification.* Sending an email changes the world outside the system: it is an **act** tool, and it is irreversible.

*Step 2 — What can go wrong.* A model error or a misunderstood question sends a wrong statement to an investor under the firm’s name. An instruction hidden in an incoming email (Exercise 6.4) could make the model send something nobody asked for. Investor communications are also subject to record-keeping and, for some content, to approval rules.

*Step 3 — The review.* *“Rejected as proposed. The assistant must not send external communications.”*

*Step 4 — The design to accept.* A *draft* tool, `draft_investor_reply(question, answer, citations)`, which stores a draft in a review queue. A person reads the draft with the checker’s report (figures supported, citations valid, no forbidden phrases), edits if necessary, and sends it from the normal email system.

**Reading the result.** The model still does the reading and writing, which is most of the time spent; the person keeps the decision and the accountability.

**Checking the answer.** Test the design against the two failure cases of Step 2. A wrong figure: the checker flags it in the draft’s report and the reviewer sees it before sending. An injected instruction: the draft tool can only write to the queue, so the worst outcome is a strange draft that a person discards.

**Mistakes to avoid.**

- Accepting the tool with a confirmation question in the prompt (*“ask before sending”*). The model can skip the question; the code must make sending impossible.
- Rejecting without an alternative. The colleague’s goal (answer investors faster) is legitimate; the review should keep it.

**Trade-offs.** Drafting saves most of the time and keeps the slowest step, approval, with a person. If volumes grow, shorten approval with better checks and templates for common questions, not by removing it.

### Exercise 8.5

**What the question asks.** List the interpretations a model could choose for the ambiguous question *“What was the balance in September?”*, and rewrite one tool description so that the model asks instead of guessing.

**The plan.** (1) List each tool and argument that fits the words. (2) Name the risk. (3) Rewrite `note_balance`’s description. (4) Back the change with the prompt and the evaluation.

**Step by step.**

*Step 1 — Interpretations.* *Balance* could be the pool balance (`pool_summary`), a class’s note balance (`note_balance`, but which class?), or the reserve fund balance (`waterfall_summary`). *September* could be `2026-09-30` or `2025-09-30`: two dates in the tape. Counting each note class separately, that is $(1 + 4 + 1) \times 2 = 12$ readings.

*Step 2 — The risk.* A model picks one reading silently, usually the most common in its training data, and answers with confidence. The answer can be correct for the reading it chose and wrong for the user.

*Step 3 — The description.*

*“Opening and closing balance, principal and interest paid, and coupon of ONE class (A, B, C or D) of Larkfield 2025-1 notes at a month-end. Use only when the user names the class and the date; if either is missing, ask the user instead of guessing.”*

*Step 4 — Prompt and evaluation.* Add to the system instructions: *“If a question can refer to several figures or dates, ask a short clarifying question.”* Add ambiguous questions to the evaluation set with the expected behaviour *asks for clarification*, scored like the not-in-document cases of Chapter 5.

**Reading the result.** With the new description, a good model replies: *“Which balance do you mean: the pool, one class of notes (A, B, C or D), or the reserve fund? And September 2025 or September 2026?”*

**Checking the answer.** Ask the question five times with the old description and five times with the new one, at different seeds, and count the clarifying questions. The change is useful only if the count rises; that count is what the evaluation case measures from then on.

**Mistakes to avoid.**

- Making every description say *ask if unsure*. The model then asks about clear questions too, and users stop using it.
- Relying on the description alone: descriptions guide, they do not enforce.

**Trade-offs.** Clarifying questions cost the user one more turn; wrong answers cost far more. Ask when the readings lead to different figures, as here; answer directly when the question is clear. The evaluation set is where you measure that balance.
