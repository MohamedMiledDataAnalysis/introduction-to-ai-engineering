"""Check a summary of a research note: faithful (nothing new), complete (key facts present), consistent, short."""
import re

from aie.factcheck import extract_figures

RECS = ("buy", "hold", "sell")


def check_summary(summary, note, key, max_words=60):
    problems = []
    note_values = {(f.unit, round(f.value * f.scale, 4)) for f in extract_figures(note)}
    for f in extract_figures(summary):                                   # 1. faithful: no figure absent from the note
        if (f.unit, round(f.value * f.scale, 4)) not in note_values:
            problems.append(f"figure {f.raw} is not in the note")
    said = [r for r in RECS if re.search(rf"\b{r}\b", summary, re.I)]    # 2. consistent recommendation
    if said and said != [key["recommendation"].lower()]:
        problems.append(f"recommendation {said} differs from the note ({key['recommendation']})")
    required = {"recommendation": key["recommendation"].lower() in summary.lower(),   # 3. complete
                "target price": f"{key['target_price_eur']:.2f}" in summary,
                "revenue growth": f"{key['revenue_growth_pct']:.1f}%" in summary,
                "main risk": sum(w in summary.lower() for w in key["main_risk"].lower().split() if len(w) > 3) >= 2}
    problems += [f"missing: {k}" for k, ok in required.items() if not ok]
    if len(summary.split()) > max_words:                                  # 4. short
        problems.append(f"{len(summary.split())} words, limit {max_words}")
    return problems


def summarise_note(nid):
    from aie.llm import chat
    from aie.prompts import load_prompt, render
    note = open(f"data/am/research/{nid}.md", encoding="utf-8").read()
    template, version = load_prompt("summarise_note_v1")
    return chat([{"role": "user", "content": render(template, note=note)}])["text"].strip(), version
