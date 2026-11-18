# 9. Agents: Letting the Model Plan the Steps

## Exercises

**Exercise 9.1.** Run the Larkfield agent with Ollama on three questions: (a) *What is the Class B coupon for the September 2026 period?* (b) *Can the reserve fund be used to repay principal?* (c) *What was the arrears ratio in October 2026?* For each, read the trace and explain the agent’s choices and its status.

**Exercise 9.2.** Ask *“What was the pool balance at 30 September 2026?”*, then the follow-up *“And at the end of August?”* passing the first exchange as history. Show the code in Python and R, and explain what the agent must infer from the history.

**Exercise 9.3.** Run the correction scenario with `max_steps=3`. What status do you get, and why? What does this teach you about choosing `max_steps`?

**Exercise 9.4.** The monthly Larkfield commentary always needs the same figures. Write it as a workflow: compute the facts with the tools directly (no model choosing), ask the model to write the paragraph from those facts, check the figures. Compare with running the agent on *“Write the September 2026 investor commentary”*.

**Exercise 9.5.** Change the agent so that it refuses any question about Harbourline funds, without calling the model, when it is configured with structured finance tools only. Where in the code would you put this check, and why not only in the system prompt?

## Corrections

### Exercise 9.1

**What the question asks.** Run the Larkfield agent with your model on three questions, read each trace, and explain the tool choices and the final status.

**The plan.** (1) Run the three questions through `agent.run()` and print each trace with `show()`. (2) For each, compare the trace with the expected trace. (3) Check every figure of the answer against the tool results.

**Step by step.**

``` python
for q in ["What is the Class B coupon for the September 2026 period?",
          "Can the reserve fund be used to repay principal?",
          "What was the arrears ratio in October 2026?"]:
    show(agent.run(q))
```

- `agent` is the `Agent` of `ch09_agent_runs.py`, with four tools: `pool_summary`, `note_balance`, `waterfall_summary`, `search_prospectus`.
- `show()` prints each step of the trace (tool, arguments, start of the result), then the status, the number of steps, any unsupported figures and the answer.

**Reading the result.**

*(a) Class B coupon.* Expected trace: `note_balance` with `note_class` B and `cutoff_date` 2026-09-30. The result contains `"coupon_pct": 4.55`: SONIA for the period (3.45% in the fictional rate path) plus the Class B margin of 1.10%. A good answer quotes 4.55%. Status `verified` if every figure it writes is in the results.

*(b) Reserve fund and principal.* Expected trace: `search_prospectus` with a query about the reserve fund. Two passages answer it: `LMF#3` lists the reserve fund’s uses (items (a) to (c) and interest on the Class A and Class B notes), and `LMF#2` states that it *does not pay principal* and is therefore excluded from credit enhancement. A correct answer says no and cites one or both; any figure it quotes (1.50%, £6,082,667.80) is in the passage, so verification passes.

*(c) October 2026.* Expected trace: `pool_summary` with `cutoff_date` 2026-10-31, and the result:

``` text
{"error": "no data for 2026-10-31; available month-ends run from 2025-06-30 to 2026-09-30"}
```

A good answer says the data ends in September 2026 and may offer the September figure, 0.84%. A bad answer invents an October figure: verification reports it, the model gets one correction, and if the figure remains the status is `needs_review`.

**Checking the answer.** Call the tools yourself, as in Chapter 8, and compare: `note_balance("B", "2026-09-30")` returns `coupon_pct` 4.55, and `pool_summary("2026-10-31")` returns the error above. The agent’s answer can only be right if it uses these exact results.

**Mistakes to avoid.**

- Judging the run by the answer alone. A right answer with a wrong trace (for example, the coupon taken from the prospectus margin plus a guessed SONIA) is a lucky answer.
- Reading `verified` as *correct*. It means every figure is supported by a tool result; a well-supported answer to the wrong question is still `verified`.

**Trade-offs.** For each trace ask three questions: did the agent call the minimum tools needed, did it translate dates correctly, did it read error messages and act on them? This manual checklist does not scale, which is why Chapter 21 turns it into an evaluation with measured tool choice; but on three questions it teaches more than any score.

### Exercise 9.2

**What the question asks.** Ask a question, then a follow-up that only makes sense with the first exchange, passing the history, in Python and R; explain what the agent must infer.

**The plan.** (1) Run the first question. (2) Build the history from the question and the final answer. (3) Run the follow-up with that history. (4) Read the follow-up’s tool call.

**Step by step.**

