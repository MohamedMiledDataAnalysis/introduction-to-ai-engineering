"""
Check every figure written in a text against a table of facts computed by code.

A figure "matches" a fact when the fact, expressed in the figure's unit and rounded
to the number of decimals the figure shows, equals the figure. "£4.88 million"
matches 4,882,267.39; "0.84%" matches 0.8432 (a percentage).
"""
import re
from dataclasses import dataclass

SCALE = {"": 1, "k": 1e3, "thousand": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6, "bn": 1e9, "billion": 1e9}
FIGURE = re.compile(
    r"(?P<cur>[£€$])?\s?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"\s?(?:(?P<pct>%|per cent|bps?\b|basis points)|(?P<scale>million|billion|thousand|bn|mn|m|k)\b)?",
    re.I)
IGNORE_CONTEXT = re.compile(r"(19|20)\d{2}$")          # years
MONTH = r"(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b"


@dataclass
class Figure:
    raw: str
    value: float          # in the unit written (e.g. 4.88 for "£4.88 million")
    decimals: int
    unit: str             # "money", "percent", "bp" or "number"
    scale: float
    start: int


def extract_figures(text):
    figures = []
    for m in FIGURE.finditer(text):
        num = m.group("num")
        before = text[max(0, m.start() - 12):m.start()]
        if IGNORE_CONTEXT.fullmatch(num) and not m.group("cur") and not m.group("pct"):
            continue                                    # a year such as 2026
        if re.search(r"(Class|item|section|LMF25-|\()\s?$", before, re.I):
            continue                                    # labels: Class A, item (l), loan ids
        if re.search(r"\d[-/]$", before) or (text[m.end():m.end() + 1] and text[m.end():m.end() + 1] in "-/"):
            continue                                    # dates such as 30/09/2026 or 2026-09-30
        if not m.group("cur") and not m.group("pct") and (re.match(r"\s?" + MONTH, text[m.end():], re.I)
                                                          or re.search(MONTH + r"\s?$", before, re.I)):
            continue                                    # dates such as 30 September or September 30
        pct = (m.group("pct") or "").lower()
        unit = "percent" if pct in ("%", "per cent") else "bp" if pct else "money" if m.group("cur") else "number"
        if unit == "number" and re.match(r"\d", text[m.end():m.end() + 1] or " "):
            continue
        scale = SCALE[(m.group("scale") or "").lower()] if unit in ("money", "number") else 1
        decimals = len(num.split(".")[1]) if "." in num else 0
        figures.append(Figure(m.group(0).strip(), float(num.replace(",", "")), decimals, unit, scale, m.start()))
    return figures


def matches(fig, fact_value, fact_unit):
    if fact_unit == "percent" and fig.unit == "bp":
        candidate = abs(fact_value) * 100
    elif fact_unit != fig.unit:
        return False
    else:
        candidate = abs(fact_value) / fig.scale
    return round(candidate, fig.decimals) == round(fig.value, fig.decimals)


def check_text(text, facts):
    """facts: dict name -> (value, unit). Returns a list of (figure, matched fact names)."""
    report = []
    for fig in extract_figures(text):
        hits = [name for name, (v, u) in facts.items() if matches(fig, v, u)]
        report.append((fig, hits))
    return report


NEGATIVE_CUE = re.compile(r"\b(fell|fall|falls|falling|down|lost|loss|losses|lower|below|behind|lag\w*|trail\w*|"
                          r"underperform\w*|detract\w*|declin\w*|negative|minus|drop\w*|short\w*|deficit|reduc\w*)\b",
                          re.I)


def sign_agrees(text, fig, fact_value, window=40):
    """matches() compares absolute values, so that "fell by 1.43%" matches -1.43. This restores the sign:
    a figure written with a minus needs a negative fact; a negative fact needs a minus or a word such as
    "fell", "behind" or "detracted" just before the figure."""
    i = fig.start
    minus = text[max(0, i - 2):i].replace(" ", "")[-1:] in ("-", "\u2212")
    if minus:
        return fact_value < 0
    if fact_value < 0:
        return bool(NEGATIVE_CUE.search(text[max(0, i - window):i]))
    return True


def check_signed(text, facts):
    """check_text() with the sign restored: the agent and explain_result() use this one."""
    return [(fig, [n for n in hits if sign_agrees(text, fig, facts[n][0])]) for fig, hits in check_text(text, facts)]


FORBIDDEN = [r"\bguarantee[ds]?\b", r"\brisk[- ]free\b", r"\bwill (outperform|rise|increase)\b",
             r"\bcertain(ly)? to\b", r"\bno risk\b", r"\byou should (buy|sell|invest)\b"]


def forbidden_phrases(text):
    return [m.group(0) for p in FORBIDDEN for m in re.finditer(p, text, re.I)]
