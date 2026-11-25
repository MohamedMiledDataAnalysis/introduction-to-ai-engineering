# 0. Setting Up Your Computer

> © 2026 Mohamed Miled. All rights reserved. This text is part of the book *Introduction to AI Engineering* and may not be copied, republished or sold. The code blocks are under the MIT licence (see `LICENSE`); the explanations are not (see `LICENSE-TEXT.md`).

## Exercises

**Exercise 0.1.** Type `ollama list` in the terminal. Write down the name and size of each model you have downloaded.

**Exercise 0.2.** Modify `check_setup.py` so that it asks the model: *“What does the abbreviation SONIA stand for?”* Run it three times. Is the answer identical each time?

**Exercise 0.3.** In R, load `data/am/funds.csv` and print the name of each of the three Harbourline funds.

**Exercise 0.4.** Change the Python script so that the `MODEL` variable contains a name you have not downloaded, for example `"does-not-exist"`. Run it. Which message do you see, and which line of the script produced it?

## Corrections

Every correction in this book follows the same seven parts: **what the question asks**, **the plan**, **step by step** (with the code explained line by line), **reading the result**, **checking the answer**, **mistakes to avoid** in this exercise, and **trade-offs**. Read the parts in order the first time; later, you can jump to the check or the mistakes.

### Exercise 0.1

**What the question asks.** List the models Ollama has stored on your computer, with their size. The aim is to learn the first command to type when a script says a model is missing.

**The plan.** Run one command in the terminal and read its table.

**Step by step.**

``` bash
ollama list
```

- `ollama` is the program installed in Step 6 of this chapter; `list` asks it for the models stored on your disk.

**Reading the result.** The table has four columns: `NAME` (for example `qwen3.5:4b`), `ID` (a short hash of the model file), `SIZE` (in GB) and `MODIFIED` (when you downloaded it). After Chapter 0 you have at least one line, `qwen3.5:4b`, the chat model; its size is several gigabytes, and the exact figure depends on the version Ollama downloaded. If you followed the tip of Step 6, `qwen3.5:9b` appears too. Chapter 7 adds `nomic-embed-text`, the embedding model.

**Checking the answer.** The name in the table must be spelt exactly as in the scripts: `qwen3.5:4b`, with the colon and the tag. Run `ollama run qwen3.5:4b "Say hello"`: if a reply appears, the model listed is the model that works.

**Mistakes to avoid.**

- Reading `qwen3.5` without the tag `:4b`. Ollama treats `qwen3.5` and `qwen3.5:4b` as different names; a script asking for the wrong one gets a 404.
- Running `ollama list` in the R or Python console instead of the terminal: it is a terminal command, not a function.

**Trade-offs.** Every model stored costs disk space. Keep the two models of the book and remove experiments with `ollama rm <name>`; download them again later if you need them.

### Exercise 0.2

**What the question asks.** Change the question sent by `check_setup.py`, run the script three times and compare the replies. The aim is to observe that a model’s wording varies from one run to the next.

**The plan.** Edit one line of the payload, run three times, compare wording and facts separately.

**Step by step.** In `chapters/ch00/python/check_setup.py`, replace the content of the message:

`chapters/ch00/python/solutions/ex0_2_sonia.py` (extract)

``` python
payload = {
    "model": MODEL,
    "messages": [{"role": "user",
                  "content": "What does the abbreviation SONIA stand for?"}],
    "stream": False,
    "think": False,     # answer directly; Chapter 3 explains
}
```

- `"model": MODEL` names the model to use; `MODEL` is defined at the top of the script.
- `"messages"` is a list of messages; here one message, with `"role": "user"` (it comes from you) and `"content"`, the question.
- `"stream": False` asks Ollama to send the whole reply at once instead of word by word.
- `"think": False` asks the model to answer directly. `qwen3.5` writes a hidden reasoning before its answer unless told not to; Chapter 3 explains why the book switches it off.

Then run, three times:

``` bash
python chapters/ch00/python/check_setup.py
```

**Reading the result.** The three replies expand SONIA as *Sterling Overnight Index Average*, the risk-free reference rate for sterling overnight lending, administered by the Bank of England. The sentences around the expansion differ: one reply adds that SONIA replaced LIBOR (the London Interbank Offered Rate, the former reference rate), another mentions the Bank of England, a third is one line long.

**Checking the answer.** Separate the two things you compare. **The fact** (the four words of the expansion) is identical in all three replies: write it down and compare letter by letter. **The wording** differs. Check the fact against an authoritative source: the Bank of England’s page on SONIA gives the same expansion.

