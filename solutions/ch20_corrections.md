# 20. Governance: Model Risk, Regulation and Data

## Exercises

**Exercise 20.1.** Add two use cases to the inventory: (a) a model that ranks mortgage applicants for approval; (b) a chatbot on Harbourline’s public website answering retail investors’ questions about the funds. Assign each a risk tier and explain which rules of section 20.4 apply.

**Exercise 20.2.** Generate the model card for AI-AM-01 (the fund database assistant). Which evaluation and which answers do you use? What must the *Known limitations* section say?

**Exercise 20.3.** Write the DPIA screening questions you would answer for the servicer note extraction of Chapter 4, and answer them.

**Exercise 20.4.** For the factsheet commentary (AI-AM-02), classify each of these changes as material or not, and justify: (a) moving from `qwen3.5:4b` to a larger local model; (b) correcting a typo in the prompt’s instructions; (c) adding a new forbidden phrase; (d) raising the temperature from 0.3 to 0.7.

**Exercise 20.5.** A reviewer approved 240 commentaries in one hour. What does this tell you, and what would you change?

## Corrections

### Exercise 20.1

**What the question asks.** Add two use cases to the inventory, a model ranking mortgage applicants and a public chatbot for retail investors, give each a risk tier, and say which rules of Section 20.4 apply.

**The plan.** For each use case: (1) place it on the tiering grid of Figure 20.2 (impact of an error, how far the output goes without a person); (2) check the EU AI Act’s categories; (3) list the UK rules; (4) write the inventory row and the requirements.

**Step by step.**

*(a) Ranking mortgage applicants.* An error affects a person’s access to credit, and the ranking feeds a decision. On the grid: high impact. Under the EU AI Act, AI used to evaluate the creditworthiness of natural persons is listed as high-risk (Annex III); as at November 2026, those obligations apply from 2 December 2027, after the AI Omnibus. A bank deploying it must also assess its impact on fundamental rights before use (Article 27). In the UK: Consumer Duty, fair treatment and anti-discrimination law, the UK GDPR rules on decisions based solely on automated processing (Article 22, as amended by the Data (Use and Access) Act 2025), and, for banks in scope, SS1/23 for a model used in credit decisions. Tier: **high**.

*(b) Public website chatbot.* It answers retail investors directly, with no person reading each answer. On the grid: client-facing, no review. The EU AI Act’s transparency obligations apply: people must be told they are interacting with an AI system. Its answers are financial promotions and can read as advice; in the UK, Consumer Duty and the financial promotion rules apply. Tier: **high** under Figure 20.2, although it is not a high-risk system under the Act’s annexes.

**Reading the result.** Two inventory rows:

``` text
AI-SF-04,Applicant ranking,sf,Rank mortgage applicants for approval,Underwriters,Feeds credit decisions,<model>,<prompt>,Underwriter decides each case,Applicant personal and financial data,Head of credit,High
AI-AM-04,Public fund chatbot,am,Answer retail investors' questions on the funds,Retail investors,Client-facing without review,<model>,<prompt>,Sampling by compliance,Published fund documents,Head of product,High
```

Requirements for (a): documented data governance and bias testing, independent validation before use, human oversight of each decision, explanations for declined applicants, logging, and monitoring of outcomes by group. For (b): a strict scope (published fund facts only, no recommendations), the checks of Chapters 6 and 7, refusal of advice and forecast questions (Chapter 22), an evaluation that includes adversarial questions, and daily sampling of answers by compliance.

**Checking the answer.** Test each tier against the inventory’s existing rows: AI-SF-01 drafts answers to investors too, but every answer is approved, so it is medium. The chatbot differs only in removing that approval, and Section 20.3 says that removing approval moves a use case up a tier. The reasoning is consistent with the rows already there.

**Mistakes to avoid.**

- Tiering by the technology. Both rows could use the same model as AI-SF-01.
- Calling the chatbot “high-risk under the AI Act”. It is high in the firm’s own tiering; under the Act it carries transparency obligations, not the high-risk regime. Use the words precisely.

**Trade-offs.** High tiers bring validation, oversight and monitoring that cost months before launch. For (b), a common path is to start at medium (staff approve drafted replies) and move to direct answers for a narrow set of questions once the evaluation and monitoring show a low, stable error rate. The same engineering can sit in the low, medium or high tier: the tier comes from the use.

