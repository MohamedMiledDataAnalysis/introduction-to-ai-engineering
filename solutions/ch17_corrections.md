# 17. Asset Management: Summarising Research Notes

## Exercises

**Exercise 17.1.** Run `summarise_note()` with Ollama for the six notes and check each summary. Report the four requirements’ pass rates.

**Exercise 17.2.** Summary B was flagged twice for one error. Change `check_summary()` so that a wrong recommendation produces a single, clear message.

**Exercise 17.3.** A summary says *“the operating margin rose to 14.9%”* for Eastleigh Engineering. Every figure is in the note and the recommendation is right. Is it acceptable? Extend the checks to catch it.

**Exercise 17.4.** Write the key-facts extraction prompt and schema that would produce `key_facts.json` from a note, and the checks you would apply to it.

**Exercise 17.5.** A portfolio manager asks for the digest to include *“what we should do”*. Explain why the system will not, and what it can offer instead.

## Corrections

### Exercise 17.1

**What the question asks.** Summarise the six research notes with your model, check each summary, and report a pass rate for each of the four requirements: faithful, consistent, complete, short.

**The plan.** (1) Summarise each note. (2) Run `check_summary()`. (3) Assign each problem to its requirement from its message. (4) Compute the four pass rates.

**Step by step.**

``` python
import json, sys
sys.path.insert(0, ".")
from collections import Counter
from aie.summary_check import check_summary, summarise_note

key_facts = json.load(open("data/am/research/key_facts.json"))
fails = Counter()
for i in range(1, 7):
    nid = f"R{i:02d}"
    note = open(f"data/am/research/{nid}.md", encoding="utf-8").read()
    text, version = summarise_note(nid)
    for p in check_summary(text, note, key_facts[nid]):
        kind = ("faithful" if "not in the note" in p else
                "consistent" if p.startswith("recommendation") else
                "complete" if p.startswith("missing") else "short")
        fails[kind] += 1
print(fails)
```

- `summarise_note(nid)` fills the prompt *“Summarise the research note … in at most 50 words. Include: …”* with the note and calls the model.
- `check_summary()` returns problem messages; each requirement writes a recognisable message (*not in the note*, *recommendation …*, *missing: …*, *… words, limit 60*), so the message tells the requirement.
- `Counter` counts failures by requirement.

**Reading the result.** For each requirement, pass rate = (6 − failures of that kind) / 6. With small models, completeness is usually the weakest, through the main risk or the direction of the margin being dropped, and length the second weakest: models tend to restate the note. A summary can fail several requirements, so the four rates do not add up to the share of accepted summaries.

**Checking the answer.** Run `ch17_check_summaries.py` on the prepared summaries: R01 A is accepted, R01 B fails consistency (*buy* for a *Hold*), R01 C fails faithfulness (a 30.0% that is not in the note) and completeness (main risk), R02 D fails length (67 words). Your classifier must put each of these in the right requirement.

**Mistakes to avoid.**

- Classifying by counting problems per summary. One wrong recommendation produced two problems (Exercise 17.2); count requirements, not messages.
- Changing the prompt and the model at the same time: you will not know which change moved the rates.

**Trade-offs.** If completeness fails, the prompt lists the required items but models drop the last one: reorder the list so that the risk comes second, and re-run. Each change costs a re-run of six summaries; at this size, that is seconds. Change one thing at a time and keep the evaluation as the judge.

### Exercise 17.2

**What the question asks.** Summary B is flagged twice for one error (a wrong recommendation). Change `check_summary()` so that it produces one clear message.

**The plan.** (1) Find which two checks fire. (2) Make the completeness check skip the recommendation when the consistency check has already failed. (3) Run on all summaries.

**Step by step.** For R01 B, the consistency check reports *recommendation \[‘buy’\] differs from the note (Hold)*, and the completeness check, not finding *hold*, reports *missing: recommendation*. Two symptoms, one cause. Change the two checks in `aie/summary_check.py`:

``` python
said = [r for r in RECS if re.search(rf"\b{r}\b", summary, re.I)]
wrong_rec = bool(said) and said != [key["recommendation"].lower()]
if wrong_rec:
    problems.append(f"recommendation {said} differs from the note "
                    f"({key['recommendation']})")
required = {"recommendation": wrong_rec or
                key["recommendation"].lower() in summary.lower(),
            ...}
```

