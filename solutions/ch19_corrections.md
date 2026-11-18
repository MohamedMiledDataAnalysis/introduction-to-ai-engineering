# 19. Monitoring: Logs, Costs and Quality Over Time

## Exercises

**Exercise 19.1.** Find the first and last error of 7 October, count them by domain, and show that they share a duration close to 3.2 seconds. Explain the duration from Chapter 3.

**Exercise 19.2.** Replace the daily review-rate rule by a rolling five-working-day rule, in Python and R. On which day does it first fire for SF? Does it fire for AM?

**Exercise 19.3.** Write the incident note for Event 2: what happened, when, the evidence, the decision, and the follow-up actions.

**Exercise 19.4.** Plot or tabulate the AM average tokens by day. Fit a straight line and estimate the daily growth. At this rate, when would the AM prompt reach 8,000 tokens?

**Exercise 19.5.** The illustrative price is \$3.00 per million tokens. Compute October’s cost per domain and per caller, and estimate the cost of a year at October’s volumes. Then recompute with the AM tokens as they are on 26 October, held constant.

## Corrections

### Exercise 19.1

**What the question asks.** Find the first and last error of 7 October, count them by domain, show that their durations are close to 3.2 seconds, and explain that duration with Chapter 3.

**The plan.** (1) Keep the rows with status `error`. (2) Read the first and last timestamps and the count by domain. (3) Read the range of durations. (4) Relate the duration to the retry policy.

**Step by step.**

``` python
import sys; sys.path.insert(0, ".")
from aie.monitor import load_log
df = load_log("data/logs/requests_2026_10.jsonl")
err = df[df.status == "error"]
print(err.ts.min(), err.ts.max(), err.groupby("domain").size().to_dict())
print(err.seconds.min(), err.seconds.max())
```

- `load_log()` reads the JSON Lines file into a table and adds a `day` column.
- `err.groupby("domain").size()` counts errors per domain.

``` r
library(jsonlite)
df  <- stream_in(file("data/logs/requests_2026_10.jsonl"), verbose = FALSE)
err <- df[df$status == "error", ]
cat(min(err$ts), max(err$ts), "\n"); print(table(err$domain)); print(range(err$seconds))
```

**Reading the result.** The first error is at 14:28:15 on 7 October and the last at 17:53:23; 6 on SF and 13 on AM, 19 in total. Durations lie between 3.05 and 3.39 seconds.

**Checking the answer.** Relate the duration to `_post()` in `aie/llm.py` (Figure 3.3): with `retries=2` there are three attempts, with waits of $2^0 = 1$ and $2^1 = 2$ seconds between them and no wait after the last. Three fast connection refusals plus 3 seconds of waiting give 3.0 to 3.4 seconds. Reproduce it: stop Ollama and call `chat()` once; it raises `LLMError: cannot reach …` after the same time.

**Mistakes to avoid.**

- Reading the 19 errors as 19 incidents. A constant duration across all of them means one cause: every request went through the whole retry policy and failed at the same point, the model server being unreachable.
- Counting the errors in the review rate. An error is not an answer; the monitoring excludes errors from the review rate.

**Trade-offs.** Errors with varied durations would point elsewhere, for example timeouts on slow answers (durations near the timeout). Duration is a cheap diagnostic because the retry policy gives every failure mode its own signature. More retries would hide short outages from users at the cost of longer waits on long ones.

### Exercise 19.2

**What the question asks.** Replace the daily review-rate alert by a rolling five-working-day rate, in Python and R, find the first day it fires for SF, and check whether it fires for AM.

**The plan.** (1) Count flagged and answered requests per day. (2) Sum each over five working days. (3) Divide. (4) Compare with the 10% threshold.

**Step by step.**

``` python
ok = df[df.status != "error"]
def rolling_review(domain, window=5):
    x = ok[ok.domain == domain]
    flagged = x.groupby("day").status.apply(lambda s: (s != "verified").sum())
    total = x.groupby("day").size()
    return (flagged.rolling(window).sum() / total.rolling(window).sum()).round(3)
r = rolling_review("sf")
print(r[r > 0.10])
```

