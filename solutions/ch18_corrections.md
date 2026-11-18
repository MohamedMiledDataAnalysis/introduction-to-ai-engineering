# 18. Serving: From a Script to a Service

## Exercises

**Exercise 18.1.** Add an endpoint `GET /tools/fund_performance?fund_code=HGEF&months=12` to the R service, and test it with `curl`.

**Exercise 18.2.** FastAPI documents the service automatically at `http://localhost:8000/docs`. Open it, read the description of `/sf/ask`, and use the page to send a question. What does the page show when the question is two characters long?

**Exercise 18.3.** Replace the single API key by a dictionary of keys per caller, `{"sf-shiny": "...", "am-shiny": "..."}`, read from an environment variable, and record the caller’s name in every log line.

**Exercise 18.4.** Measure the service: send the same question 20 times and report the median and the maximum time. Where does the time go?

**Exercise 18.5.** A colleague wants to expose the service on the internet so that clients can ask questions directly. List what must be true before that can happen.

## Corrections

### Exercise 18.1

**What the question asks.** Add to the R service an endpoint that returns a fund’s performance, `GET /tools/fund_performance?fund_code=HGEF&months=12`, and test it with `curl`.

**The plan.** (1) Copy the structure of the existing `/tools/pool_summary` endpoint. (2) Convert the query parameters to the types the tool’s schema requires. (3) Return the tool’s result, or a 400 with its error. (4) Test a valid and an invalid call.

**Step by step.** Add to `services/r/plumber.R`:

``` r
#* @get /tools/fund_performance
#* @serializer unboxedJSON
function(fund_code, months, res) {
  owd <- setwd(root); on.exit(setwd(owd))
  out <- fromJSON(run_tool(list(name = "fund_performance",
    arguments = list(fund_code = fund_code, months = as.integer(months)))),
    simplifyVector = FALSE)
  if (!is.null(out$error)) { res$status <- 400; return(list(detail = out$error)) }
  out
}
```

- The comments starting with `#*` are plumber’s annotations: the method and path, and the serializer that writes single values without brackets.
- `fund_code` and `months` are read from the query string by name.
- `setwd(root)` with `on.exit()` runs the request from the repository root, where the data is, and restores the folder afterwards.
- `as.integer(months)`: query parameters always arrive as text, and the tool’s schema requires an integer.
- `run_tool()` goes through the dispatcher, so the schema is checked; an error becomes HTTP 400 with the message.

Restart the service:

``` bash
Rscript -e 'plumber::pr_run(plumber::pr("services/r/plumber.R"), port = 8001)'
```

**Reading the result.**

``` bash
curl -H "x-api-key: dev-key-change-me" \
  "localhost:8001/tools/fund_performance?fund_code=HGEF&months=12"
```

``` text
{"fund_code":"HGEF","period_months":12,"period_end":"2026-09-30","fund_return_pct":6.4592,
 "benchmark_return_pct":7.8601,"relative_return_pct":-1.4009}
```

The 12-month figures of Chapter 8: fund 6.4592%, benchmark 7.8601%, relative −1.4009%.

**Checking the answer.** Test the error path with `months=6`: status 400 and `{"detail":"invalid arguments: 'months' = '6' is not one of 1, 3, 12, 36"}`. The schema rejected the value before the function ran, and the caller learns which values are valid. Remove `as.integer()` and call with `months=12`: 400, *‘months’ has type character, expected integer*. That is why the conversion is there.

**Mistakes to avoid.**

- Calling the tool function directly instead of `run_tool()`: the schema check and the allow-list are skipped.
- Forgetting the API key header: the filter answers 401 before the endpoint runs.

**Trade-offs.** One endpoint per tool is explicit and easy to document, but every new tool needs new code in two services. The Python service uses a single `GET /tools/{name}` endpoint with optional parameters: less code, a less precise contract. For a handful of tools, explicit endpoints are clearer; for dozens, a generic endpoint driven by each tool’s schema is easier to maintain.