- `said` lists the recommendation words the summary contains.
- `wrong_rec` is `True` when the summary states a recommendation and it is not the note’s.
- In `required`, the recommendation counts as *present* when it is wrong: the problem is already reported, and reporting it twice adds nothing.

**Reading the result.** R01 B now gives one message: *recommendation \[‘buy’\] differs from the note (Hold)*.

**Checking the answer.** Re-run every prepared summary: R01 A and R02 A still accepted, R01 C and R02 D unchanged. And a summary with **no** recommendation still reports *missing: recommendation*, because `wrong_rec` is `False` when `said` is empty.

**Mistakes to avoid.**

- Removing the completeness test for the recommendation altogether: a summary that omits it would then pass.
- Deduplicating messages at the end by text: the two messages are different strings with one cause.

**Trade-offs.** The checks now depend on each other, which makes the code slightly harder to read. Clear, single messages matter in practice: the person who reads the rejections must see the cause at once, not two symptoms of it. When checks overlap, decide which one owns the error.

### Exercise 17.3

**What the question asks.** A summary says *“the operating margin rose to 14.9%”* for Eastleigh Engineering; every figure is in the note and the recommendation is right. Is it acceptable? Extend the checks to catch it.

**The plan.** (1) Compare with the note. (2) Find why the four checks pass. (3) Add a direction check at clause level. (4) Test on correct and wrong sentences, including a flat margin.

**Step by step.** The note says the margin was 14.9%, *down* from 15.5%: *rose* reverses the analyst’s finding. The figure is faithful; the direction is not. The key facts already hold both margins (`operating_margin_pct` 14.9, `previous_margin_pct` 15.5).

``` python
def margin_direction_errors(summary, key):
    if key["operating_margin_pct"] == key["previous_margin_pct"]:
        up = None
    else:
        up = key["operating_margin_pct"] > key["previous_margin_pct"]
    problems = []
    for clause in re.split(r"[.;,]|\band\b", summary.lower()):
        if "margin" not in clause:
            continue
        said_up = re.search(r"\b(rose|increased|up|higher|improved|widened)\b", clause)
        said_down = re.search(r"\b(fell|declined|down|lower|narrowed)\b", clause)
        if said_up and up is not True:
            problems.append("says the margin rose; it did not")
        if said_down and up is not False:
            problems.append("says the margin fell; it did not")
    return problems
```

- `up` is `True`, `False`, or `None` for a flat margin.
- The summary is split into clauses at punctuation and at *and*; only clauses that mention *margin* are checked.
- A direction word is an error unless it matches the facts; for a flat margin, any direction is an error.

Call it at the end of `check_summary()`: `problems += margin_direction_errors(summary, key)`.

**Reading the result.** *“the operating margin rose to 14.9%”*: `['says the margin rose; it did not']`. R02 A, *“Revenue grew 8.2% … and the operating margin fell to 14.9% from 15.5%”*: no error.

**Checking the answer.** Test the clause split with *“Revenue rose 8.2% and the operating margin fell to 14.9% from 15.5%.”*: no error, because *rose* is in the revenue clause. Test R03, whose margin is flat at 9.5%: *“The operating margin was stable at 9.5%.”* passes; *“The margin rose to 9.5%.”* is rejected.

**Mistakes to avoid.**

- Checking direction words over the whole summary. *“Revenue rose … the margin fell”* would be flagged as a contradiction.
- Treating a flat margin as a fall because `14.9 > 15.5` style comparisons return `False`: equal values need their own case.

**Trade-offs.** As in Exercise 14.5, direction words depend on the metric and need one list per metric. Clause splitting at *and* handles the common case and fails on clauses joined differently (*“while the margin…”*); add separators as you find them in failed summaries.

### Exercise 17.4

**What the question asks.** Write the prompt and the schema that would produce `key_facts.json` from a note, and the checks that make the extracted facts trustworthy.

**The plan.** (1) List the fields and types from `key_facts.json`. (2) Write the schema. (3) Write the prompt with units. (4) Write the checks against the note.

**Step by step.**

*The schema.*

``` json
{"type": "object",
 "properties": {
   "issuer": {"type": "string"},
   "recommendation": {"type": "string", "enum": ["Buy", "Hold", "Sell"]},
   "target_price_eur": {"type": ["number", "null"]},
   "revenue_growth_pct": {"type": ["number", "null"]},
   "operating_margin_pct": {"type": ["number", "null"]},
   "previous_margin_pct": {"type": ["number", "null"]},
   "net_debt_to_ebitda": {"type": ["number", "null"]},
   "main_risk": {"type": ["string", "null"]}},
 "required": ["issuer", "recommendation", "target_price_eur", "revenue_growth_pct",
              "operating_margin_pct", "previous_margin_pct", "net_debt_to_ebitda", "main_risk"],
 "additionalProperties": false}
```

