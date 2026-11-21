# 14. Structured Finance: Producing the Investor Report

## Exercises

**Exercise 14.1.** Produce the investor report for every collection period from July 2025 to September 2026. Confirm that all reconciliations pass, and list the months with new defaults.

**Exercise 14.2.** Write `draft_commentary(f)` that sends `facts_for_prompt(f)` to the model with a prompt of your own, checks the draft with `check_commentary()`, and falls back to the template if any figure is unsupported. Run it for September 2026 and for March 2026.

**Exercise 14.3.** Explain why the arrears ratio fell from 1.80% in March 2026 to 0.84% in September 2026, using the tape. Is it because borrowers cured, or for another reason?

**Exercise 14.4.** Break the data on purpose: in a copy of the notes file, reduce the Class B closing balance for September 2026 by £100. Run the production and show where it stops.

**Exercise 14.5.** Add a check that every direction word about the arrears ratio in the commentary (*rose*, *increased*, *fell*, *decreased*) agrees with the sign of the change.

## Corrections

### Exercise 14.1

**What the question asks.** Produce the investor report for each of the fifteen collection periods from July 2025 to September 2026, confirm that every reconciliation passes, and list the months with new defaults.

**The plan.** (1) List the dates from the tape, without the closing date. (2) For each date: compute the figures, reconcile, write the report. (3) Print the result of the gate and the new defaults.

**Step by step.**

`chapters/ch14/python/solutions/ex14_1_fifteen_reports.py` (extract)

``` python
from pathlib import Path
import pandas as pd
from aie.investor_report import (TAPE, month_figures, reconcile,
                                 render_markdown, template_commentary)

dates = sorted(pd.read_csv(TAPE)["RREL6"].unique())[1:]   # no report at closing
Path("reports").mkdir(exist_ok=True)
for d in dates:
    f = month_figures(d)
    ok = all(reconcile(f).values())
    Path(f"reports/larkfield_investor_report_{d[:7].replace('-', '_')}.md") \
        .write_text(render_markdown(f, template_commentary(f)), encoding="utf-8")
    print(d, "PASS" if ok else "FAIL", f"{f['new_defaults']:,.2f}")
```

- `sorted(...unique())[1:]` drops the first date, 30 June 2025: it is the pool cut-off at closing, and no payment was made on it.
- `reconcile(f)` returns the three checks of the gate; `all(...)` is `True` only if each passes.
- The file name uses the year and month, so that each report has its own file.
- In production the report would be written only if `ok` is `True`; here every report is written so that you can compare them.

**Reading the result.** All fifteen months print `PASS`. New defaults appear in nine months:

| Month         | New defaults |
|---------------|-------------:|
| December 2025 |  £460,387.60 |
| January 2026  |  £378,918.87 |
| February 2026 |  £195,826.14 |
| March 2026    |  £241,800.00 |
| April 2026    |  £627,986.46 |
| May 2026      |  £141,198.79 |
| June 2026     |   £96,500.00 |
| July 2026     |  £137,200.00 |
| August 2026   |  £426,546.50 |

September 2026 has none.

**Checking the answer.** The nine amounts sum to £2,706,364.36, the cumulative defaulted balance of the deal to date. Every default was debited to the PDL. In six of the nine months, excess spread cured the debit in full the same month. In December 2025, January 2026 and April 2026 it fell short: the Class D sub-ledger carried £103,135.69, £125,998.10 and £21,141.27 at those month-ends, and nothing was paid to the residual certificate holders. The debit stayed on the ledger from December to January and was cleared by the excess spread of February 2026; the £21,141.27 of April was cleared in May. The PDL has been zero since. Exercise 1.6 confirms it from the other side: notes minus PDL equals the pool in all 16 months.

**Mistakes to avoid.**

- Including 30 June 2025: there is no waterfall on the closing date, and `month_figures()` stops with `KeyError: 'Available revenue receipts'`.
- Writing reports to a folder inside the repository that Git tracks. `reports/` is in `.gitignore`: generated files do not belong in the repository.

**Trade-offs.** Producing every month at once tests the code on fifteen different situations (no defaults, large defaults, rising and falling arrears) in seconds; a single month tests one. The cost is fifteen files to look at; open the months that differ most (December 2025, April 2026, September 2026) rather than all.

### Exercise 14.2

**What the question asks.** Write `draft_commentary(f)`: send the month’s facts to the model with your own prompt, check the draft, and fall back to the template if any figure is unsupported. Run it for September and March 2026.

**The plan.** (1) Write a versioned prompt. (2) Fill it with `facts_for_prompt(f)`. (3) Check the reply with `check_commentary()`. (4) Return the draft or the template, with a record of which was used.

**Step by step.** Save as `prompts/investor_commentary_v1.txt` (the repository’s reference copy is `prompts/solutions/investor_commentary_v1.txt`):

