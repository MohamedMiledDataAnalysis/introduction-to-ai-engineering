# 4. Prompts as Code

## Exercises

**Exercise 4.1.** Using `render()`, display the full prompt sent for note `N002`. Then call `render()` without `note_text` and read the error.

**Exercise 4.2.** Write three more replies for the validator in Step 1: (F) a reply with an extra field `"reason"`; (G) a reply with `"arrears_balance": -50`; (H) a reply that is not JSON at all, *“I cannot find the loan.”*. Predict the verdicts, then run.

**Exercise 4.3.** Create `prompts/extract_servicer_note_v2.txt` with the two examples of Figure 4.4 between the instructions and the note. Compute its hash in Python and in R. Do they match?

**Exercise 4.4.** Add a field `"reason"` to the extraction: the cause of the arrears, chosen from `"income_reduction"`, `"illness"`, `"contract_end"`, `"relationship"`, `"payment_increase"`. Update the prompt (as v3) and the schema. Which phrases of the notes map to `"income_reduction"` and `"contract_end"`?

**Exercise 4.5.** Run the extraction twice with Ollama: once with `format=schema`, once with `format=None`. Compare the number of invalid replies. Explain.

## Corrections

### Exercise 4.1

**What the question asks.** Show the complete prompt that is sent to the model for note `N002`, then see what happens when the note is not supplied. The aim is to look at what the model actually receives, and to see a template fail loudly.

**The plan.** (1) Load the versioned template. (2) Find note N002 in the notes file. (3) Render and print. (4) Render without the value and read the error.

**Step by step.**

`chapters/ch04/python/solutions/ex4_1_rendered_prompt.py`

``` python
import json, sys
sys.path.insert(0, ".")
from aie.prompts import load_prompt, render

template, version = load_prompt("extract_servicer_note_v1")
notes = [json.loads(l) for l in
         open("data/sf/rmbs/servicer_notes_2026_09.jsonl", encoding="utf-8")]
note = next(n for n in notes if n["note_id"] == "N002")
print(render(template, note_text=note["text"]))
```

- `load_prompt()` reads `prompts/extract_servicer_note_v1.txt` and returns the text and its version hash, `49335149af`.
- The file is JSON Lines: one JSON object per line, so `json.loads(l)` decodes each line into a dictionary.
- `next(n for n in notes if ...)` returns the first note whose `note_id` is `N002`.
- `render(template, note_text=...)` replaces `{note_text}` in the template with the note’s text.

**Reading the result.** The instructions print unchanged (the five fields, *If a fact is not in the note, use null. Do not guess.*), then `NOTE:` followed by the text of N002: *30 Sep 2026 – account LMF25-00190: £1,960.79 outstanding in arrears (90 days). The customer set up an arrangement to clear the arrears, starting 28/10/2026. …* This is exactly what the model reads; nothing else is sent.

Now call `render(template)` without the value:

``` text
KeyError: "missing values for placeholders: ['note_text']"
```

In R, `render(p$text)` stops with *missing values for placeholders: note_text*.

**Checking the answer.** `render()` first lists the template’s placeholders with the pattern `\{([a-z_][a-z0-9_]*)\}`: for v1 the list is `['note_text']`. Every name in that list must be supplied, otherwise it raises. Check that the printed prompt contains no `{` followed by a letter: every placeholder has been filled.

**Mistakes to avoid.**

- Using Python’s `str.format()` for prompts. It fails on the JSON braces of an example (`{"loan_id": ...}`) and raises a confusing error; `render()` only replaces the named placeholders.
- Passing `note=` instead of `note_text=`: the name must match the placeholder exactly.

**Trade-offs.** A silent `render()` would send the literal text `{note_text}` to the model; the model would extract nothing, or invent a loan. That failure looks like a model problem and is a code problem. Failing loudly costs one check per call and puts the error where it belongs.

### Exercise 4.2

**What the question asks.** Add three faulty replies to the validator’s examples, predict each verdict from the schema, then run to confirm.

**The plan.** (1) Read the schema rule each reply breaks. (2) Write the replies. (3) Run the script. (4) Decide what the application does with each.

**Step by step.**

*Step 1 — Predict from `prompts/servicer_note_schema.json`.* F has a field the schema does not list, and the schema sets `"additionalProperties": false`: invalid. G has `arrears_balance` at −50, and the schema sets `"minimum": 0`: invalid. H contains no `{`: the parser cannot find a JSON object.

*Step 2 — Add to the `replies` dictionary* of `ch04_parse_and_validate.py`:

`chapters/ch04/python/solutions/ex4_2_three_faulty_replies.py` (extract)