**Mistakes to avoid.**

- Concluding that the model is wrong because the sentences change. Variation in wording is expected; variation in a fact would be a problem.
- Editing the `"role"` instead of the `"content"`: a message with `"role": "What does..."` is refused by Ollama.

**Trade-offs.** Variation is useful when you want several drafts to choose from; it is a problem when you want a test to give the same result every day. Chapter 3 sets `temperature` to 0 and fixes a `seed` (the starting number of the random draws, Chapter 2) to make replies reproducible, at the cost of always getting the same draft.

### Exercise 0.3

**What the question asks.** Read the fund list in R and print the three fund names. The aim is to check that R reads the repository’s data from the root folder.

**The plan.** Read the CSV file into a data frame, then print one column.

**Step by step.**

`chapters/ch00/r/solutions/ex0_3_fund_names.R`

``` r
funds <- read.csv("data/am/funds.csv")
print(funds$name)
```

- Line 1: `read.csv()` reads the file into a data frame; the path is relative to the working directory, which must be the repository root.
- Line 2: `funds$name` selects the column called `name`; `print()` shows it.

**Reading the result.**

**What you should see**

``` text
[1] "Harbourline Global Equity Fund"
[2] "Harbourline Euro Corporate Bond Fund"
[3] "Harbourline Balanced Multi-Asset Fund"
```

The numbers in brackets are R’s positions in the vector, not part of the names.

**Checking the answer.** `nrow(funds)` returns 3, and `funds$fund_code` returns `"HGEF" "HECB" "HBMA"`, the codes used throughout the book.

**Mistakes to avoid.**

- Running the script from another folder: R then reports *cannot open file ‘data/am/funds.csv’*. Run `getwd()`; its result must end with this folder name: `introduction-to-ai-engineering`.
- Writing `funds$Name` with a capital: R column names are case-sensitive and the result is `NULL`, without an error.

**Trade-offs.** `read.csv()` is in base R and needs no package. `readr::read_csv()` is faster on large files and reads dates as dates; for a three-line file the difference does not matter.

### Exercise 0.4

**What the question asks.** Give the script a model name that does not exist, and find which line prints the message you see. The aim is to read error handling before writing it.

**The plan.** Change `MODEL`, run, then follow the error from the HTTP status to the `except` block.

**Step by step.**

`chapters/ch00/python/solutions/ex0_4_missing_model.py` (extract)

``` python
MODEL = "does-not-exist"
```

Run the script. The relevant part of the script is:

`chapters/ch00/python/solutions/ex0_4_missing_model.py` (extract)

``` python
try:
    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()
    print("Model reply:", response.json()["message"]["content"].strip())
except requests.exceptions.ConnectionError:
    print("Ollama is not running. Start the Ollama application, "
          "then run this script again.")
except requests.exceptions.HTTPError as err:
    print("Ollama answered with an error:", err)
    print(f"Check that you downloaded the model with: ollama pull {MODEL}")
```

- `requests.post(...)` sends the request. Ollama is running, so there is no `ConnectionError`; it answers with HTTP status **404** (*not found*), because it has no model of that name.
- `response.raise_for_status()` turns any status of 400 or above into an `HTTPError`. The next line, which would read the reply, is skipped.
- `except requests.exceptions.HTTPError as err:` catches it; the two `print` lines run.

**Reading the result.**

``` text
Ollama answered with an error: 404 Client Error: Not Found for url: http://localhost:11434/api/chat
Check that you downloaded the model with: ollama pull does-not-exist
```

The first line is printed by `print("Ollama answered with an error:", err)`; the second by the f-string line below it.

**Checking the answer.** Stop the Ollama application and run again: now the *other* message appears (*Ollama is not running…*), printed by the `ConnectionError` block. Two different failures, two different messages: the error handling distinguishes them. In R, the same two cases are handled by `httr2_failure` (connection) and `httr2_http` (status 404) in `check_setup.R`.

**Mistakes to avoid.**

- Removing `raise_for_status()`: the script then tries to read `["message"]` from an error body and stops with a `KeyError`, a message that says nothing about the cause.
- Catching every error with a bare `except:`: the script then hides typing errors in your own code behind *Ollama answered with an error*.

**Trade-offs.** Specific `except` blocks give precise messages but need one block per failure you anticipate; anything else stops the script with a traceback, which is what you want for errors you did not anticipate. This is the habit of the book: **every call to a model is wrapped in error handling**, because in production the model server will, sooner or later, be unavailable.
