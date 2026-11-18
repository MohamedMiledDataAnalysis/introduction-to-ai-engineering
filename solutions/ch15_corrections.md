# 15. Asset Management: Extracting Data from Key Information Documents

## Exercises

**Exercise 15.1.** Run `extract_kid()` with Ollama for the three funds, and check each result with `check_extraction()` and against `evals/kid_truth.json`.

**Exercise 15.2.** Write a positional check for the moderate scenario: find the *Moderate* row of the scenarios table and require the extracted value to be in its last column. Show that it rejects the HBMA extraction.

**Exercise 15.3.** Add the stress scenario at the end of the RHP to the schema, the prompt and the checks. Which check catches a stress value taken from the favourable row?

**Exercise 15.4.** The product team changes HECB’s ongoing charges figure to 0.38% in the master data, but the KID still says 0.40%. What does `check_extraction()` report on a correct extraction, and what should happen next?

**Exercise 15.5.** Compare the model with a regular-expression extractor written for Harbourline’s KIDs. Write the extractor for the management costs and the SRI, then explain why it would fail on another manager’s KIDs, and why the model would not need rewriting.

## Corrections

### Exercise 15.1

**What the question asks.** Extract the three funds’ KIDs with your model, check each extraction with `check_extraction()`, and compare it with the reference values in `evals/kid_truth.json`.

**The plan.** (1) Extract each KID. (2) Run the three checks. (3) Compare each field with the truth. (4) Put every field in one of four boxes: right/wrong × accepted/rejected.

**Step by step.**

``` python
import json, sys
sys.path.insert(0, ".")
import pandas as pd
from aie.kid_extract import extract_kid, check_extraction

funds = pd.read_csv("data/am/funds.csv").set_index("fund_code")
truth = json.load(open("evals/kid_truth.json"))
for code in ("HGEF", "HECB", "HBMA"):
    obj, version = extract_kid(code)
    document = open(f"data/am/documents/{code.lower()}_kid.md",
                    encoding="utf-8").read()
    problems = check_extraction(obj, document, funds.loc[code])
    wrong = [f for f in obj if obj.get(f) != truth[code][f]]
    print(code, problems or "accepted", "| wrong:", wrong or "none")
```

- `extract_kid(code)` sends one KID to the model with the schema of `prompts/kid_schema.json`; one document per call, so costs of two funds cannot be mixed.
- `check_extraction()` runs the three checks: each value written in the document as the KID writes it; a valid ISIN check digit; agreement with the fund master (risk indicator, and management costs against the ongoing charges figure).
- `wrong` compares each field with the truth file: this is what the checks are trying to predict without knowing the truth.

**Reading the result.** For each field, four outcomes are possible: right and accepted (good), wrong and rejected (good: caught), right and rejected (a check too strict: inspect it), wrong and accepted (the dangerous case: a check is missing). Costs and the RHP are usually right: they sit in clear sentences. The SRI and the scenarios are where small models err: the SRI sentence contains both 1 and 7 (*“3 on a scale of 1 … to 7”*), and the scenario table has two columns of similar numbers.

**Checking the answer.** Run the same checks on the prepared candidates, `ch15_check_kids.py`: HGEF and HECB are rejected with their wrong fields named; HBMA is **accepted although its moderate scenario is wrong** (10,430 instead of 11,840). That is the wrong-and-accepted box, and Exercise 15.2 closes it.

**Mistakes to avoid.**

- Counting a rejected extraction as a failure of the pipeline. A wrong value rejected is the pipeline working.
- Comparing with the truth file in production. The truth exists only for evaluation; in production only the checks run.

**Trade-offs.** Each check costs little, but each misses some errors: the presence check accepts a number that is in the document but in the wrong place. Fill the two-by-two table per field, as in Figure 5.3, after every change of prompt or model; the empty or full boxes tell you which check to add.

### Exercise 15.2

**What the question asks.** Write a check that finds the *Moderate* row of the scenarios table and requires the extracted value to be its last cell (the value at the end of the recommended holding period), then show that it rejects the HBMA extraction.

**The plan.** (1) Find the row with a pattern anchored at the start of the line. (2) Capture its last *EUR* cell. (3) Compare with the extracted value. (4) Run on the three candidates.

**Step by step.**

