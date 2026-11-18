# 24. The Asset Management Application, and Your Next Steps

## Exercises

**Exercise 24.1.** Select the 3-year period. Write down the three tiles for each fund and explain why the warning matters more on this view.

**Exercise 24.2.** Replace the second draft by the first one in the Attribution tab. What does the check show, and does a draft that passes need a human review?

**Exercise 24.3.** Select HBMA on the Portfolio tab. Which characteristic would the AM agent quote incorrectly if its prompt did not explain the field names?

**Exercise 24.4.** Add an *Approve* button to the Attribution tab that is enabled only when every figure is OK. Write it, and test it with both drafts.

**Exercise 24.5.** Write the deployment checklist for putting both applications and the service on a shared server in your firm: at least six items.

## Corrections

### Exercise 24.1

**What the question asks.** Set the period to 3 years, write down the three tiles for each fund, and explain why the past-performance warning matters more on this view.

**The plan.** (1) Read the tiles for each fund. (2) Compare the relative returns with three years of charges. (3) Compare the 3-year and 1-year views of HGEF. (4) Relate the difference to the warning.

**Step by step.** Choose *3 years* in the sidebar and select each fund in turn. The tiles call `fund_performance(fund_code, 36)`, which compounds the last 36 monthly returns of the fund and of its benchmark.

**Reading the result.**

| Fund | Fund return | Benchmark | Relative |
|------|------------:|----------:|---------:|
| HGEF |      −2.74% |    −1.07% |   −1.68% |
| HECB |       9.20% |    10.49% |   −1.29% |
| HBMA |       3.99% |     4.65% |   −0.66% |

All three funds are behind their benchmarks over three years. Over one year HGEF returned 6.46%; over three years, −2.74%.

**Checking the answer.** Compare each gap with three years of ongoing charges, since fund returns are net of fees and benchmark returns are not: HECB’s gap, −1.29%, is close to $3 \times 0.40\% = 1.20\%$; HGEF’s, −1.68%, is smaller than $3 \times 0.75\% = 2.25\%$, so before fees HGEF was ahead of its benchmark over the period; HBMA’s, −0.66%, is smaller than $3 \times 0.60\% = 1.80\%$. The figures are consistent with what each fund charges.

**Mistakes to avoid.**

- Reading the relative return as the manager’s skill without the fees. Part of every gap is the charge, which the investor pays whatever the manager does.
- Adding the three 1-year returns to get the 3-year figure: returns compound.

**Trade-offs.** The two periods give opposite impressions of the same fund, which is exactly why the warning exists: a single period’s return, good or bad, does not predict the next. Client documents go further: under PRIIPs, past performance is published for up to the last ten calendar years in a fixed format. A 1-year/3-year toggle is an internal view, convenient for specialists, not a client document.

### Exercise 24.2

**What the question asks.** Show the first draft in the Attribution tab instead of the second, read the check, and decide whether a draft that passes still needs a person’s review.

**The plan.** (1) Change one line of the app. (2) Read the check table. (3) Find what the check cannot see. (4) Decide.

**Step by step.** In `apps/am_app/app.R` change

``` r
draft <- drafts[2]
```

to `draft <- drafts[1]`. The file `evals/drafts/hgef_commentary_2026_09.txt` holds the two drafts of Chapters 6 and 13, separated by `DRAFT 1` and `DRAFT 2`; `drafts` is the list split on those markers.

**Reading the result.** The check table for Draft 1: 4.53% fund return OK, 5.03% benchmark return OK, 13.7bp Real Estate effect OK (*detracted*, and the effect is −13.7bp), 7.8bp Materials effect OK, 4.8bp Consumer Discretionary effect OK. Five figures, no problem.

**Checking the answer.** The check verifies figures, their labels and their directions. Draft 1 also makes two claims without figures, which only a person can check against the attribution file: *“Stock selection and sector allocation both detracted”* (the column totals are −26.2bp and −14.9bp: true) and Consumer Discretionary *“helped by stock selection”* (its selection effect is +4.55bp: true). Both are supported, but by the reviewer, not by the code.

**Mistakes to avoid.**

- Approving a draft because the table shows five OKs. The table covers figures, not the sentences around them.
- Concluding that the check is useless because a person still reads the draft. It reduced the review from every figure to two sentences.

**Trade-offs.** Yes, a passing draft still needs a review, a shorter one. To shrink it further, apply Exercise 13.2: give the model the totals as figures (*“selection detracted 26.2bp”*) so that more claims become checkable, at the price of a denser commentary. The approval then focuses on tone and on the claims no figure can carry.

### Exercise 24.3

**What the question asks.** On the Portfolio tab, select HBMA, and identify the characteristic the AM agent would quote incorrectly if its prompt did not explain field names.

**The plan.** (1) Read HBMA’s characteristics. (2) Find the fields that describe part of the fund. (3) Write the wrong and the right sentence. (4) Fix the prompt and the evaluation.

**Step by step.** The Characteristics table calls `fund_characteristics("HBMA")` through `run_tool()` and prints each field.

**Reading the result.** HBMA: 45 holdings, 5.0% cash, weighted ESG score 72.4, weighted carbon intensity 116.4, bond modified duration 6.11 years, BBB share of bonds 60.49%.

