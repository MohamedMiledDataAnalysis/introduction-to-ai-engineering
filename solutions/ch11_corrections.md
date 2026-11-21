# 11. Asset Management: Asking the Fund Database in English

## Exercises

**Exercise 11.1.** Write the correct query for each of the five failures, and add one sentence to the schema description or the prompt rules that would have prevented each error.

**Exercise 11.2.** Prove that layer 4 works on its own: open a read-only connection to the database in Python and in R, and try to execute `DELETE FROM issuer_esg` directly, without `run_sql()`. What happens?

**Exercise 11.3.** The distributor-facing version of the assistant must not see transactions. Restrict the allowed tables accordingly, and show what the guard returns for S07.

**Exercise 11.4.** Write three new evaluation cases: one that needs a `GROUP BY`, one that needs a date other than the latest, and one that is ambiguous (for example *“What is the largest holding?”*, without a fund). Give the reference query for the first two, and the expected behaviour for the third.

**Exercise 11.5.** Run `ask_database()` with Ollama on the ten questions of the evaluation set and score the results with `same_result()`. Classify every failure with the categories of Figure 11.3.

## Corrections

### Exercise 11.1

**What the question asks.** For each of the five failed candidate queries (S01, S03, S04, S09, S10), write the correct query, then write one sentence for the schema description or the prompt rules that would have prevented the error.

**The plan.** (1) Compare each candidate with its reference and name the difference. (2) Correct the query and run it through `run_sql()`. (3) Compare with the reference result. (4) Write the preventing sentence, or explain why none is needed.

**Step by step.** For each failure, the correction and its effect:

| Case | Error in the candidate         | Correction                                               | Result                                    |
|------|--------------------------------|----------------------------------------------------------|-------------------------------------------|
| S01  | no date filter: sums 36 months | add `AND month_end='2026-09-30'`                         | 0.163154 (16.32%)                         |
| S03  | cash counted as a holding      | add `AND isin<>'CASH-EUR'` before `ORDER BY`             | first row Eastleigh Engineering, 0.041703 |
| S04  | plain average of durations     | `SUM(h.weight*s.modified_duration)/SUM(h.weight)`        | 5.8227 years                              |
| S09  | a second statement, `DELETE`   | keep only the first statement                            | 68.18                                     |
| S10  | join on the date only          | `ON n.month_end=b.month_end AND n.fund_code=b.fund_code` | 17 months                                 |

The S04 correction in full:

``` sql
SELECT SUM(h.weight * s.modified_duration) / SUM(h.weight)
FROM holdings h JOIN securities s ON h.isin = s.isin
WHERE h.fund_code = 'HECB' AND h.month_end = '2026-09-30'
```

- `h.weight * s.modified_duration` weights each bond’s duration by its share of the fund.
- Dividing by `SUM(h.weight)` rescales to the bonds only, so that the cash weight does not dilute the result.

*The preventing sentences.* For each failure, one sentence for the schema description or the prompt rules:

- S01: none needed; the rules already say *“use the latest month-end”*. The candidate ignored an existing rule.
- S03: *“‘Holdings’ means securities: exclude isin ‘CASH-EUR’ unless the question asks about cash.”*
- S04: *“Averages of security characteristics (duration, ESG score, spread) are weighted by holding weight.”*
- S09: none; the guard refuses it. Log it: a model producing a write statement is a signal to investigate the prompt and the inputs.
- S10: in the description of `benchmark_returns`: *“Join with nav on both month_end and fund_code.”*

**Reading the result.** All five corrected queries return the reference rows. The candidate errors are of four kinds: a missing filter (S01), a wrong population (S03), a wrong formula (S04, S10) and an unsafe statement (S09). Three of them call for a new sentence; S01 and S09 do not.

**Checking the answer.** Run each corrected query and compare with the reference using `same_result(run_sql(reference), run_sql(corrected), ordered)`: five `True`. Then check the meaning of S10’s wrong count: 49 is larger than the 36 months of data, which alone shows that the join duplicated rows (each HGEF month matched three benchmark rows, one per fund).

**Mistakes to avoid.**

- Fixing S09 by removing `DELETE` from the guard’s forbidden list. The guard did its job.
- Writing a sentence for every failure. S01 was already covered: the rules say *“use the latest month-end”*. The candidate ignored an existing rule; that is an evaluation failure to keep in the set, not a prompt gap.