### Exercise 20.2

**What the question asks.** Generate the model card for AI-AM-01, the fund database assistant: which evaluation and answers to use, and what the *Known limitations* section must say.

**The plan.** (1) Identify the evaluation of this use case. (2) Adapt the generator’s evaluation block to SQL. (3) Filter the monitoring on the AM domain. (4) Write the limitations from the evidence.

**Step by step.** The evaluation of AI-AM-01 is the SQL set of Chapter 11, scored by comparing query results, not text. Replace the evaluation block of `model_card()`:

``` python
from aie.sqlguard import run_sql, same_result

cases = pd.read_csv("evals/am_sql_qa.csv")
cands = pd.read_csv("evals/candidates/am_sql_candidates.csv").set_index("id")["sql"]
passed = [same_result(run_sql(c.reference_sql), run_sql(cands[c.id]), bool(c.ordered))
          for c in cases.itertuples()]
k, n = sum(passed), len(passed)
low, high = wilson_interval(k, n)
failed = [c for c, p in zip(cases.id, passed) if not p]
```

- Each candidate query and its reference are run through the same guard; `same_result()` compares rows.
- The candidates file reproduces Chapter 11; in production, use the SQL of a live run (Exercise 11.5) and record the model and prompt that produced it.

The monitoring block stays, filtered on `inv.domain`, which is `am`.

The *Known limitations* section cannot be computed; it is written from the evidence, and must state five facts:

- weighted averages and two-key joins were the most frequent errors (Chapter 11);
- the connection is read-only and limited to listed tables;
- answers are internal and checked by the specialist before forwarding;
- the evaluation set has ten cases, hence the wide interval;
- the AM prompt’s token count grew through October (Chapter 19) and is under investigation.

**Reading the result.** Evaluation: 5/10 passed (95% interval 24% to 76%), failed cases S01, S03, S04, S09, S10. Monitoring for the AM domain in October: 290 requests over 18 days, error rate 4.5% (the outage of 7 October), median daily review rate 5.1%, worst day 14.3%, median response time 3.5 seconds.

**Checking the answer.** The evaluation figures must match Chapter 11’s output, *5/10 candidate queries return the reference result*, and the failed cases must be the five corrected in Exercise 11.1. Note what the monitoring covers: the October log records the AM agent’s requests as a whole, not only database questions; the card must say so, or it overstates the evidence.

**Mistakes to avoid.**

- Reusing the prospectus evaluation of AI-SF-01 because the generator was written for it.
- Leaving the generator’s default limitations (*“limited to the prospectus excerpt”*), which describe another use case.

**Trade-offs.** A card that lists its weaknesses is more useful to a validator than one that does not, and it is the honest record if something goes wrong.

### Exercise 20.3

**What the question asks.** Write the screening questions of a data protection impact assessment for the servicer note extraction of Chapter 4, and answer them.

**The plan.** (1) Write six questions covering identity, necessity, sensitivity, location, retention and effect. (2) Answer each for the servicer notes. (3) Conclude.

**Step by step.** The questions:

1.  Does the data identify, or could it identify, a living person?
2.  Which personal data fields are sent to the model, and are they all needed for the task?
3.  Is any of it special-category data, for example health?
4.  Where is the model hosted, and does the data leave the firm?
5.  Is the data logged, where, for how long, and who can read it?
6.  Could the output affect the person (their account, their treatment)?

**Reading the result.** Answers for the servicer notes:

1.  Yes: notes concern identified borrowers through loan identifiers, and real notes may contain names (the book’s notes are signed by the collections officer, for example *M. Haddad*).
2.  The task needs the loan identifier, months in arrears, balance, action and dates. Names are not needed and are removed before the call.
3.  Yes, potentially: *a period of illness* is health information. The extraction maps it to a category (`illness`, Exercise 4.4) and the free text is not stored beyond the servicer’s own system.
4.  A local model in the firm’s environment: the data does not leave.
5.  The extraction output is stored with the loan; the prompt and the raw note are not logged in text, only their hashes.
6.  Indirectly: the extracted action feeds the monitoring of collections. A person reviews any record flagged by the checks.