``` python
import re

def moderate_rhp_in_document(document):
    m = re.search(r"^\| Moderate \|[^\n]*\| EUR ([\d,]+) \|\s*$", document, re.M)
    return float(m.group(1).replace(",", "")) if m else None
```

- `^\| Moderate \|` anchors on a line that starts with the *Moderate* cell; `re.M` makes `^` and `$` match at each line.
- `[^\n]*` skips the middle cells without leaving the line.
- `\| EUR ([\d,]+) \|\s*$` captures the last cell before the end of the line.

Add to `check_extraction()`:

``` python
expected = moderate_rhp_in_document(document)
if expected is not None and obj.get("moderate_scenario_rhp_eur") != expected:
    problems.append(f"moderate scenario {obj['moderate_scenario_rhp_eur']} "
                    f"is not the RHP column value ({expected})")
```

In R:

``` r
moderate_rhp_in_document <- function(document) {
  line <- grep("^\\| Moderate \\|", strsplit(document, "\n")[[1]], value = TRUE)
  if (!length(line)) return(NULL)
  cells <- regmatches(line, gregexpr("EUR [0-9,]+", line))[[1]]
  as.numeric(gsub("EUR |,", "", tail(cells, 1)))
}
```

- `grep(..., value = TRUE)` returns the matching line; `regmatches(gregexpr(...))` extracts every *EUR* cell; `tail(cells, 1)` keeps the last.

**Reading the result.** HBMA is now rejected: *moderate scenario 10430.0 is not the RHP column value (11840.0)*. HGEF (14,020) and HECB (10,690) keep their earlier problems only; their scenario values were right.

**Checking the answer.** HBMA’s KID row reads *\| Moderate \| … \| EUR 10,430 \| EUR 11,840 \|*: 10,430 is the value after one year, 11,840 after the RHP. The candidate took the wrong column, and the R function returns 11840 too. The wrong-and-accepted box of Exercise 15.1 is now empty.

**Mistakes to avoid.**

- Searching for *Moderate* anywhere in the document: the word also appears in the narrative.
- Capturing the first *EUR* cell: that is exactly the error the check must catch.

**Trade-offs.** A positional check depends on the table layout of Harbourline’s KIDs; other manufacturers order the columns differently. A layout-independent alternative is to extract *both* columns (after one year and after the RHP) and check that the pair, in that order, matches a row of the document. It doubles the fields to extract and check; it survives a change of template.

### Exercise 15.3

**What the question asks.** Add the stress scenario at the RHP to the schema, the prompt and the checks, and identify which check catches a stress value taken from the favourable row.

**The plan.** (1) Extend the schema, the prompt and the document format. (2) Go through each existing check with a wrong value from the favourable row. (3) Add the check that catches it, and a layout-independent second line.

**Step by step.**

*Step 1 — Extend.*

- Schema (`prompts/kid_schema.json`): add `"stress_scenario_rhp_eur": {"type": "number", "minimum": 0}` and list it in `required`.
- Prompt (`extract_kid_v2.txt`): *“stress_scenario_rhp_eur”: what you might get back in the stress scenario at the end of the recommended holding period, in EUR.*
- `DOC_FORMAT` in `aie/kid_extract.py`: `"stress_scenario_rhp_eur": "EUR {:,.0f}"`.

*Step 2 — Which check catches a favourable value (for HBMA, 14,210 instead of 5,030)?* The presence check does not: *EUR 14,210* is in the document. The schema does not: it is a positive number. The fund master has no scenarios. Only a positional check on the *Stress* row, written like Exercise 15.2’s with `Stress` instead of `Moderate`, catches it.

*Step 3 — A second line, independent of the layout.*

``` python
order = ["stress_scenario_rhp_eur", "unfavourable_scenario_rhp_eur",
         "moderate_scenario_rhp_eur", "favourable_scenario_rhp_eur"]
values = [obj.get(f) for f in order if obj.get(f) is not None]
if values != sorted(values):
    problems.append("scenario values are not in increasing order")
```

**Reading the result.** With 14,210 as the stress value and 11,840 as the moderate, the order check fails: a stress outcome cannot exceed a moderate one.

**Checking the answer.** HBMA’s KID gives, at the RHP: stress 5,030, unfavourable 9,520, moderate 11,840, favourable 14,210, in increasing order. The correct extraction passes the order check; the swapped one fails it.

