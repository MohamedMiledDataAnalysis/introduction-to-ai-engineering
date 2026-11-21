# Exercise 14.2 - The model's commentary, with a fallback
# Run from the root of the repository:  python chapters/ch14/python/solutions/ex14_2_model_commentary.py

import shutil
import sys
from pathlib import Path

sys.path.insert(0, ".")
from aie.investor_report import (check_commentary, facts_for_prompt, month_figures,
                                 template_commentary)
from aie.llm import chat
from aie.prompts import load_prompt, render

# the prompt you saved, or the repository's reference copy if you have not written it yet
if not Path("prompts/investor_commentary_v1.txt").exists():
    shutil.copy("prompts/solutions/investor_commentary_v1.txt", "prompts/")

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

for d in ("2026-09-30", "2026-03-31"):
    text, record = draft_commentary(month_figures(d))
    print(d, record)
    print(text, "\n")