``` python
first_q = "What was the pool balance at 30 September 2026?"
first = agent.run(first_q)
history = [{"role": "user", "content": first_q},
           {"role": "assistant", "content": first["answer"]}]
second = agent.run("And at the end of August?", history=history)
show(second)
```

- `history` is a list of messages in the same format as the conversation: who spoke (`role`) and what was said (`content`).
- `agent.run(..., history=history)` puts these messages before the new question, so the model reads the earlier exchange.

``` r
source("aie_r/agent.R")
first_q <- "What was the pool balance at 30 September 2026?"
first   <- run_agent(first_q, system_prompt, tool_names)
history <- list(list(role = "user", content = first_q),
                list(role = "assistant", content = first$answer))
second  <- run_agent("And at the end of August?", system_prompt,
                     tool_names, history = history)
```

- `system_prompt` and `tool_names` are the same as in Python; `run_agent()` takes the history as its last argument.

**Reading the result.** The follow-up’s trace should show `pool_summary` with `cutoff_date` `2026-08-31`, and the answer £327,600,033.97. From the history the agent must infer two things: *“And”* continues the question about the **pool balance**, and *the end of August* means **2026-08-31**, the month before the date discussed, not August 2025.

**Checking the answer.** Call `pool_summary("2026-08-31")` directly: `pool_balance_gbp` is 327600033.97. Then run the follow-up **without** history: the model has no subject for *“And at the end of August?”* and either asks what is meant or guesses; the difference shows what the history contributed.

**Mistakes to avoid.**

- Putting the first run’s tool calls and results in the history. It works, but it multiplies the tokens of every later turn.
- Storing the history as one string: the model then cannot tell who said what.

**Trade-offs.** The history holds questions and final answers only; the agent calls the tools again for the new date. This keeps each turn short and every figure fresh from a tool. Sending the full earlier trace would let the model reuse results, at a higher token cost and with the risk that it quotes an old result for a new date.

### Exercise 9.3

**What the question asks.** Replay the correction scenario with a step limit of 3, read the status, and draw a rule for choosing `max_steps`.

**The plan.** (1) Start the mock with the correction script. (2) Run the agent with `max_steps=3`. (3) Count the steps the scenario needs. (4) Run again with the default limit to compare.

**Step by step.**

``` bash
MOCK_SCRIPT=tools/scripts/ch09_correction.json python tools/mock_ollama.py
```

``` python
agent3 = Agent(SYSTEM, ["pool_summary", "note_balance", "waterfall_summary",
                        "search_prospectus"], max_steps=3)
show(agent3.run(question))
```

The script replays four model replies: a call to `waterfall_summary`, a call to `search_prospectus`, an answer with excess spread of £629,429.96 (digits swapped), and a corrected answer with £692,429.96.

In `Agent.run()`, each loop iteration is one step, one model call:

``` python
for step in range(1, self.max_steps + 1):
    reply = chat(messages, system=self.system, tools=tools)
```

**Reading the result.** Step 1 and step 2 are the tool calls. Step 3 is the first answer: verification finds £629,429.96 unsupported, adds a `verification` line to the trace and asks for a correction. The correction would be step 4, but the loop has ended:

``` text
  status=stopped steps=3 unsupported=[]
  answer: stopped: step limit reached
```

**Checking the answer.** Restart the mock and run with `max_steps=6`: the same scenario ends with status `verified` in 4 steps. The only difference is the limit, so the limit caused the stop.

**Mistakes to avoid.**

- Raising `max_steps` to 20 “to be safe”. A looping agent then makes 20 model calls before stopping, and each call costs tokens and seconds.
- Forgetting the correction round when counting: a question that needs two tool steps and an answer needs **four** steps if the first answer fails verification.

**Trade-offs.** Count the steps your evaluation questions need (here 2 tool steps + 1 answer + 1 correction = 4) and set the limit a little above the largest typical count, here 6. Too low, and good runs are cut off; too high, and loops cost more before they stop. The token budget (`max_tokens`) is a second limit that catches long runs the step count allows.

### Exercise 9.4

**What the question asks.** Write the monthly commentary as a **workflow**: compute the facts with the tools in code, have the model write the paragraph from those facts, check the figures. Compare with asking the agent to write the commentary.

**The plan.** (1) Call the three tools directly. (2) Send the facts and a writing instruction to the model. (3) Check the draft against the same facts. (4) Compare predictability and cost with the agent.

**Step by step.**

*Step 1 — Facts, in code.*