``` python
replies["F extra field"] = ('{"loan_id": "LMF25-00190", "months_in_arrears": 3, '
    '"arrears_balance": 1960.79, "action": "payment_plan", '
    '"promise_date": "2026-10-28", "reason": "reduced hours"}')
replies["G negative amount"] = ('{"loan_id": "LMF25-00190", '
    '"months_in_arrears": 3, "arrears_balance": -50, '
    '"action": "payment_plan", "promise_date": "2026-10-28"}')
replies["H not JSON"] = "I cannot find the loan."
```

The script’s loop then calls `parse_json_reply()` on each reply (which removes code fences and finds the first balanced `{...}`) and, if that succeeds, `validate()` (which returns a list of error messages, empty when valid).

**Reading the result.**

**What you should see**

``` text
F extra field              INVALID
                            - unexpected fields ['reason']
G negative amount          INVALID
                            - 'arrears_balance' = -50 is below the minimum 0
H not JSON                 NOT JSON: no JSON object in the reply
```

All three predictions hold, and each message names the rule broken.

**Checking the answer.** Remove `"reason"` from F and run again: F becomes valid, proving that the extra field was the only problem. Change G’s −50 to 0: valid, because the minimum is inclusive.

**Mistakes to avoid.**

- Writing the replies with Python’s `True`/`None` instead of JSON’s `true`/`null`: the parser rejects them, and you test the wrong thing.
- Concluding that F is harmless and switching off `additionalProperties`. Extra fields are often the first sign that the model is not following the format.

**Trade-offs.** Each rejected reply needs a decision. F: reject and count it; the values may be right, but the model is drifting from the format. G: a real error, an arrears balance is never negative; reject. H: the model refused or failed; retry once, then route the note to a person. Strict rejection costs some retries; lenient acceptance lets errors into the data. Count every rejection by type: it becomes a line in the monitoring of Chapter 19.

### Exercise 4.3

**What the question asks.** Create a version 2 of the extraction prompt with the two examples of Figure 4.4, compute its hash in Python and R, and compare.

**The plan.** (1) Copy v1 to v2 and insert the examples before `NOTE:`. (2) Hash in both languages. (3) Compare, and explain any difference.

**Step by step.**

*Step 1 — The file.* Copy `prompts/extract_servicer_note_v1.txt` to `extract_servicer_note_v2.txt`. Between the line *If a fact is not in the note, use null. Do not guess.* and `NOTE:`, insert the two examples exactly as in Figure 4.4, each an `EXAMPLE NOTE:` line followed by an `EXAMPLE JSON:` line.

*Step 2 — The hashes.*

`chapters/ch04/python/solutions/ex4_3_prompt_hash.py` (extract)

``` python
from aie.prompts import load_prompt
print(load_prompt("extract_servicer_note_v2")[1])
```

`chapters/ch04/r/solutions/ex4_3_prompt_hash.R` (extract)

``` r
source("aie_r/prompts.R"); cat(load_prompt("extract_servicer_note_v2")$hash)
```

- `load_prompt()` returns the text and the first ten hexadecimal characters of its SHA-256 hash. Python strips the final line break before hashing; R’s `readLines()` drops it too, so both hash the same characters.

**Reading the result.** Both languages print `13626251e7`, different from v1’s `49335149af`. The repository holds a reference copy of the file in `prompts/solutions/extract_servicer_note_v2.txt`; if your hash differs, compare your file with it line by line. Any change to the file, even one space, changes the hash.

**Checking the answer.** Add a space at the end of one line, save and hash again: the hash changes in both languages, and still matches between them. Remove the space: the original hash returns.

**Mistakes to avoid.**

- **Windows line endings.** A file saved with `\r\n` endings is read differently by the two languages, and the hashes differ. Configure your editor (Positron: *Files: Eol* set to `\n`) and Git (`git config core.autocrlf input`).
- Saving in an encoding other than UTF-8: the pound sign then hashes differently.
- Editing v1 instead of creating v2. Version 1’s hash is recorded in earlier evaluation results; changing the file breaks the link between those results and the prompt that produced them.

**Trade-offs.** Examples improve the format of replies from small models, at a cost of about 150 tokens per call. The examples use invented loans, `LMF25-09999` and `LMF25-09998`, which do not exist in the tape: if an output ever contains them, the model copied an example instead of reading the note, which is a check in its own right.

### Exercise 4.4

**What the question asks.** Add a `reason` field (the cause of the arrears, from a closed list of five) to the prompt and the schema, and identify which phrases map to `income_reduction` and `contract_end`.