**Mistakes to avoid.**

- Adding the field to the schema but not to `DOC_FORMAT`: the presence check then silently skips it.
- Requiring strict inequality for the scenarios of a money-market fund, where two scenarios can be equal: use `<=`.

**Trade-offs.** The order check needs all four scenarios, so it costs three more fields to extract. Plausibility relations between fields are cheap and layout-independent, but they only catch errors that break the relation: a stress value taken from the unfavourable row still passes the order check if it stays below the moderate. Use both: positional for precision, relational for robustness.

### Exercise 15.4

**What the question asks.** HECB’s ongoing charges figure is changed to 0.38% in the master data while the KID still says 0.40%. Say what `check_extraction()` reports for a correct extraction, and what should happen next.

**The plan.** (1) Change the master value in a copy. (2) Check the correct extraction. (3) Diagnose. (4) Route the issue.

**Step by step.**

``` python
f = funds.copy()
f.loc["HECB", "ocf"] = 0.0038
doc = open("data/am/documents/hecb_kid.md", encoding="utf-8").read()
print(check_extraction(truth["HECB"], doc, f.loc["HECB"]))
```

- `truth["HECB"]` is a correct extraction (0.40%).
- The master stores costs as decimals: 0.38% is 0.0038.

**Reading the result.**

``` text
["management costs 0.4% differ from the fund master's ongoing charges (0.38%)"]
```

Check 1 passes (0.40% is in the KID); check 3 fails.

**Checking the answer.** Run the same call with the original master (`funds.loc["HECB"]`): the result is `[]`. The extraction did not change; only the master did, so the problem is the disagreement between the two sources.

**Mistakes to avoid.**

- Treating the rejection as an extraction error and retrying the model. The model was right.
- “Fixing” the check’s tolerance so that 0.40 and 0.38 match.

**Trade-offs.** The extraction is right; the KID and the master data disagree. Either the KID is out of date, or the master was changed in error. The mismatch goes to the product team as a data issue, with the KID section and the master record side by side. A KID whose costs differ from the costs charged must be corrected, because costs are among the figures investors compare. The extraction pipeline found a compliance issue that had nothing to do with AI; the price of the third check is that it raises such issues, which is its value.

### Exercise 15.5

**What the question asks.** Write a regular-expression extractor for the management costs and the SRI on Harbourline’s KIDs, compare it with the model, explain why it would fail on another manager’s KIDs and why the model would not need rewriting.

**The plan.** (1) Write a pattern for each field from the KID’s wording. (2) Run it on the three KIDs and compare with the truth. (3) Imagine other wordings. (4) Compare maintenance.

**Step by step.**

``` python
import re

def regex_extract(document):
    sri = re.search(r"Risk indicator:\*\* (\d) on a scale", document)
    oc = re.search(r"operating costs \| ([\d.]+)% of the value", document)
    return {"summary_risk_indicator": int(sri.group(1)) if sri else None,
            "management_costs_pct": float(oc.group(1)) if oc else None}
```

- The SRI pattern copies Harbourline’s sentence, *“**Risk indicator:** 3 on a scale of 1 … to 7”*, and captures the first digit after it.
- The cost pattern finds the table cell after *operating costs* and captures the percentage.
- Each returns `None` if the pattern is not found.

**Reading the result.** On the three Harbourline KIDs the extractor is exact: HGEF 4 and 0.75%, HECB 2 and 0.40%, HBMA 3 and 0.60%, all equal to the truth file.

**Checking the answer.** Feed it a sentence in another manager’s style, *“We have classified this product as 4 out of 7”*: the SRI comes back `None`. Feed it costs written *0.60% per annum* in a table headed *Ongoing charges*: `None` again. Each variation needs a new pattern, and a pattern written too loosely can match the wrong number instead of none.

**Mistakes to avoid.**

- Concluding that regular expressions are obsolete. On your own template they are faster, free and exact.
- Trusting a regex extractor without the checks. A silent `None` or a wrong match is as dangerous as a model error.

**Trade-offs.** The model’s prompt describes the meaning of each field, not its wording, so it recognises *4 out of 7* and *4 on a scale of 1 to 7* as the same fact; the checks stay the same for both methods. For your own firm’s KIDs, generated from a template, use regular expressions. For third-party documents, use the model. In both cases keep the checks: they are what make either method safe.
