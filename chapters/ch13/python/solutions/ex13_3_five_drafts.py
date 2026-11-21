# Exercise 13.3 - Five drafts of the commentary
# Run from the root of the repository:  python chapters/ch13/python/solutions/ex13_3_five_drafts.py

import sys; sys.path.insert(0, ".")
from aie.commentary import draft_commentary

results = [draft_commentary() for _ in range(5)]
for text, report, version in results:
    problems = [(fig, p) for fig, _, p in report if p]
    print("PASS" if not problems else problems)