**The plan.** (1) List the cause phrases in the notes. (2) Map each to a category. (3) Write prompt v3. (4) Update the schema so that it accepts the five values or null.

**Step by step.**

*Step 1 — The phrases.* The notes introduce the cause with *Reason:*, *Cause given:* or *Circumstances:*. In the 18 notes of September 2026 there are four distinct phrases: *a relationship breakdown* (6 notes), *reduced working hours* (5), *an increase in the monthly payment after the fixed rate ended* (5), *a period of illness* (2).

*Step 2 — The mapping.* *Reduced working hours* is `income_reduction`. *The end of a fixed-term contract* is `contract_end`: it is in the servicer’s list of causes, but no September note uses it. *An increase in the monthly payment after the fixed rate ended* is `payment_increase`, not an income problem: keeping it separate matters for Larkfield, because it reveals payment shock when fixed rates revert.

*Step 3 — Prompt v3.* Add after the `promise_date` line:

``` text
- "reason": the cause of the arrears, one of "income_reduction",
  "illness", "contract_end", "relationship", "payment_increase",
  or null if the note gives no cause
```

*Step 4 — The schema.* Add the property, and add `"reason"` to `required`:

``` json
"reason": {"type": ["string", "null"],
           "enum": ["income_reduction", "illness", "contract_end",
                    "relationship", "payment_increase", null]}
```

- `"type": ["string", "null"]` allows a string or null.
- The `enum` lists the allowed values, **including `null`**. The book’s validator skips the enum check for null values, but Ollama uses the schema to constrain the model’s output; without `null` in the list, the model cannot write null even when the note gives no cause.

**Reading the result.** Run the v3 extraction: each reply now ends with a `reason`. On the September notes, expect 6 `relationship`, 5 `income_reduction`, 5 `payment_increase`, 2 `illness` and no `contract_end`.

**Checking the answer.** Count the phrases with code, independently of the model:

`chapters/ch04/python/solutions/ex4_4_reason_phrases.py` (extract)

``` python
import re
from collections import Counter
print(Counter(re.search(r"(?:Reason|Cause given|Circumstances): ([^.]*)",
                        n["text"]).group(1) for n in notes))
```

The model’s counts must match these: any difference is an extraction error to inspect.

**Mistakes to avoid.**

- Mapping *an increase in the monthly payment* to `income_reduction` because the borrower “has less money”. The cause is the payment, not the income.
- Forgetting to add `"reason"` to `required`: replies without it would then pass the validator.

**Trade-offs.** A closed list is easy to count and report; it forces every cause into a box. Add `"other"` if notes may contain causes outside the five, and keep the original phrase in a free-text field if analysts need it. A category with no occurrences this month (`contract_end`) still belongs in the list: next month it may appear.

### Exercise 4.5

**What the question asks.** Run the extraction once with the JSON schema passed to the model and once without, compare the number of invalid replies, and explain.

**The plan.** Run `ch04_extract_notes.py` twice, changing only the `format` argument; count invalid replies; relate the difference to how Ollama uses the schema.

**Step by step.** In `ch04_extract_notes.py`, the call is:

`chapters/ch04/python/ch04_extract_notes.py` (extract)

``` python
    reply = chat([{"role": "user",
                   "content": render(template, note_text=note["text"])}],
                 format=schema)
```

Run it, note the count of invalid replies printed at the end, then change `format=schema` to `format=None` and run again. The changed script is `chapters/ch04/python/solutions/ex4_5_without_schema.py`.

**Reading the result.** With the schema: 0 invalid replies, or very few. Without it, small models add explanations around the JSON (the parser tolerates them), write amounts as text such as `"£1,960.79"`, or rename fields (the validator rejects them): several invalid replies out of 18.

**Checking the answer.** For each invalid reply of the second run, print the reply and the validator’s message: each message names a rule (a type, a missing field, an extra field) that the schema enforces in the first run. Then compare the **values** of the valid replies in both runs against the `truth` field stored with each note in `servicer_notes_2026_09.jsonl`: the schema changes the format, not the accuracy.

**Mistakes to avoid.**

- Concluding that the schema makes extraction correct. A wrong month count is still wrong, just well formatted. Chapter 5 evaluates values, field by field.
- Comparing runs with different models or temperatures: change one thing at a time.

**Trade-offs.** With a schema, Ollama restricts the tokens the model may produce at each step to those that keep the reply valid: a quoted amount cannot appear where a number is required. The price is that the model cannot express “I am not sure” outside the fields, so the schema must allow `null` wherever a fact may be absent. Not every provider supports schema-constrained output; where it is missing, the validator is your only protection, which is why the book always validates.