**Checking the answer.** HBMA holds 55% equities, 40% bonds and 5% cash (Exercise 22.1). `bond_modified_duration_years` (6.11) is the duration of the 40%; `bbb_share_of_bonds_pct` (60.49%) is a share of the bonds, which is $0.6049 \times 40\% = 24.2\%$ of the fund. An agent writing *“HBMA has a duration of 6.11 years”* or *“60% of HBMA is rated BBB”* gives a correct figure with a wrong meaning, and the figure check passes, because the value is in the tool result.

**Mistakes to avoid.**

- Relying on the figure check for meaning: it checks values and labels, not what the label covers.
- Fixing it by renaming the fields only. A longer name helps; the model can still drop words when it writes.

**Trade-offs.** The fix is in two places: a sentence in the system prompt (*“For HBMA, duration and rating shares refer to the bond part of the fund only; say so.”*) and an evaluation case, *“What share of HBMA is rated BBB?”*, whose keywords require *bonds*. A meaning error cannot be caught by figures; it is caught by a test written by someone who knows the domain. The tool could instead return the BBB share of the fund (24.2%) as well; one more field, one less misreading.

### Exercise 24.4

**What the question asks.** Add an *Approve* button to the Attribution tab that is enabled only when every figure of the draft is OK, and test it with both drafts.

**The plan.** (1) Add a placeholder for the button in the UI. (2) Compute whether the check passed. (3) Render the button enabled or disabled. (4) Test with each draft in `testServer()`.

**Step by step.** In the UI, add `uiOutput("approve_ui")` to the card of the draft and its check. In the server:

``` r
check_ok <- reactive({
  r <- check_commentary(draft, hf$facts)
  length(r) > 0 && all(vapply(r, function(x) is.na(x$problem), TRUE))
})
output$approve_ui <- renderUI({
  b <- actionButton("approve", "Approve commentary", class = "btn-success")
  if (check_ok()) b else tagAppendAttributes(b, disabled = "disabled")
})
```

- `check_commentary()` returns one entry per figure, with `problem` set to `NA` when the figure is supported.
- `vapply(..., TRUE)` turns the entries into a logical vector; `all()` is `TRUE` only if every figure is supported.
- `length(r) > 0` refuses a draft with no figures at all: in R, `all(logical(0))` is `TRUE`.
- `tagAppendAttributes(b, disabled = "disabled")` adds the HTML attribute that greys out the button.

**Reading the result.** With Draft 2 (two errors), the button is disabled; with Draft 1, it is enabled.

**Checking the answer.** In `testServer()`, read `check_ok()` and look for `disabled` in the rendered HTML:

``` r
testServer(app, cat(check_ok(), grepl("disabled", as.character(output$approve_ui$html)), "\n"))
```

Draft 2 prints `FALSE TRUE`; Draft 1 prints `TRUE FALSE`.

**Mistakes to avoid.**

- Forgetting the empty case: a commentary without a single figure would be approvable automatically.
- Checking the draft once when the app starts and never again. In production the draft changes; the check must be a reactive expression of the current draft.

**Trade-offs.** A disabled button is guidance, not control: anyone can copy the text. The control is the record: when *Approve* is clicked, write the draft, the check results, the approver and the time to a log, as Chapter 20 requires. Approval then means that a named person took responsibility for the sentences the code could not check.

### Exercise 24.5

**What the question asks.** Write the checklist for deploying both applications and the service on a shared server in your firm, with at least six items.

**The plan.** Cover six areas in turn: access, data, versions, monitoring, resilience, governance; then decide what a pilot needs.

**Step by step.**

1.  **Access.** The applications behind the firm’s single sign-on; the service reachable only from the applications’ server; one API key per caller (Exercise 18.3), stored as secrets, never in the repository.
2.  **Data.** Data folders mounted read-only; client or personal data only after the DPIA of Chapter 20 is approved; the model in the firm’s environment (Ollama on an internal server) or an external API covered by the firm’s contract and data agreement.
3.  **Versions.** Each deployment tagged in Git, with the prompt hashes and the model name recorded in the model card; the evaluation re-run on the deployed configuration before go-live, with its results attached.
4.  **Monitoring.** The JSONL log collected centrally; the alerts of Chapter 19 (error rate above 2%, review rate above 10% over five working days, p95 latency above 12 seconds) sent to a named owner.
5.  **Resilience.** Health checks on `/health`; the applications’ deterministic tabs tested with the service stopped (Exercise 23.3); a restart policy for the service and the model server.
6.  **Governance.** Both use cases in the AI inventory with owners; the risk tier agreed with the second line; a review date in the calendar.

**Reading the result.** Six items, each with an owner who can say *done* or *not done*.

**Checking the answer.** Walk one failure through the list: the model server stops on a Monday morning. Resilience restarts it; monitoring raises the error-rate alert to its owner; the applications’ dashboards keep working; versions tell support which model and prompt were running. Each item has a role in a real failure.

**Mistakes to avoid.**

- Copying the development API key to the server: it is in the book and in the repository’s defaults.
- Leaving the working directory to chance: `runApp()` and plumber change it, which is why both apps and the R service set it from `AIE_ROOT` (Chapter 23).

**Trade-offs.** Each item adds work before the first user sees the application. The minimum for a pilot with five named users is access control, the log and the evaluation; the rest must be in place before the application is opened more widely, and the governance file must say which stage you are in.
