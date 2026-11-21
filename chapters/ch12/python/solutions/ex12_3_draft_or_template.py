# Exercise 12.3 - The model's draft, or the template
# Run from the root of the repository:  python chapters/ch12/python/solutions/ex12_3_draft_or_template.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.dq import RULES, run_rules

tape = pd.read_csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv")
from aie.dq_email import check_email, draft_email, template_email

found = run_rules(tape, "2026-09-30")
draft, version = draft_email(found, "30 September 2026", "7 October 2026")
problems = check_email(draft, found)
email = draft if not problems else template_email(
    found, "30 September 2026", "7 October 2026")
print(problems or "draft accepted")
print(email)