*The prompt.* One note per call (Chapter 15). Each field defined with its unit: *“revenue_growth_pct: revenue growth year on year, in %, as a number: 2.9 for 2.9%”*; *“previous_margin_pct: the operating margin a year earlier”*; *null when the note does not state it*.

*The checks.*

``` python
def check_key_facts(obj, note):
    problems = []
    fmt = {"target_price_eur": "EUR {:.2f}", "revenue_growth_pct": "{:.1f}%",
           "operating_margin_pct": "{:.1f}%", "previous_margin_pct": "{:.1f}%",
           "net_debt_to_ebitda": "{:.1f} times"}
    for field, f in fmt.items():
        if obj.get(field) is not None and f.format(obj[field]) not in note:
            problems.append(f"{field} = {obj[field]} not written in the note")
    rec = re.search(r"Recommendation: (\w+)", note)
    if not rec or rec.group(1) != obj["recommendation"]:
        problems.append("recommendation differs from the note's Recommendation line")
    if obj.get("main_risk") and obj["main_risk"] not in note:
        problems.append("main risk is not a phrase of the note")
    if obj["issuer"] not in note.split("\n")[0]:
        problems.append("issuer is not the name in the title")
    return problems
```

**Reading the result.** On R01, the correct facts produce no problem: *EUR 32.72*, *2.9%*, *27.9%*, *26.2%*, *3.1 times* and *currency movements* are all written in the note, *Recommendation: Hold* is in its bold line, and *Upland Telecom* is in its title.

**Checking the answer.** Run `check_key_facts()` on each entry of the existing `key_facts.json` with its note: all six must pass, since the file is the truth. Then change R01’s target price to 32.36 (the *current* price, also in the note): the presence check passes (*EUR 32.36* is in the note), which shows the gap such a check leaves; anchoring on the words *Target price:* closes it.

**Mistakes to avoid.**

- Accepting `main_risk` as a free paraphrase. Requiring a phrase of the note makes it checkable.
- Extracting several notes in one call: figures move between issuers.

**Trade-offs.** The key facts serve two purposes: the completeness check of summaries, and a research database that the portfolio manager can query with the tools of Chapter 11. Extracting them costs one model call per note and a set of checks; the presence checks are cheap but, as the target-price test shows, a value can be present for the wrong reason. Anchor each figure on its label where the note’s layout allows.

### Exercise 17.5

**What the question asks.** A portfolio manager asks the digest to include *“what we should do”*. Explain why the system will not, and what it can offer instead.

**The plan.** (1) Name what the request is. (2) Say who owns that decision and under which controls. (3) Offer checkable facts that support the decision.

**Step by step.** *“What we should do”* is an investment decision. It belongs to the portfolio manager, under the fund’s mandate and the firm’s governance. A system that suggests trades from summaries of research becomes part of the investment process, with the controls that requires (Chapter 20), and its suggestion would rest on text the model cannot be held accountable for.

**Reading the result.** What the digest can offer, each item checkable:

- the fund’s weight in each issuer, from the note and from the holdings (Chapter 11’s tools);
- the change in the analyst’s recommendation since the previous note;
- notes whose recommendation conflicts with the fund’s position: a *Sell* on a top-ten holding.

These are flags, not instructions: the manager decides.

**Checking the answer.** Test each proposed item against the rule *every figure comes from data and can be checked*. The fund weight is in the holdings table (HGEF holds 5.03% in Upland Telecom, also stated in R01). A recommendation change is a comparison of two key-fact records. A conflict flag is a join of key facts and holdings. None of them asks the model for an opinion.

**Mistakes to avoid.**

- Phrasing a flag as advice (*“consider reducing Upland Telecom”*). Write the fact (*“Sell recommendation; fund weight 5.03%”*).
- Refusing without an alternative. The manager’s need, to act on research faster, is legitimate.

**Trade-offs.** Saying no to advice keeps the system outside the investment decision and its controls, at the cost of a less ambitious product. The flags deliver most of the time saving (finding what changed and where it matters) and leave the judgement where accountability already sits. If the firm later wants suggestions, that is a new use case with its own risk assessment, not a prompt change.