``` text
You write the commentary of a UK RMBS investor report, in British English,
in at most four sentences. Use only the facts below and quote each figure
exactly as written. Mention new defaults only if they are above zero.
Do not forecast.

FACTS:
{facts}
```

`chapters/ch14/python/solutions/ex14_2_model_commentary.py` (extract)

``` python
def draft_commentary(f):
    template, version = load_prompt("investor_commentary_v1")
    text = chat([{"role": "user", "content":
                  render(template, facts=facts_for_prompt(f))}],
                temperature=0.3)["text"].strip()
    unsupported = [raw for raw, hits in check_commentary(text, f) if not hits]
    if unsupported:
        return template_commentary(f), {"used": "template",
                                        "unsupported": unsupported}
    return text, {"used": "model", "prompt": version}
```

- `facts_for_prompt(f)` gives the month’s figures already rounded and worded (*“Arrears ratio: 0.84% (down from 0.97% the previous month)”*).
- `check_commentary(text, f)` checks each figure against the full fact table of the month.
- The function returns the text **and** a record: which text was used, and why. That record goes to the log.

**Reading the result.** For September 2026, a good draft mentions the £4.88 million of principal repaid on the Class A notes, the fall of the arrears ratio to 0.84% from 0.97%, and the reserve fund at £6,082,667.80, and no defaults. For March 2026, it must mention the £241,800.00 of new defaults and the arrears ratio of 1.80%, up from 1.74%.

**Checking the answer.** Compare each draft with the template commentary of the same month, which uses the same facts: every figure in the draft should appear in the template or in `facts_for_prompt(f)`. Then force the fallback: change one figure in the draft by hand and pass it to `check_commentary()`; it must come back unsupported.

**Mistakes to avoid.**

- Checking the draft against `facts_for_prompt()` text instead of the fact table: the check must compare values, not strings.
- Telling the model to *“mention defaults”* without the condition: in September it will write *“there were no new defaults of £0.00”*, a correct but useless figure.

**Trade-offs.** Over the fifteen months, count how often the template was used. A fallback rate above one month in five means the prompt or the model needs work; record it in the monitoring of Chapter 19. The template is always correct and always dull; the model is usually correct and more readable. The check is what lets you use the model without trusting it.

### Exercise 14.3

**What the question asks.** Explain, using the tape, why the arrears ratio fell from 1.80% in March 2026 to 0.84% in September 2026: did borrowers cure, or did something else happen?

**The plan.** (1) Take the loans in arrears in March. (2) Look up each one’s status in September. (3) Count the outcomes. (4) Relate them to the ratio.

**Step by step.**

`chapters/ch14/python/solutions/ex14_3_march_arrears.py` (extract)

``` python
t = pd.read_csv(TAPE)
march = set(t[(t.RREL6 == "2026-03-31") & (t.RREL69 == "ARRE")].RREL2)
sep = t[t.RREL6 == "2026-09-30"].set_index("RREL2")["RREL69"]
print(len(march))
print(pd.Series({l: sep.get(l, "gone") for l in march}).value_counts())
```

- `march` is the set of loan identifiers in arrears at 31 March 2026.
- `sep` maps each loan identifier to its status at 30 September 2026.
- `sep.get(l, "gone")` returns `"gone"` for a loan no longer in the September tape (redeemed in between).

**Reading the result.** 34 loans were in arrears in March, against 18 in September. The 34 March loans ended September as follows:

**What you should see**

``` text
PERF    16
DFLT     8
RNAR     7
gone     2
ARRE     1
```

23 cured (16 back to performing, 7 restructured with no arrears), 2 redeemed and left the tape, 1 is still in arrears, and **8 defaulted**.

**Checking the answer.** $16 + 8 + 7 + 2 + 1 = 34$: every March loan is accounted for. The September tape’s 18 loans in arrears are therefore 1 March loan and 17 loans that fell behind after March: arrears are a flow, not a fixed group.

**Mistakes to avoid.**

- Concluding *“borrowers cured”* from the ratio alone. Defaulted loans carry a zero balance in the tape, so they leave the arrears numerator: 8 of the 34 left arrears by defaulting.
- Forgetting the `"gone"` default: `sep[l]` would raise a `KeyError` for the two redeemed loans.

**Trade-offs.** The arrears ratio fell mostly through cures, and partly *because* loans defaulted. *“Arrears fell”* is true and incomplete if defaults were high in the same period, which is why investor reports show cumulative defaults next to arrears. Add a fact *cumulative defaults since closing* to `facts_for_prompt()`, so that the model can mention both; the price is a longer fact list and one more figure to check.

### Exercise 14.4

