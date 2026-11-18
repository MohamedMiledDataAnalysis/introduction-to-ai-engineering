"""Assemble the documentation of one AI use case from the repository's own evidence."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from aie.evals import run_eval, wilson_interval
from aie.monitor import daily_metrics, load_log


def prompt_hash(name):
    text = Path(f"prompts/{name}.txt").read_text(encoding="utf-8").rstrip("\n")
    return hashlib.sha256(text.encode()).hexdigest()[:10]


def model_card(use_case_id, eval_file, answers_file, log_file):
    inv = pd.read_csv("governance/inventory.csv").set_index("id").loc[use_case_id]
    cases = pd.read_csv(eval_file, dtype=str, keep_default_na=False)
    answers = pd.read_csv(answers_file).set_index("id")["answer"].to_dict()
    res = run_eval(cases, answers)
    low, high = wilson_interval(res.passed.sum(), len(res))
    m = daily_metrics(load_log(log_file))
    m = m[m.domain == inv.domain]
    lines = [f"# Model card — {use_case_id} {inv['name']}", "",
             "| Item | Value |", "|---|---|",
             *[f"| {k.replace('_', ' ').capitalize()} | {inv[k]} |" for k in
               ["purpose", "users", "decision_impact", "model", "human_review", "data", "owner", "risk_tier"]],
             f"| Prompt version | {inv['prompt']} (hash {prompt_hash(inv['prompt'])}) |", "",
             "## Evaluation", "",
             f"- Evaluation set: `{eval_file}`, {len(res)} cases.",
             f"- Result: {res.passed.sum()}/{len(res)} passed (95% interval {low:.0%} to {high:.0%}).",
             f"- Failed cases: {', '.join(res[~res.passed].id) or 'none'}.", "",
             "## Monitoring (period of the log)", "",
             f"- Requests: {int(m.requests.sum())}; days: {m.day.nunique()}.",
             f"- Error rate: {(m.error_rate * m.requests).sum() / m.requests.sum():.1%}.",
             f"- Review rate (median day): {m.review_rate.median():.1%}; worst day: {m.review_rate.max():.1%}.",
             f"- Median response time (median day): {m.p50_seconds.median():.1f} s.", "",
             "## Known limitations", "",
             "- Small evaluation set: the interval above is wide.",
             "- Answers are limited to the prospectus excerpt; other documents are out of scope.", "",
             "## Sign-off", "", "| Role | Name | Date |", "|---|---|---|",
             "| Owner | | |", "| Model validation | | |", "| Compliance | | |"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    card = model_card("AI-SF-01", "evals/sf_prospectus_qa.csv", "evals/candidates/prospectus_qa_run_a.csv",
                      "data/logs/requests_2026_10.jsonl")
    Path("governance/model_card_AI-SF-01.md").write_text(card, encoding="utf-8")
    print(card)