**Trade-offs.** Each sentence makes the prompt longer and every call slightly dearer. Add sentences only for errors the evaluation shows, and re-run the evaluation after each addition: a new rule can break a case that passed.

### Exercise 11.2

**What the question asks.** Show that the read-only connection (layer 4) refuses a write by itself, without the text checks of `run_sql()`, in Python and R.

**The plan.** (1) Open the database read-only. (2) Execute a `DELETE` directly. (3) Read the error. (4) Confirm the table is unchanged.

**Step by step.**

`chapters/ch11/python/solutions/ex11_2_read_only.py`

``` python
import sqlite3
con = sqlite3.connect("file:data/am/harbourline.sqlite?mode=ro", uri=True)
try:
    con.execute("DELETE FROM issuer_esg")
except sqlite3.OperationalError as err:
    print("refused:", err)
```

- `file:...?mode=ro` is a URI that asks SQLite to open the file read-only; `uri=True` tells Python to interpret the string as a URI.
- `con.execute()` sends the statement straight to SQLite: no guard, no keyword check.
- SQLite raises `OperationalError`, caught and printed.

`chapters/ch11/r/solutions/ex11_2_read_only.R`

``` r
library(DBI); library(RSQLite)
con <- dbConnect(SQLite(), "data/am/harbourline.sqlite", flags = SQLITE_RO)
tryCatch(dbExecute(con, "DELETE FROM issuer_esg"),
         error = function(e) cat("refused:", conditionMessage(e), "\n"))
dbDisconnect(con)
```

- `flags = SQLITE_RO` opens the file read-only; `dbExecute()` runs a statement that returns no rows.

**Reading the result.** Both languages print:

``` text
refused: attempt to write a readonly database
```

**Checking the answer.** Count the rows afterwards: `SELECT COUNT(*) FROM issuer_esg` returns 96, the number before the attempt. The refusal happened before anything changed.

**Mistakes to avoid.**

- Opening the connection without `uri=True`: Python then creates a new file literally named `file:data/...?mode=ro`, writable, and the test proves nothing.
- Testing on a copy opened read-write by mistake: always print the error, never assume.

**Trade-offs.** Layer 4 does not depend on recognising dangerous text, so it also stops writes the guard would miss. Its cost is an extra connection configuration, and it protects only against writes: a read-only connection still lets a query read every table, which is why layers 2 and 3 (allowed tables) remain. In a production database the same guarantee comes from a database user with `SELECT` rights only, on views of the allowed tables.

### Exercise 11.3

**What the question asks.** Remove access to the `transactions` table for the distributor version of the assistant, and show what the guard returns for S07, which queries that table.

**The plan.** (1) List the allowed tables without `transactions`. (2) Run S07 through `run_sql()` with that list. (3) Remove the table from the prompt’s schema too. (4) Describe the database-side equivalent.

**Step by step.**

`chapters/ch11/python/solutions/ex11_3_distributor_tables.py` (extract)

``` python
DISTRIBUTOR_TABLES = {"funds", "securities", "holdings", "nav",
                      "benchmark_returns", "issuer_esg"}
print(run_sql(cands["S07"], allowed_tables=DISTRIBUTOR_TABLES))
```

- `allowed_tables` is checked against every table name that follows `FROM` or `JOIN` in the query, before execution.

**Reading the result.**

``` text
{'error': 'table not allowed: transactions'}
```

S07 (*“How many trades did the Global Equity Fund execute in September 2026, and what was their total notional?”*) is refused before reaching the database.

**Checking the answer.** Run S07 without `allowed_tables`: it returns 28 trades and €142,810,928.35. The only difference is the list, so the list caused the refusal.

**Mistakes to avoid.**

- Restricting the guard but leaving `transactions` in the schema description sent to the model. The model will keep writing queries against it, and every one will fail; users see errors instead of a clear *“not available”*.
- Restricting the prompt only. A model can still name a table it was not told about.

**Trade-offs.** Build the schema description for this application without the `transactions` line: a model that does not know a table exists will not query it, and the guard is the backstop. In production, add the third layer: a database user for the distributor application with access to views over the allowed tables only. Three layers cost three configurations to keep in step; one shared list of allowed tables, used to generate the prompt, the guard and the grants, keeps them consistent.

### Exercise 11.4

