"""Score answers against an evaluation set and compare runs."""
import re

import pandas as pd

REFUSAL = re.compile(r"do(es)? not (state|mention|contain|name|say|give|include|specify)|"
                     r"not (stated|mentioned|given) in|not in the (document|text)|no information|covers .{3,60} only|"
                     r"cannot give investment advice|no data for|data (is available|ends)", re.I)
NUMBER = re.compile(r"-?\d[\d,]*\.?\d*")


def numbers_in(text):
    """All numbers written in a text, as floats (commas removed)."""
    return [float(n.replace(",", "")) for n in NUMBER.findall(text) if any(ch.isdigit() for ch in n)]


def score_one(case, answer):
    """Return (passed, reason)."""
    answer = re.sub(r"\[[A-Z][A-Za-z\-]*#[\d.]+\]", "", answer)     # citations are not part of the answer's content
    kind = case["answer_type"]
    if kind == "number":
        target, tol = float(case["expected"]), float(case["tolerance"])
        found = numbers_in(answer)
        ok = any(abs(x - target) <= tol for x in found)
        return ok, "number found" if ok else f"expected {case['expected']}, found {found}"
    if kind == "text":
        options = [k.strip().lower() for k in str(case["keywords"]).split("|")]
        ok = any(k in answer.lower() for k in options)
        return ok, "keyword found" if ok else f"none of {options}"
    if kind == "ordered":
        pos = 0
        for label in str(case["expected"]).split(","):
            m = re.compile(rf"\b(Class )?{label.strip()}\b").search(answer, pos)
            if not m:
                return False, f"'{label}' missing or out of order"
            pos = m.end()
        return True, "order correct"
    if kind == "not_in_document":
        ok = bool(REFUSAL.search(answer))
        return ok, "declined correctly" if ok else "answered instead of declining"
    raise ValueError(f"unknown answer_type {kind}")


def run_eval(cases, answers):
    """cases: DataFrame of the evaluation set; answers: dict id -> answer text."""
    rows = []
    for case in cases.to_dict("records"):
        ans = answers.get(case["id"], "")
        ok, reason = score_one(case, ans)
        rows.append({"id": case["id"], "answer_type": case["answer_type"], "passed": ok, "reason": reason})
    return pd.DataFrame(rows)


def compare_runs(before, after):
    """Cases that passed before and fail now (regressions), and the reverse (fixes)."""
    m = before.merge(after, on="id", suffixes=("_before", "_after"))
    return (m[m.passed_before & ~m.passed_after]["id"].tolist(),
            m[~m.passed_before & m.passed_after]["id"].tolist())


def wilson_interval(passed, total, z=1.96):
    """95% confidence interval for a pass rate (Wilson score interval)."""
    if total == 0:
        return (0.0, 1.0)
    p = passed / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
