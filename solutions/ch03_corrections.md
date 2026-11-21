# 3. Calling a Model from Code

## Exercises

**Exercise 3.1.** Run `ch03_cost.py` (or `ch03_cost.R`). Then change the assumptions: 2,000 questions a month, 6,000 input tokens per question (eight passages instead of three) and 500 output tokens. What is the yearly cost with the large paid model? Which change contributed most?

**Exercise 3.2.** Start the mock with `MOCK_FAIL_FIRST=2` (on Windows PowerShell: `$env:MOCK_FAIL_FIRST=2; python tools/mock_ollama.py`). Send the test message of `chapters/ch00/python/check_setup.py` (*“Reply with exactly these three words: Ollama is ready”*) through `chat()` and observe the time taken. Explain the duration from Figure 3.3.

**Exercise 3.3.** Run `ch03_repeatability.py` against Ollama. How many distinct answers do you get at temperature 0 and at temperature 1? Explain.

**Exercise 3.4.** Write a function `ask_section(section_title, question)` that finds a prospectus section by its title and asks the question, in Python and R. Use it to ask *“What is the Reserve Fund Required Amount?”* with Section 3.

**Exercise 3.5.** Change the system instructions to remove *“If the text does not contain the answer, say so.”* Ask *“What is the rating of the Class A notes?”* with Section 2. Then put the sentence back and ask again. Compare the two answers.

## Corrections

### Exercise 3.1

**What the question asks.** The yearly cost of the investor-question service with the large paid model, under new assumptions (2,000 questions a month, 6,000 input and 500 output tokens per question), and which change raised the cost most.

**The plan.** (1) Compute the cost of one question. (2) Scale to a year. (3) Confirm with the program. (4) Split the increase between the three changes.

**Step by step.**

*Step 1 — One question.* With the script’s illustrative large-model prices, \$3.00 per million input tokens and \$15.00 per million output tokens:

- input: $6{,}000 / 10^6 \times 3.00 = \$0.0180$;
- output: $500 / 10^6 \times 15.00 = \$0.0075$;
- total: \$0.0255 per question.

*Step 2 — A year.* $0.0255 \times 2{,}000 \times 12 = \$612.00$.

*Step 3 — The program.* Change the three constants at the top of `ch03_cost.py`:

``` python
QUESTIONS_PER_MONTH = 2_000
INPUT_TOKENS = 6_000
OUTPUT_TOKENS = 500
```

The loop then computes, for each model, `per_q = INPUT_TOKENS / 1e6 * p_in + OUTPUT_TOKENS / 1e6 * p_out`: tokens converted to millions, times the price per million, for input and output separately. The R script has the same three variables.

**Reading the result.**

**What you should see**

``` text
small paid model   per question: $0.0085   per month: $17.00   per year: $204.00
large paid model   per question: $0.0255   per month: $51.00   per year: $612.00
```

The large model costs \$612.00 a year, against \$72.00 with the original assumptions.

**Checking the answer.** Split the increase from \$72 to \$612, changing one assumption at a time:

| Change                                                                          | Cost per year |     Added |
|---------------------------------------------------------------------------------|--------------:|----------:|
| Original (500 questions, 2,500 in, 300 out)                                     |       \$72.00 |           |
| Volume to 2,000 questions                                                       |      \$288.00 | +\$216.00 |
| Input to 6,000 tokens (3,500 more, at \$3 per million, 24,000 questions a year) |      \$540.00 | +\$252.00 |
| Output to 500 tokens (200 more, at \$15 per million)                            |      \$612.00 |  +\$72.00 |

The three additions sum to \$540, the full increase. The largest single addition is the extra passages (+\$252), slightly more than the volume (+\$216) in this order of calculation.

**Mistakes to avoid.**

- Applying the input price to output tokens. Output is five times dearer here; the error would understate the cost.
- Forgetting the factor 12: \$51 is the monthly figure.
- Reading the attribution as unique. Change the order (passages first, then volume) and the shares change, because the effects multiply. State the order you used.

**Trade-offs.** Sending fewer passages lowers cost and latency but risks leaving out the passage that holds the answer. The right number is the smallest one that keeps the evaluation score of Chapter 5 at its target: measure, then cut. The prices in the script are illustrative; take current prices from your provider before deciding.

### Exercise 3.2

**What the question asks.** Make the mock server fail twice, call it through `chat()`, and explain the time the call takes using the retry diagram (Figure 3.3).

**The plan.** Start the mock with two failures, time one call, then read `_post()` to explain the waits. Then push the mock past the retry limit.

**Step by step.**

*Step 1 — Start the failing mock* (macOS, Linux):

``` bash
MOCK_FAIL_FIRST=2 python tools/mock_ollama.py
```

The variable tells the mock to answer HTTP 503 (*service unavailable*) to the first two requests.

*Step 2 — Call through `chat()`* in another terminal, from the repository root:

``` python
import sys; sys.path.insert(0, ".")
from aie.llm import chat
r = chat([{"role": "user",
           "content": "Reply with exactly these three words: Ollama is ready"}])
print(r["text"], r["seconds"])
```

