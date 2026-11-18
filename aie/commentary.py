"""Facts for a fund commentary, and a checker that verifies value, label and direction of every figure."""
import re

import pandas as pd

from aie.factcheck import extract_figures, matches

POSITIVE = ("contributed", "added", "helped", "ahead", "outperform", "beat", "positive")
NEGATIVE = ("detracted", "cost", "hurt", "weighed", "behind", "lag", "underperform", "negative", "subtracted")


def hgef_facts(month="2026-09-30"):
    nav = pd.read_csv("data/am/fund_nav_monthly.csv")
    bm = pd.read_csv("data/am/benchmark_returns_monthly.csv").set_index("month_end")
    fund = nav[(nav.fund_code == "HGEF") & (nav.month_end == month)].net_return.iloc[0]
    bench = bm.loc[month, "HGEF"]
    attr = pd.read_csv("data/am/hgef_attribution_2026_09.csv")
    attr["total"] = attr.allocation + attr.selection + attr.interaction
    facts = {"fund return": (100 * fund, "percent", ["fund", "returned", "return"], False),
             "benchmark return": (100 * bench, "percent", ["benchmark", "index"], False),
             "relative return": (100 * (fund - bench), "percent", ["relative", "benchmark", "lag", "behind", "ahead",
                                                                   "outperform", "underperform"], True)}
    for r in attr.itertuples():
        name = r.sector
        facts[f"{name} effect"] = (100 * r.total, "percent", [name.lower(), name.split()[0].lower()], True)
        facts[f"{name} active weight"] = (100 * (r.portfolio_weight - r.benchmark_weight), "percent",
                                          [name.lower(), name.split()[0].lower(), "weight", "overweight",
                                           "underweight"], False)
        for label, w in (("fund weight", r.portfolio_weight), ("benchmark weight", r.benchmark_weight)):
            facts[f"{name} {label}"] = (100 * w, "percent", [name.lower(), name.split()[0].lower(), "weight",
                                                             "overweight", "underweight", "against"], False)
    return facts, attr


def check_commentary(text, facts, window=90):
    report = []
    for fig in extract_figures(text):
        before = text[max(0, fig.start - window):fig.start].lower()
        sentence = re.split(r"[.;]\s", before)[-1]             # the figure's sentence
        clause = re.split(r",\s", sentence)[-1]                # the figure's clause
        label_hits = lambda ctx: [n for n, (v, u, keys, _) in facts.items()
                                  if matches(fig, v, u) and any(k in ctx for k in keys)]
        hits = label_hits(clause) or label_hits(sentence)
        problem = None if hits else "no fact with this value and label"
        for n in hits:
            value, _, _, signed = facts[n]
            if signed and value < 0 and any(w in clause for w in POSITIVE):
                problem = f"says positive, {n} is negative"
            if signed and value > 0 and any(w in clause for w in NEGATIVE):
                problem = f"says negative, {n} is positive"
        report.append((fig.raw, hits, problem))
    return report


def facts_for_prompt(attr, fund, bench):
    """The facts the model may quote, already rounded and in words: the model never computes."""
    lines = [f"- Fund return: {100 * fund:.2f}%", f"- Benchmark return: {100 * bench:.2f}%",
             f"- Relative return: {100 * (fund - bench):+.2f}%"]
    ranked = attr[attr.sector != "Cash"].sort_values("total")
    for r in list(ranked.head(2).itertuples()) + list(ranked.tail(2).itertuples())[::-1]:
        side = "overweight" if r.portfolio_weight > r.benchmark_weight else "underweight"
        lines.append(f"- {r.sector}: total effect {10000 * r.total:+.1f}bp "
                     f"({'contributed' if r.total > 0 else 'detracted'}); the fund was {side} "
                     f"({100 * r.portfolio_weight:.2f}% against {100 * r.benchmark_weight:.2f}%)")
    return "\n".join(lines)


def draft_commentary(month="2026-09-30"):
    from aie.llm import chat
    from aie.prompts import load_prompt, render
    facts, attr = hgef_facts(month)
    fund, bench = facts["fund return"][0] / 100, facts["benchmark return"][0] / 100
    template, version = load_prompt("fund_commentary_v1")
    prompt = render(template, fund_name="Harbourline Global Equity Fund", month="September 2026",
                    facts=facts_for_prompt(attr, fund, bench))
    text = chat([{"role": "user", "content": prompt}], temperature=0.3)["text"].strip()
    return text, check_commentary(text, facts), version