**Checking the answer.** Check answers 2 and 5 against the code, not intentions: the extraction prompt contains the whole note (`render(template, note_text=note["text"])`), so names *are* sent unless a removal step is added before the call; and `log_event()` in the service logs the question text. The screening reveals two changes the code needs before real notes are used: a redaction step and a log that stores hashes.

**Mistakes to avoid.**

- Answering *“no personal data”* because loan identifiers are not names. A loan identifier identifies a borrower to anyone with access to the servicer’s system.
- Answering for the fictional data. The screening is for the real use.

**Trade-offs.** The presence of potential health information and the effect on individuals’ accounts point towards a full DPIA. The controller decides, after seeking the advice of the data protection officer (GDPR Article 35(2)). Redacting names and logging hashes reduces the risk at a small cost: a reviewer debugging an extraction needs access to the original note in the servicer’s system rather than in the log.

### Exercise 20.4

**What the question asks.** Classify four changes to the factsheet commentary (AI-AM-02) as material or not, and justify each.

**The plan.** Use one principle: a change is material when it can change outputs in a way the existing evidence does not cover. Apply it to each change.

**Step by step.**

*(a) Moving to a larger local model — material.* Every output can change. Re-run the full evaluation, update the card, validate before release.

*(b) Correcting a typo in the prompt — not material in itself, but the prompt’s hash changes.* The release gate re-runs the evaluation (it costs minutes). If no case changes, release with a note; if any case changes, it was not a typo in effect, and it becomes material.

*(c) Adding a forbidden phrase — not material for validation.* It only adds a check that can reject outputs; it cannot make an output wrong. Record it in the change log; compliance owns the list.

*(d) Temperature from 0.3 to 0.7 — material.* Outputs become more varied, and the rate of unsupported figures can rise (Exercise 13.3). Re-run the evaluation several times, since outputs differ between runs, and compare the review rate in monitoring after release.

**Reading the result.** Two material changes (a, d), one non-material change confirmed by a re-run (b), one non-material change recorded (c).

**Checking the answer.** Apply the principle in reverse: for each change, ask whether the current evaluation results still describe the system. For (a) and (d), no: they were measured with another model or temperature. For (b), only the re-run can say. For (c), yes: every output that passed before still passes or is newly rejected, which is safer.

**Mistakes to avoid.**

- Classifying by effort: (a) is one line in a configuration file and is the most material of the four.
- Skipping the re-run for (b) because “it’s only a typo”. The hash is how the firm knows which prompt produced which output.

**Trade-offs.** Strict change control slows releases; loose change control lets untested behaviour reach clients. The re-run of an automated evaluation is what makes strict control cheap: minutes instead of a committee. Material changes still need a person’s sign-off, recorded with the evidence.

### Exercise 20.5

**What the question asks.** A reviewer approved 240 commentaries in one hour. Say what this tells you and what you would change.

**The plan.** (1) Compute the time per item. (2) Compare with what a review needs. (3) Decide whether the control operates. (4) Propose changes.

**Step by step.** $3{,}600 / 240 = 15$ seconds per commentary. A careful review compares four sentences with their facts and reads the claims without figures (Exercise 13.2): a minute or more.

**Reading the result.** Approval has become a formality. Either the reviewer trusts the checks to do everything, or the reviewer is overloaded. In both cases the control written in the inventory, *portfolio manager approves*, is not operating as designed, which a validator or an auditor would report.

**Checking the answer.** Look for the evidence in the log: approval timestamps 15 seconds apart, and no edits or rejections among the 240. Check a sample: give a second reviewer 20 of the 240 and count what they would have changed. If they find nothing, the checks may be sufficient and the control should be redesigned; if they find errors, the review was not happening.

**Mistakes to avoid.**

- Blaming the reviewer. The process put 240 items in front of one person.
- Adding a mandatory delay before the *Approve* button. Time spent is not attention paid.

**Trade-offs.** Monitor approval time per item and alert on very short times; show reviewers only what needs judgement (claims without figures highlighted); split the volume across reviewers; sample approved commentaries weekly for a second review. If the volume is structural, re-tier the use case honestly and strengthen the automatic checks rather than pretend the review happens. A control that exists only on paper is worse than none: it gives false assurance.