**What the question asks.** Break the notes data on purpose (reduce the Class B closing balance for September 2026 by £100), run the production, and show where it stops.

**The plan.** (1) Corrupt a copy of the notes file. (2) Point the module at the copy. (3) Run the reconciliation. (4) Read which check fails and what that tells the analyst.

**Step by step.**

`chapters/ch14/python/solutions/ex14_4_broken_notes.py` (extract)

``` python
import tempfile
from pathlib import Path

import pandas as pd
import aie.investor_report as ir

notes = pd.read_csv(ir.NOTES)
mask = (notes.cutoff == "2026-09-30") & (notes.cls == "B")
notes.loc[mask, "closing"] -= 100
broken = Path(tempfile.gettempdir()) / "notes_broken.csv"
notes.to_csv(broken, index=False)

ir.NOTES = str(broken)
print(ir.reconcile(ir.month_figures("2026-09-30")))
```

- The copy goes to the computer’s temporary folder, which `tempfile.gettempdir()` finds on every system: the repository’s data is never modified.
- `ir.NOTES` is the path the module reads; changing it redirects `month_figures()` to the copy.

**Reading the result.**

``` text
{'notes - PDL = pool': False,
 'revenue paid = revenue available + reserve drawn': True,
 'principal paid = principal available + PDL cures': True}
```

Running `ch14_investor_report.py` with the copy prints `FAIL  notes - PDL = pool` and exits with *Reconciliation failed: the report is not produced.*

**Checking the answer.** Set `ir.NOTES` back to `data/sf/rmbs/larkfield_2025_1_notes.csv` and run again: all three checks pass. The £100 change alone caused the failure. The two other checks still pass because they compare waterfall amounts, which do not involve note balances.

**Mistakes to avoid.**

- Editing the real notes file to test: you then have to restore it, and may commit the broken version.
- Forgetting to restore `ir.NOTES` in the same Python session: every later report would use the broken copy.

**Trade-offs.** The failure says the liabilities are £100 short of the assets, and the passing checks say the cash movements are consistent: the gate has narrowed the search to the notes file before anyone opens it. A gate with one global check would only say *“something is wrong”*. Several independent checks cost a few lines each and turn a failure into a diagnosis.

### Exercise 14.5

**What the question asks.** Check that every word describing the direction of the arrears ratio (*rose*, *increased*, *fell*, *decreased*) agrees with the sign of the month’s change.

**The plan.** (1) List the words for each direction. (2) Split the commentary into sentences and keep those about arrears. (3) Compare the words with the sign of the change. (4) Test on a correct and a corrupted commentary.

**Step by step.**

`chapters/ch14/python/solutions/ex14_5_direction_words.py` (extract)

``` python
import re
UP = ("rose", "increased", "up", "higher", "worsened")
DOWN = ("fell", "decreased", "down", "lower", "improved")

def arrears_direction_errors(text, f):
    change = f["arrears_ratio"] - f["prev_arrears_ratio"]
    errors = []
    for sentence in re.split(r"(?<=\.)\s", text):
        s = sentence.lower()
        if "arrears" not in s:
            continue
        if change < 0 and any(re.search(rf"\b{w}\b", s) for w in UP):
            errors.append(f"says up, arrears fell: {sentence}")
        if change > 0 and any(re.search(rf"\b{w}\b", s) for w in DOWN):
            errors.append(f"says down, arrears rose: {sentence}")
    return errors
```

- `change` is negative when arrears fell; `f["prev_arrears_ratio"]` is the previous month’s ratio, already in the month’s figures.
- `re.split(r"(?<=\.)\s", text)` splits after each full stop.
- `\b{w}\b` matches whole words, so *up* does not match *supported*.

**Reading the result.** On the template commentary for September 2026 (*“The arrears ratio fell to 0.84% from 0.97%”*): no error. Replace *fell* by *rose*:

``` text
['says up, arrears fell: The arrears ratio rose to 0.84% from 0.97%, and the annualised prepayment rate was 14.8%.']
```

**Checking the answer.** Test the other branch on March 2026, where arrears rose (1.74% to 1.80%): the template (*“rose to 1.80%”*) gives no error, and replacing *rose* by *fell* gives *says down, arrears rose*. Both directions have now produced an error, so both work.

**Mistakes to avoid.**

- Checking the whole commentary instead of the arrears sentences: *“principal receipts … repaid”* or *“prepayment rate was higher”* would trigger false errors.
- Treating *improved* as *up*. For arrears, improving means falling.

**Trade-offs.** Direction words depend on the metric: *improved* means *fell* for arrears but *rose* for a credit score. Keep one word list per metric and test each on sentences from past reports. A sentence about two metrics (*“arrears fell and prepayments rose”*) defeats a sentence-level check; split on *and* or check clause by clause as Chapter 13 does, at the cost of more code.
