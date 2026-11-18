# 23. The Structured Finance Application in R Shiny

## Exercises

**Exercise 23.1.** Add a fifth tile, *Reserve fund*, to the dashboard. Which field of `month_figures()` do you use, and what does the tile show for 30 September 2026?

**Exercise 23.2.** Select the interest payment date 31 March 2026. Write down the four tiles and explain the arrears ratio by reference to Chapter 14.

**Exercise 23.3.** Start the application in mode 2 with no service running. What does the user see when asking a question, and what do the other tabs do? Write the test.

**Exercise 23.4.** Add a review queue: every answer with status `needs_review` is appended to `logs/review_queue.csv` with the time, the question, the answer and the unsupported figures.

**Exercise 23.5.** A colleague proposes to fill the dashboard tiles by asking the agent *“What is the pool balance?”* and displaying its answer. Give three reasons against.

## Corrections

### Exercise 23.1

**What the question asks.** Add a fifth tile, *Reserve fund*, to the dashboard, say which field of `month_figures()` it uses, and give its value for 30 September 2026.

**The plan.** (1) Find the field. (2) Add an output placeholder in the UI. (3) Fill it in the server from the existing reactive expression. (4) Test it with `testServer()`.

**Step by step.**

*Step 1 — The field.* `names(month_figures("2026-09-30"))` lists `reserve`: the reserve fund balance after the month’s waterfall, in pounds.

*Step 2 — The UI.* In the Dashboard’s `layout_columns(...)`, add a fifth box:

``` r
value_box("Reserve fund", textOutput("kpi_reserve"))
```

- `value_box()` (from `bslib`) draws a tile with a title and a value; `textOutput("kpi_reserve")` reserves the place the server will fill.

*Step 3 — The server.*

``` r
output$kpi_reserve <- renderText(gbp(figures()$reserve / 1e6, 2) |> paste0("m"))
```

- `figures()` is the reactive expression already used by the other tiles, so no new computation runs when the date changes.
- `gbp(x, 2)` formats pounds with two decimals and thousands separators; dividing by one million and adding *m* matches the other tiles.

**Reading the result.** The tile shows **£6.08m**: the Reserve Fund Required Amount of £6,082,667.80 (1.50% of the pool at the cut-off date, Chapter 3), which does not amortise and has never been drawn.

**Checking the answer.** Add to `tests/test_sf_app.R`, inside `testServer()`:

``` r
stopifnot(output$kpi_reserve == "£6.08m")
```

and run the test. Change the date to 2026-03-31: the tile still shows £6.08m, as it must for a reserve that was never drawn.

**Mistakes to avoid.**

- Calling `month_figures()` again inside the new `renderText()`: it works, but it doubles the work at every date change.
- Running the test in a session whose locale is not UTF-8: the pound sign then prints as `<U+00A3>` and the comparison fails. Run with `LANG=C.UTF-8`, or compare without the sign.

**Trade-offs.** Five tiles of equal width are narrower: on a laptop screen the amounts wrap onto two lines. Shorten the labels or drop the decimals. A tile is read in a second: choose fewer, clearer tiles over more. A reserve that never moves may be better as a line in the reconciliation table than as a tile.

### Exercise 23.2

**What the question asks.** Select 31 March 2026, write down the four tiles, and explain the arrears ratio with Chapter 14.

**The plan.** (1) Select the date. (2) Read the tiles. (3) Explain the ratio from the tape. (4) Cross-check with the Investor report tab.

**Step by step.** Select 2026-03-31 in the sidebar. The tiles are computed by `month_figures("2026-03-31")`; the trend chart is unchanged, since it shows every date.

**Reading the result.** Pool balance **£352.87m**, arrears ratio **1.80%**, CPR **16.8%**, Class A balance **£304.20m**. The three reconciliation checks pass.

The trend chart shows the arrears ratio rising from 0.50% at the first interest payment date (31 July 2025) to its peak of 1.80% on 31 March 2026, then falling. Exercise 14.3 traced what became of the 34 loans in arrears in March: 16 returned to performing, 7 were restructured with no arrears, 8 defaulted, 2 redeemed and 1 remained in arrears. Cures and defaults both remove loans from the arrears buckets, which is why the ratio fell to 0.84% by September, less than half its peak.

**Checking the answer.** Open the Investor report tab for March: the template commentary reads *“The arrears ratio rose to 1.80% from 1.74%”*. The same figures, from the same function, in words. In `testServer()`, `session$setInputs(date = "2026-03-31")` gives `output$kpi_arrears == "1.80%"`.

**Mistakes to avoid.**

- Comparing tiles across dates by memory: March’s CPR of 16.8% is higher than September’s 14.8%. Read each tile against its own history on the trend chart.
- Concluding from the tile alone that the deal improved after March. A falling arrears ratio is good news only when cures, not defaults, explain it.

**Trade-offs.** The dashboard shows *what* the figures are; the explanation (cures versus defaults) needed the loan-level analysis of Chapter 14. Adding a *cumulative defaults* tile would put both sides on screen, at the cost of a sixth tile; a better place may be a line under the trend chart.

### Exercise 23.3

**What the question asks.** Start the application in mode 2 with no service running: what does the user see when asking a question, and what do the other tabs do? Write the test.

**The plan.** (1) Point the application at an address where nothing listens. (2) Ask a question and follow `ask_agent()`. (3) Check the other tabs. (4) Write a `testServer()` test of both.

**Step by step.**

``` bash
AIE_SERVICE_URL=http://127.0.0.1:9 Rscript -e 'shiny::runApp("apps/sf_app", port = 8101)'
```