``` python
import json
from aie.tools import note_balance, pool_summary, waterfall_summary
from aie.agent import facts_from_results
from aie.factcheck import check_text

d = "2026-09-30"
results = [("waterfall_summary", json.dumps(waterfall_summary(d))),
           ("pool_summary", json.dumps(pool_summary(d))),
           ("note_balance", json.dumps(note_balance("A", d)))]
```

- The tool functions are called directly, not through a model: the same three calls every month.
- Each result is stored as `(tool name, JSON string)`, the format `facts_from_results()` expects.

*Step 2 — The model writes.*

``` python
prompt = ("Write a four-sentence investor commentary for Larkfield "
          "Mortgage Funding 2025-1 for the period ending 30 September 2026, "
          "using only these figures, quoted as given:\n"
          + "\n".join(r for _, r in results))
draft = chat([{"role": "user", "content": prompt}])["text"]
```

*Step 3 — Check.*

``` python
facts = facts_from_results(results)
for fig, hits in check_text(draft, facts):
    print(fig.raw, "OK" if hits else "NOT SUPPORTED")
```

**Reading the result.** The draft is checked figure by figure. As a reference, Draft 1 of Chapter 6 checked against these facts passes completely: £1.86 million, £4.88 million (twice), £274.06 million, 0.84%, £322.7 million, £6,082,667.80 and £0.69 million are all supported.

**Checking the answer.** Run the workflow three times: the tool calls and the facts are identical each time, and only the wording may change. Then ask the agent *“Write the September 2026 investor commentary”* three times and compare the traces: on some runs it skips the arrears figure, on others it searches the prospectus first. The comparison is the answer to the exercise.

**Mistakes to avoid.**

- Letting the model compute anything in the workflow (a percentage change, a ratio). Compute it in Step 1 and add it to the facts.
- Checking the draft against facts other than those sent to the model: the check must use the same `results`.

**Trade-offs.** The workflow makes three tool calls and one model call every month; its cost and duration are constant and its content predictable, which is what a monthly production process needs. It cannot answer a question you did not foresee. Keep the workflow for the commentary and the agent for investor questions: that is the design of the final project, where Chapter 14’s investor report is a workflow and Chapter 21’s assistant is an agent.

### Exercise 9.5

**What the question asks.** Make the structured finance agent refuse questions about Harbourline funds without calling the model, decide where the check goes, and explain why a system prompt alone is not enough.

**The plan.** (1) Choose the place: before the first model call. (2) Write a pattern of words that identify the other domain. (3) Return a fixed refusal. (4) Test on an in-scope question that shares words.

**Step by step.**

``` python
AM_TERMS = re.compile(r"\b(harbourline|hgef|hecb|hbma)\b", re.I)

def run(self, question, history=None):
    if (not set(self.tool_names) & {"fund_performance", "top_holdings"}
            and AM_TERMS.search(question)):
        return self._end("This assistant covers Larkfield Mortgage Funding "
                         "2025-1 only.", [], 0, 0, "out_of_scope")
    ...
```

- `set(self.tool_names) & {...}` is empty when the agent has no fund tools: the agent is configured for structured finance.
- `AM_TERMS` matches the firm’s name and the three fund codes, as whole words.
- `self._end(...)` returns the usual result dictionary with zero steps and zero tokens, and status `out_of_scope`.

**Reading the result.** *“What is the ongoing charge of HECB?”* returns the refusal at once, with `steps=0` and `tokens=0`. *“Does the Larkfield reserve fund pay principal?”* runs normally: it contains *fund*, but none of the patterns.

**Checking the answer.** Check that no model call was made: start the mock server with an empty script; the out-of-scope question still returns its refusal, because the mock is never reached. Chapter 21 uses this design in `aie/assistants.py` (and `aie_r/assistants.R`), where the guards run before the agent for both domains.

**Mistakes to avoid.**

- Matching generic words such as *fund*: *“Does the Larkfield reserve fund…”* would be refused.
- Putting the check after the first model call: the refusal then costs tokens, and the model may already have answered from its general knowledge.

**Trade-offs.** The prompt makes the model *likely* to decline; the check makes it *certain*, and free. The allow-list of Chapter 8 already prevents the agent from reaching fund data; this check also prevents it from answering from the model’s general knowledge, which is where an out-of-scope answer would come from. A keyword list misses questions that do not name the fund (*“the euro bond fund’s costs”*); add such questions to the evaluation set to measure both kinds of error, and extend the list from what you find.
