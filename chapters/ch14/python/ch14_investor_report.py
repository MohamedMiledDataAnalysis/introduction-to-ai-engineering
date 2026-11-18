# Chapter 14 - Build the September 2026 investor report: reconcile, compute, comment, check, render
import sys
from pathlib import Path

sys.path.insert(0, ".")
from aie.investor_report import (check_commentary, facts_for_prompt, month_figures, reconcile,
                                 render_markdown, template_commentary)

f = month_figures("2026-09-30")
checks = reconcile(f)
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
if not all(checks.values()):
    sys.exit("Reconciliation failed: the report is not produced.")

print("\nFacts given to the model:\n" + facts_for_prompt(f))
commentary = template_commentary(f)          # replaced by the model's draft in Exercise 14.3
print("\nCommentary:", commentary)
print("Check:", [(raw, "OK" if hits else "NOT SUPPORTED") for raw, hits in check_commentary(commentary, f)])
Path("reports").mkdir(exist_ok=True)
Path("reports/larkfield_investor_report_2026_09.md").write_text(render_markdown(f, commentary), encoding="utf-8")
print("\nWritten: reports/larkfield_investor_report_2026_09.md")