### Exercise 18.2

**What the question asks.** Open FastAPI’s generated documentation, read the description of `/sf/ask`, send a question from the page, and see what happens with a two-character question.

**The plan.** (1) Start the Python service. (2) Open `/docs`. (3) Send a valid question. (4) Send a question of two characters and read the response.

**Step by step.**

``` bash
uvicorn services.python.app:app --port 8000
```

Open `http://localhost:8000/docs`. FastAPI builds this page from the code: the `Question` class appears with its two fields, from

``` python
class Question(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    user: str = Field(default="anonymous", max_length=100)
```

Click *Try it out* on `POST /{domain}/ask`, enter `sf` as `domain`, `dev-key-change-me` as `x-api-key`, and a question.

**Reading the result.** A valid question returns 200 with the answer, the status and the tools used. A two-character question (*“Hi”*) returns **422**:

``` text
{"detail": [{"type": "string_too_short", "loc": ["body", "question"],
             "msg": "String should have at least 3 characters", ...}]}
```

**Checking the answer.** Confirm that the model was not called: with Ollama stopped, the two-character question still returns 422 (validation), whereas a valid question returns 503 (the model is unavailable). Validation happens before any cost is incurred.

**Mistakes to avoid.**

- Testing on the docs page without the API key: every call returns 401, which hides the validation.
- Writing a separate document describing the API by hand: it will drift from the code.

**Trade-offs.** The generated documentation cannot drift from the code, because it is the code. Share the `/docs` address with the teams that build callers; it is the contract. The limits (3 to 2,000 characters) are a product decision: 2,000 characters keeps prompts and costs bounded, at the price of refusing very long questions, which are rare and usually better split.

### Exercise 18.3

**What the question asks.** Replace the single API key by one key per caller, read from an environment variable, and record the caller’s name in every log line.

**The plan.** (1) Read a JSON dictionary of keys. (2) Turn the key check into a dependency that returns the caller’s name. (3) Use the name in the endpoint and the log. (4) Test with two keys and a wrong one.

**Step by step.**

``` python
import json
KEYS = json.loads(os.environ.get("AIE_API_KEYS", '{"dev": "dev-key-change-me"}'))
CALLER_BY_KEY = {v: k for k, v in KEYS.items()}

def caller(x_api_key: str = Header(default="")):
    if x_api_key not in CALLER_BY_KEY:
        raise HTTPException(status_code=401, detail="invalid API key")
    return CALLER_BY_KEY[x_api_key]

@app.post("/{domain}/ask")
def ask(domain: str, q: Question, who: str = Depends(caller)):
    ...
    log_event(request_id=request_id, caller=who, domain=domain, ...)
```

- `AIE_API_KEYS` holds, for example, `{"sf-shiny": "…", "am-shiny": "…"}`; the default keeps the development key working.
- `CALLER_BY_KEY` inverts the dictionary: from a key to the caller’s name.
- `caller()` is a FastAPI dependency: it runs before the endpoint, refuses unknown keys with 401, and returns the name, which FastAPI passes to the endpoint as `who`.
- `log_event(..., caller=who)` adds the name to every log line.

**Reading the result.** With `AIE_API_KEYS='{"sf-shiny": "k1", "am-shiny": "k2"}'`: key `k1` is accepted as `sf-shiny`, `k2` as `am-shiny`, and any other key gets `401 invalid API key`.

**Checking the answer.** Send one question with each key and read `logs/requests.jsonl`: each line carries `"caller": "sf-shiny"` or `"caller": "am-shiny"`. Revoke `k2` by removing it from the variable and restarting: the AM application gets 401, the SF application keeps working.

**Mistakes to avoid.**

- Keeping the keys in the repository, even in an example file with real values.
- Logging the key itself: a log file then becomes a list of credentials. Log the caller’s name.

