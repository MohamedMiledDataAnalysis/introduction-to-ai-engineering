# Chapter 12 - The model drafts the query to the servicer; code checks that it lists exactly the flagged loans
import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.dq import run_rules
from aie.dq_email import check_email, template_email

found = run_rules(pd.read_csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv"), "2026-09-30")
email = template_email(found, "30 September 2026", "7 October 2026")
print(email[:420], "...\n")
print("Check of the template email:", check_email(email, found) or "complete and exact")

second = found.loan_id.iloc[1]
draft = email.replace(second, second[:-3] + second[-2] + second[-3] + second[-1])    # two digits transposed
draft = draft.replace(f"- {found.loan_id.iloc[0]}: ", "- ")                           # one loan id dropped
print("Check of a faulty draft:   ", check_email(draft, found))
