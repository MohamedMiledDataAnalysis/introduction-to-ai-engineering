# Exercise 6.5 - Two forbidden phrases from compliance
# Run from the root of the repository:  python chapters/ch06/python/solutions/ex6_5_forbidden_phrases.py

import sys

sys.path.insert(0, ".")
import aie.factcheck
from aie.factcheck import forbidden_phrases

# the two patterns added to FORBIDDEN (here in memory; in aie/factcheck.py in the exercise)
aie.factcheck.FORBIDDEN += [
    r"\bcapital[- ]protected\b", r"\bcan('|no)?t lose\b",
]
for s in ["This fund is capital protected.",
          "The fund does not offer any capital protection.",
          "Investors can't lose more than they invest.",
          "You cannot lose money.", "A capital-protected note."]:
    print(forbidden_phrases(s), "<-", s)