**Trade-offs.** Per-caller keys let you revoke one caller without affecting the others, and let the monitoring of Chapter 19 report costs per caller. They are still shared secrets: anyone with the application’s key is that application. Keep them in an environment variable set by the deployment, or a secrets manager; rotate them on a schedule and when someone with access leaves. For named human users, use the firm’s single sign-on instead.

### Exercise 18.4

**What the question asks.** Send the same question to the service 20 times, report the median and the maximum time, and explain where the time goes.

**The plan.** (1) Time 20 identical requests. (2) Compute median and maximum. (3) Read the service’s log and the trace to split the time. (4) Use the figures for timeouts.

**Step by step.**

``` python
import statistics, time, requests
BASE, KEY = "http://localhost:8000", {"x-api-key": "dev-key-change-me"}
times = []
for _ in range(20):
    t = time.perf_counter()
    requests.post(f"{BASE}/sf/ask", json={"question":
        "What was the arrears ratio at 30 September 2026?"}, headers=KEY,
        timeout=600)
    times.append(time.perf_counter() - t)
print(f"median {statistics.median(times):.2f} s, max {max(times):.2f} s")
```

- `time.perf_counter()` is a precise clock for durations.
- The median is the typical wait; the maximum is the worst one in the sample.

**Reading the result.** The figures depend on your computer and model. The pattern does not: the first request is the slowest, and the others cluster around the median.

**Checking the answer.** Compare with the service’s own measurement: each log line has `seconds`. The client’s time is slightly larger (network and serialisation), and the order of requests is the same. Then time one tool alone: `run_tool({"name": "pool_summary", ...})` takes tens of milliseconds, except the first call, which reads the tape into memory (the `lru_cache` of `aie/tools.py` keeps it afterwards).

**Mistakes to avoid.**

- Reporting the mean: one slow cold start inflates it.
- Setting the caller’s timeout from the median: users then see errors on every cold start.

**Trade-offs.** Almost all the time is model calls: with a local model each step takes one to several seconds, and a question needs two or three steps. A larger model answers better and slower; a smaller one faster and less accurately. Report the median for users’ experience and the maximum for timeouts, and make the evaluation of Chapter 5 and these timings the two inputs of the choice.

### Exercise 18.5

**What the question asks.** List what must be true before the service can be exposed on the internet for clients to ask questions directly.

**The plan.** Go through four areas: security, regulation, controls, data; then conclude who decides.

**Step by step.**

- **Security.** Proper authentication of each client (not a shared key), encryption (HTTPS), rate limits per client, protection against prompt injection in questions (Chapter 6), and a security review.
- **Regulation.** Answers to clients about investments are financial communications: they must be fair, clear and not misleading, and some may count as advice. Compliance must approve the use case, the wording rules and the record-keeping.
- **Controls.** No answer with status `needs_review` reaches a client; a person approves until the evaluation (Chapter 5) shows that the error rate is acceptable for the use; complaints and errors have an owner.
- **Data.** Clients see only what they are entitled to; the agents’ tools must be scoped to each client’s products.

**Reading the result.** Exposing the service internally is an engineering task. Exposing it to clients is a business decision with legal consequences, made by the firm with compliance and risk, after the evidence of Chapters 5, 19 and 20.

**Checking the answer.** Test the list against one realistic failure: a client asks *“Should I sell my Class B notes?”*. Security does not stop it; the advice guard of Chapter 21 does (control), and compliance’s rules decide what the refusal says (regulation). Every item of the list is needed for at least one plausible failure.

**Mistakes to avoid.**

- Treating the list as a checklist to complete before launch day. Several items (approval rates, complaint handling) need months of evidence.
- Assuming the internal evaluation applies to clients: their questions differ from analysts’. Build a new evaluation set from their questions.

**Trade-offs.** Each control slows the launch and reduces what the service can do for clients; each control removed transfers risk to clients and to the firm. A common path is staged: internal use, then client-facing drafts approved by staff, then direct answers for a narrow set of questions whose error rate is measured and low.