- `sys.path.insert(0, ".")` lets Python import the `aie` package from the repository root.
- `chat()` returns a dictionary; `r["seconds"]` is the total time of the call, including waits.

*Step 3 — The retry loop* in `aie/llm.py`:

``` python
for attempt in range(retries + 1):
    r = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if r.status_code in (429, 500, 502, 503, 529):
        last = LLMError(f"HTTP {r.status_code}: {r.text[:200]}")
        if attempt < retries:              # no wait after the last attempt
            # the server may say how long to wait
            wait = r.headers.get("Retry-After", "")
            time.sleep(min(float(wait), 30) if wait.isdigit()
                       else min(2 ** attempt, 8))
        continue
```

- `range(retries + 1)` with `retries=2` allows three attempts: 0, 1, 2.
- The listed statuses are temporary errors; for them, the loop waits and tries again. After the last attempt it does not wait: nothing follows.
- How long it waits: if the server sent a `Retry-After` header (a number of seconds, common with 429), the loop obeys it, up to 30 seconds; otherwise it waits $2^{\text{attempt}}$ seconds, at most 8. The mock sends no such header.
- The full function treats a connection that fails or times out the same way: wait, then retry. `httr2::req_retry()` in R behaves alike for HTTP errors and failed connections.

**Reading the result.** It prints `Ollama is ready 3.009` (the last digits vary). Attempt 0 receives 503 and waits $2^0 = 1$ second; attempt 1 receives 503 and waits $2^1 = 2$ seconds; attempt 2 succeeds. Waiting: 3 seconds, plus a few milliseconds of work.

**Checking the answer.** Restart the mock with `MOCK_FAIL_FIRST=5`. Three attempts, three failures: `chat()` raises

``` text
LLMError: HTTP 503: {"error": "server busy"}
```

after waiting $1 + 2 = 3$ seconds: no wait follows the third failure. The time and the error both follow from the loop. In R, `httr2`’s retry gives the same sequence and shows a progress bar during the waits.

**Mistakes to avoid.**

- Leaving the failing mock running for later exercises: every call then takes three seconds. Stop it with `Ctrl+C`.
- Retrying on every status. A 404 (wrong model name) or 400 (bad request) will fail again; retrying only delays the error. The loop raises them at once.

**Trade-offs.** More retries survive longer outages but make the user wait; the cap of 8 seconds per wait keeps the worst case bounded. For a person waiting in an application, two retries are enough; for a batch job running overnight, five are reasonable. Whatever the number, the application must catch `LLMError` and show a clear message, never a stack trace.

### Exercise 3.3

**What the question asks.** Ask the same question five times at temperature 0 and five times at temperature 1, count the distinct answers, and explain the difference.

**The plan.** Run the script with Ollama (mock stopped), read the two counts, relate them to Chapter 2’s temperature.

**Step by step.**

``` bash
python chapters/ch03/python/ch03_repeatability.py
```

The script asks the same one-sentence question five times with `temperature=0.0, seed=42`, then five times with `temperature=1.0, seed=None`. For each temperature, `Counter(answers)` counts each distinct reply once, so `len(Counter(answers))` is the number of different answers.

**Reading the result.** The run with `qwen3.5:4b` printed:

**What you should see**

``` text
Temperature 0.0: 1 distinct answers out of 5
Temperature 1.0: 5 distinct answers out of 5
```

At temperature 0 with seed 42, the five answers are identical. At temperature 1 without a fixed seed, all five differ. The R script gave the same two counts, and so did a second run on another machine.

**Checking the answer.** Print the five temperature-1 answers side by side. The facts are the same in each (borrowers move to the higher standard variable rate and refinance to a new fixed deal); the wording differs. At temperature 0, compare the strings with `==`: they are identical, character for character.

**Mistakes to avoid.**

- Running the script with the mock server: the mock always returns its scripted reply, so both counts are 1 and you learn nothing about the model.
- Concluding that temperature 0 makes answers *correct*. It makes them *repeatable*; a wrong answer at temperature 0 is wrong every time.

**Trade-offs.** At temperature 0 the most likely token is always chosen, so the same input gives the same output, which is what tests need. Identical outputs at temperature 0 hold on one machine, not across machines: paid providers batch requests differently from one call to the next, and a local model on another processor can change a word (the first call of this chapter did). Log the model’s answer rather than assume it. Use temperature 0 for anything you test or publish; use a higher temperature when you want several drafts to choose from.

### Exercise 3.4

**What the question asks.** Write `ask_section(section_title, question)`, which finds a prospectus section by title and asks the model about it, in Python and R, and use it on Section 3.

**The plan.** (1) Split the prospectus into sections keyed by title. (2) Refuse an unknown title with a helpful message. (3) Send the section and the question with grounding instructions. (4) Check the answer against Section 3.

**Step by step.**