- `ok` excludes errors: the review rate is a share of answers.
- `flagged` counts answers not `verified` per day; `total` counts answers per day. The log has working days only, so five rows are five working days.
- `.rolling(5).sum()` adds each day and the four before it; dividing the two sums gives a rate weighted by volume, not an average of daily rates.

``` r
ok <- df[df$status != "error", ]
ok$day <- substr(ok$ts, 1, 10)
rolling_review <- function(domain, window = 5) {
  x <- ok[ok$domain == domain, ]
  flagged <- tapply(x$status != "verified", x$day, sum)
  total <- tapply(x$status != "verified", x$day, length)
  roll <- function(v) stats::filter(v, rep(1, window), sides = 1)
  setNames(round(as.numeric(roll(flagged) / roll(total)), 3), names(flagged))
}
r <- rolling_review("sf"); print(r[!is.na(r) & r > 0.10])
```

- `stats::filter(v, rep(1, 5), sides = 1)` sums each value with the four before it.

**Reading the result.** SF’s rolling rate rises from 4.2% on 7 October to 9.3% on 19 October, then crosses 10% on **20 October** (13.8%) and reaches 18.2% on 26 October. AM’s never crosses: its maximum is 9.9%.

**Checking the answer.** Compare with the daily rule. Daily SF alerts fired on 6, 12 and 14 October, before any change, and on every day from 19 October. The rolling rule keeps the sustained change and drops the three isolated days. Daily AM alerts fired on 6, 13, 14 and 15 October on 6 to 23 requests a day: noise that the rolling rule absorbs, though only just (9.9%).

**Mistakes to avoid.**

- Averaging the five daily rates: a day with 6 requests would weigh as much as a day with 23.
- Including the first four days: the window is incomplete and the rate is undefined (`NaN`), not low.

**Trade-offs.** A five-day window detects a sustained change one day late here (20 October for a change on the 19th), and misses a one-day problem entirely. AM’s 9.9% shows the threshold is a choice, not a law: one more flagged answer would have fired it. Keep a daily rule for errors, which are unambiguous, and the rolling rule for rates.

### Exercise 19.3

**What the question asks.** Write the incident note for the rise in SF reviews (Event 2): what happened, when, the evidence, the decision and the follow-up.

**The plan.** Use the headings of a standard incident note, and fill each with figures from the log.

**Step by step.** The evidence first:

``` python
sf = df[(df.domain == "sf") & (df.status != "error")]
print(sf.groupby("prompt").status.apply(lambda s: round((s != "verified").mean(), 3)))
print(sf.groupby("prompt").size())
```

which gives 6.3% on 268 answers with prompt `a41c2e09f7`, and 17.6% on 148 answers with `c7d03b51e2`.

The note:

- **What.** The share of SF answers needing review rose from 6.3% to 17.6%.
- **When.** From 19 October 2026, the release date of prompt `c7d03b51e2`; detected by the rolling alert on 20 October.
- **Evidence.** Review rate by prompt version (6.3% before, 17.6% after, on 268 and 148 answered requests); no change in model, volume or error rate over the period.
- **Impact.** About one SF answer in six needed an analyst’s review instead of one in sixteen; no unverified answer was sent to an investor, because `needs_review` answers go to the review queue.
- **Decision.** Roll back to prompt `a41c2e09f7` on 27 October.
- **Follow-up.** Add the real questions of 19 to 26 October that failed verification to the evaluation set; find why the new prompt passed its release evaluation; re-release only after the enlarged evaluation passes.

**Reading the result.** One page, every statement backed by a figure or a date from the log.

**Checking the answer.** Check that the evidence isolates the cause: group the review rate by `model` over the same days (one model, so no change), and by day for AM (no jump on 19 October). Only the prompt changed on that date. Without these two checks, the note would assert a cause it had not tested.

**Mistakes to avoid.**

- Writing *“the new prompt is worse”* without the counts. 17.6% on 148 answers is evidence; *worse* is an opinion.
- Ending the note at the rollback. The follow-up is what prevents the next incident.

**Trade-offs.** The evaluation of Chapter 5 is only as good as its cases; every incident the evaluation did not predict is a missing case. Writing the note takes an hour; skipping it means the same gap in the evaluation lets the next prompt through.