**What the question asks.** Write three evaluation cases: one needing `GROUP BY`, one using a past date, one ambiguous; give reference queries for the first two and the expected behaviour for the third.

**The plan.** (1) Write each question in a distributor’s words. (2) Write and run the reference query. (3) Decide ordered or unordered comparison. (4) For the ambiguous case, define how it is scored.

**Step by step.**

*A `GROUP BY` case.* *“What is the sector allocation of the Global Equity Fund?”*

``` sql
SELECT sector, SUM(weight) AS weight FROM holdings
WHERE fund_code='HGEF' AND month_end='2026-09-30'
GROUP BY sector
```

- `GROUP BY sector` gives one row per sector; `SUM(weight)` adds the weights of its holdings. Unordered comparison (`ordered = 0`): the order of sectors does not matter.

*A past date.* *“What was the net return of the Euro Corporate Bond Fund in March 2026?”*

``` sql
SELECT net_return FROM nav WHERE fund_code='HECB' AND month_end='2026-03-31'
```

The case tests that the model turns *March 2026* into the string `'2026-03-31'`.

*The ambiguous case.* *“What is the largest holding?”* names no fund. The expected behaviour is a clarifying question, not a query.

**Reading the result.** The first reference returns twelve rows, including *Cash* at 1.5% and Information Technology at 16.32% (S01’s figure). The second returns 0.014313, a net return of 1.43%.

**Checking the answer.** The twelve weights of the first query sum to 1.0, the whole fund. Decide whether the question means securities only: if so, add `AND isin<>'CASH-EUR'` and say so in the question (*“…excluding cash”*). For the second, check the value in `fund_nav_monthly.csv` for HECB at 2026-03-31: 0.014313.

**Mistakes to avoid.**

- Writing the March case with `month_end LIKE '2026-03%'`. It works on this database, but the reference should use the exact convention the model is asked to follow.
- Adding the ambiguous case without a way to score it. A case the scorer cannot judge is noise.

**Trade-offs.** The ambiguous case needs three changes:

- a column `expected_behaviour` with the value `clarify`;
- a prompt rule, *“If the question does not identify the fund, return {"clarify": "<question to the user>"} instead of SQL”*;
- the JSON schema `SQL_SCHEMA` in `aie/text_to_sql.py` widened to accept either key, with `ask_database()` returning the clarification instead of running a query.

More code, and one more kind of reply to handle in the application; in return, the assistant stops guessing a fund.

### Exercise 11.5

**What the question asks.** Run `ask_database()` with your model on the ten evaluation questions, score each result against the reference with `same_result()`, and classify every failure with Figure 11.3.

**The plan.** (1) Loop over the cases. (2) Run the model’s query and the reference query. (3) Compare results. (4) Classify each failure.

**Step by step.**

`chapters/ch11/python/solutions/ex11_5_live_sql_eval.py` (extract)

``` python
cases = pd.read_csv("evals/am_sql_qa.csv")
score = 0
for c in cases.itertuples():
    out = ask_database(c.question)
    ok = "result" in out and same_result(run_sql(c.reference_sql),
                                         out["result"], bool(c.ordered))
    score += ok
    if not ok:
        print(c.id, out.get("sql"), out.get("result", {}).get("error"))
print(score, "/", len(cases))
```

- `ask_database()` asks the model for one query, runs it through the guard, and retries once with the error message if it fails.
- `same_result()` compares rows, ignoring column names, rounding floats to six decimals; `ordered` says whether row order matters.
- For each failure, the query and any guard error are printed for classification.

**Reading the result.** A score out of 10 and, for each failure, the model’s SQL. Classify each with Figure 11.3: missing filter, cash included, unweighted average, extra statement, incomplete join, or a new category.

**Checking the answer.** For each failure, run the model’s query yourself and compare its rows with the reference’s, as in Exercise 11.1: the difference names the category. A failure whose category you cannot name is not yet understood.

**Mistakes to avoid.**

- Counting a query that the guard refused as a model *success* because it did no harm. It answered nothing.
- Ignoring new categories. They are the most valuable output of this exercise: add a rule and a case for each.

**Trade-offs.** With a small local model, simple lookups (S05, S06) pass; aggregations with conditions mostly pass after the rules of Exercise 11.1; weighted averages and two-key joins fail most often. Larger models make fewer of these errors at a higher cost per question; the evaluation tells you whether the difference justifies the cost for your users.