When the user asks, `ask_agent()` builds the request and `httr2::req_perform()` fails with *connection refused*; `tryCatch` returns `NULL`; the function returns the fall-back result:

``` r
list(answer = "The assistant is unavailable; the figures on the dashboard remain available.",
     status = "error", trace = list(), unsupported = character(0))
```

**Reading the result.** The Assistant tab shows that sentence with a red *error* badge. The Dashboard, Data quality and Investor report tabs work normally: they never call the service.

**Checking the answer.**

``` r
library(shiny)
Sys.setenv(AIE_ROOT = getwd(), AIE_SERVICE_URL = "http://127.0.0.1:9")
app <- source("apps/sf_app/app.R")$value
testServer(app, {
  session$setInputs(date = "2026-03-31")
  stopifnot(output$kpi_arrears == "1.80%")                       # dashboard works
  session$setInputs(question = "What was the arrears ratio in September 2026?", ask = 1)
  stopifnot(log()[[1]]$r$status == "error")                      # assistant fails gracefully
})
```

- `Sys.setenv()` must come **before** `source()`: the file reads `AIE_SERVICE_URL` when it is loaded.
- `session$setInputs(ask = 1)` simulates a click on *Ask*.

Both conditions hold.

**Mistakes to avoid.**

- Testing with the variable set after sourcing the app: the app stays in mode 1 and the test passes for the wrong reason.
- Showing the HTTP error to the user. *Connection refused* means nothing to an analyst.

**Trade-offs.** The error sentence does not say *why* the assistant is unavailable. For the analyst, that is right: they cannot fix the service. For the support team, the reason must be logged; add `message(conditionMessage(e))` in the `error` handler of `tryCatch` so that it appears in the application’s log.

### Exercise 23.4

**What the question asks.** Add a review queue: every answer with status `needs_review` is appended to `logs/review_queue.csv` with the time, the question, the answer and the unsupported figures.

**The plan.** (1) Find where the answer’s status is known: the `observeEvent(input$ask, ...)` observer. (2) Append one row per such answer. (3) Test it with a scripted model that produces an unsupported figure.

**Step by step.** In the observer, after `r` is known:

``` r
if (identical(r$status, "needs_review")) {
  dir.create("logs", showWarnings = FALSE)
  row <- data.frame(time = format(Sys.time(), "%Y-%m-%dT%H:%M:%S"), question = input$question,
                    answer = r$answer, unsupported = paste(r$unsupported, collapse = "; "))
  f <- "logs/review_queue.csv"
  write.table(row, f, sep = ",", row.names = FALSE, col.names = !file.exists(f), append = file.exists(f))
}
```

- `identical()` is safe even if `status` is missing.
- `col.names = !file.exists(f)` writes the header only the first time; `append = file.exists(f)` adds to an existing file.
- `write.table()` quotes text fields, so answers containing commas stay in one column.

**Reading the result.** The script `tools/scripts/ch23_review.json` replays a model that calls `arrears_buckets` and then writes £1,098,476.03 instead of £1,088,476.03, twice: the answer and the one correction of Chapter 9. With the mock started on that script and the question *How many loans were two months in arrears at 30 September 2026?* in `testServer()`:

**What you should see**

``` text
needs_review | £1,098,476.03
[1] 1
[1] "£1,098,476.03"
```

One row, with the unsupported figure.

**Checking the answer.** Read the queue: `nrow(read.csv("logs/review_queue.csv")) == 1`. Then ask a guarded question (*“Should I buy the Class B notes?”*): status `declined`, no new row. Only `needs_review` answers enter the queue.

**Mistakes to avoid.**

- Writing the queue inside the repository’s tracked files. `logs/` is in `.gitignore`: review data does not belong in Git.
- Queueing `error` answers too: they contain no draft to review.

**Trade-offs.** A CSV file is enough for one analyst. With several users on one server, two sessions can append at the same moment and corrupt a line; use the service’s JSONL log (one line per write) or a database table instead. A typo of one digit, caught by verification and routed to a person, is exactly what the queue is for.

### Exercise 23.5

**What the question asks.** A colleague proposes filling the dashboard tiles by asking the agent *“What is the pool balance?”* and showing its answer. Give three reasons against.

**The plan.** Compare the two ways of producing a tile on cost, risk and availability, then state the rule.

**Step by step and reading the result.**

1.  **Cost and speed.** Each tile would cost a model call, several seconds and tokens, at every date change; `month_figures()` takes under a second and costs nothing.
2.  **Risk.** A deterministic function returns the right figure every time; the agent returns it *most* of the time, and the evaluation of Chapter 21 measures how often. A dashboard read by investors’ analysts cannot be right most of the time.
3.  **Availability.** The dashboard would be empty whenever the model is down, which Exercise 23.3 showed it is not today.

**Checking the answer.** Measure reason 1: time `month_figures("2026-09-30")` (under a second in R, including reading the files) and one agent answer to *“What is the pool balance at 30 September 2026?”* with your model (several seconds, plus tokens). Four tiles mean four calls per date change.

**Mistakes to avoid.**

- Accepting the proposal for *“just one tile”*. The same three reasons apply to one tile.
- Rejecting it without saying where the model *does* belong in the application.

**Trade-offs.** The rule: use the model where language is the task (questions in words, drafting); use code where the answer is a figure that code can compute. The agent itself follows this rule: it calls the same functions. The colleague’s idea has one merit, a single source of truth for figures, and the application already has it: the tiles and the agent call the same functions.