### Exercise 19.4

**What the question asks.** Tabulate AM’s average tokens per request by day, fit a straight line, estimate the daily growth, and project when the AM prompt reaches 8,000 tokens.

**The plan.** (1) Take the daily averages from `daily_metrics()`. (2) Turn days into a number. (3) Fit a line. (4) Solve for 8,000.

**Step by step.**

``` python
import numpy as np
from aie.monitor import daily_metrics
m = daily_metrics(df)
am = m[m.domain == "am"][["day", "avg_tokens"]].reset_index(drop=True)
am["t"] = (pd.to_datetime(am.day) - pd.Timestamp("2026-10-01")).dt.days
slope, intercept = np.polyfit(am.t, am.avg_tokens, 1)
print(round(slope, 1), round(intercept))
```

- `t` counts calendar days since 1 October, so weekends are gaps, not missing steps.
- `np.polyfit(x, y, 1)` fits $y = \text{slope} \times x + \text{intercept}$ by least squares.

In R: `coef(lm(avg_tokens ~ t, data = am))`.

**Reading the result.** The slope is 44.5 tokens per calendar day, from 1,794 tokens on 1 October. On 26 October the average is 2,982 tokens.

**Checking the answer.** The projection: $(8{,}000 - 2{,}982) / 44.5 = 112.8$ days after 26 October, which is 16 February 2027. Check the line against the data: $1{,}794 + 44.5 \times 25 = 2{,}907$ for 26 October, close to the observed 2,982; the line fits the trend.

**Mistakes to avoid.**

- Treating the projection as a forecast. It says what happens if nothing changes; its purpose is to make someone change something.
- Fitting on the request index instead of dates: days with more requests would stretch the axis.

**Trade-offs.** Long before February, latency and cost would have doubled again, and with an 8,000-token window (Chapter 2) answers would start to fail. Find the cause: compare a request of 1 October with one of 26 October in the access-controlled text store, and see what was added. Typical culprits are a conversation history that is never trimmed (Chapter 9) or a retrieval step whose $k$ grew. A straight line in the token count is the signature of something appended at every turn.

### Exercise 19.5

**What the question asks.** Compute October’s cost per domain and per caller at \$3.00 per million tokens, estimate a year at October’s volumes, then recompute with AM’s tokens held at their 26 October level.

**The plan.** (1) Sum tokens by domain and by caller, convert to dollars. (2) Scale October’s 18 working days to a year. (3) Rescale AM by the ratio of the 26 October average to the month’s average.

**Step by step.**

``` python
print((df.groupby("domain").tokens.sum() / 1e6 * 3).round(2))
print((df.groupby("caller").tokens.sum() / 1e6 * 3).round(2))
print(df.groupby("domain").tokens.mean().round(0))
```

- Tokens divided by one million, times the price per million, gives dollars.
- `tokens.mean()` gives the month’s average per request, used in step 3.

**Reading the result.** October: SF \$3.24, AM \$1.98, total \$5.22. In the simulated log each domain has one caller (`sf-shiny`, `am-shiny`), so the caller split is the same. A year at October’s volumes: October has 18 working days and a year about 252, so $5.22 \times 252 / 18 = \$73.11$. With AM held at 2,982 tokens per request instead of its month average of 2,274, AM costs $1.98 \times 2{,}982 / 2{,}274 = \$2.59$ a month, and the year becomes $(3.24 + 2.59) \times 14 = \$81.74$.

**Checking the answer.** Check the conversion on one figure: AM’s tokens summed to about 659,000 in October; $659{,}000 / 10^6 \times 3 = \$1.98$. And the year factor: $252 / 18 = 14$ months of October-sized activity.

**Mistakes to avoid.**

- Multiplying October by 12. October has 18 working days in this log; a calendar month averages 21.
- Holding the growth constant instead of the level. Held at the 26 October level, the cost is \$81.74; if the growth of Exercise 19.4 continued, it would be much higher.

**Trade-offs.** The numbers are small because the volumes are small; the method is what matters. At a firm with a thousand times the volume, the same drift is a budget line. Cost by caller needs the per-caller keys of Exercise 18.3: a small change in the service that makes every later cost question answerable.