``` python
import re, sys
sys.path.insert(0, ".")
from aie.llm import chat

PROSPECTUS = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
                  encoding="utf-8").read()
SECTIONS = {s.split("\n")[0]: s for s in re.split(r"\n## ", PROSPECTUS)[1:]}

def ask_section(section_title, question):
    if section_title not in SECTIONS:
        raise KeyError(f"no section titled {section_title!r}; "
                       f"choose from {list(SECTIONS)}")
    reply = chat(
        system="Answer only from the text provided. If the text does not "
               "contain the answer, say so.",
        messages=[{"role": "user", "content":
                   f"TEXT:\n{SECTIONS[section_title]}\n\nQUESTION: {question}"}])
    return reply["text"].strip()

print(ask_section("3. Reserve fund",
                  "What is the Reserve Fund Required Amount?"))
```

- `re.split(r"\n## ", PROSPECTUS)[1:]` cuts the text at each second-level heading and drops the part before the first one.
- `s.split("\n")[0]` is the first line of each section, its title (for example `3. Reserve fund`); the dictionary maps title to text.
- The `if` refuses an unknown title and lists the valid ones.
- `system=` gives the grounding rule; the user message labels the text and the question so that the model cannot confuse them.
- `.strip()` removes spaces and line breaks around the reply.

``` r
source("aie_r/llm.R")
prospectus <- paste(readLines(
  "data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
  encoding = "UTF-8"), collapse = "\n")
parts <- strsplit(prospectus, "\n## ", fixed = TRUE)[[1]][-1]
sections <- setNames(parts, sub("\n.*", "", parts))

ask_section <- function(section_title, question) {
  if (!section_title %in% names(sections))
    stop("no section titled '", section_title, "'")
  reply <- chat(
    system = paste("Answer only from the text provided. If the text does",
                   "not contain the answer, say so."),
    messages = list(list(role = "user", content = paste0(
      "TEXT:\n", sections[[section_title]], "\n\nQUESTION: ", question))))
  trimws(reply$text)
}
cat(ask_section("3. Reserve fund",
                "What is the Reserve Fund Required Amount?"), "\n")
```

- `readLines()` returns one string per line; `paste(..., collapse = "\n")` joins them into one text.
- `strsplit(..., fixed = TRUE)` splits on the literal heading marker; `[[1]][-1]` takes the pieces and drops the first.
- `sub("\n.*", "", parts)` keeps each piece’s first line, the title; `setNames()` names the pieces by title.
- `stop()` is R’s way of raising the error.

**Reading the result.** A good answer: *The Reserve Fund Required Amount is £6,082,667.80, equal to 1.50% of the aggregate current balance of the portfolio at the pool cut-off date; it does not amortise.*

**Checking the answer.** Open Section 3 of the excerpt: it states £6,082,667.80, 1.50% of the portfolio at the pool cut-off date (30 June 2025), and that the amount does not amortise. Every figure in the reply must appear there. Then test the error path: `ask_section("3. Reserve", ...)` raises the error listing the valid titles, without calling the model.

**Mistakes to avoid.**

- Returning an empty string for an unknown title instead of an error. The model would then receive an empty text and answer from nothing: the hallucination of Chapter 2.
- Matching titles without the number (`"Reserve fund"`): the keys include `3.`. Print `list(SECTIONS)` once to see them.
- Forgetting `encoding="utf-8"`: on Windows the pound sign is then misread.

**Trade-offs.** Looking up a section by its exact title is reliable but requires the caller to know the title. Chapter 7 replaces it with retrieval, which finds the section from the question itself, at the price of sometimes finding the wrong one; that is why retrieval is measured.

### Exercise 3.5

**What the question asks.** Compare the model’s answer to a question the text cannot answer, with and without the instruction *“If the text does not contain the answer, say so.”*

**The plan.** Ask about the Class A rating with Section 2 (which contains no rating) twice: once with the sentence removed from the system instructions, once with it.

**Step by step.** With `ask_section()` of Exercise 3.4, first change the system text to `"Answer only from the text provided."`, then ask:

``` python
print(ask_section("2. The notes", "What is the rating of the Class A notes?"))
```

Then put the second sentence back and ask again.

**Reading the result.** Without the sentence, a small model can answer with a rating such as *AAA*: senior notes of UK prime RMBS are commonly rated AAA, so the rating is a plausible continuation that the text does not support. With the sentence, the model should answer that the text does not state a rating. Run each version five times and count: the sentence is worth keeping if it turns invented ratings into refusals.

**Checking the answer.** Search Section 2 for *rat*: there is no rating, no rating agency. Any rating in the reply is invented. Run each version three times at temperature 0.7 with different seeds (`seed=1, 2, 3`) and count how often a rating appears. Temperature 0.7 matters: at temperature 0 the most probable token is always taken, so the seed has no effect and the three runs would be identical: you are measuring, on a small scale, what Chapter 5 measures on a test set.

**Mistakes to avoid.**

- Using the wrong section title: print `list(SECTIONS)` to see the exact title of Section 2.
- Concluding from one run. One answer is an anecdote; the rate over several runs is evidence.

**Trade-offs.** The instruction gives the model an acceptable continuation other than a guess, at the cost of occasional refusals when the answer *is* in the text but phrased differently. *Usually* is not enough for production: Chapter 5 adds questions whose correct answer is *not in the document* to the evaluation set and measures how often the model gives it.
