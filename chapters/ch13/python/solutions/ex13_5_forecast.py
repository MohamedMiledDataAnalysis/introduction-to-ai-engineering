# Exercise 13.5 - A forecast added after approval
# Run from the root of the repository:  python chapters/ch13/python/solutions/ex13_5_forecast.py

import re

FORECAST = [r"\bwe expect\b", r"\bwill (recover|rebound|rise|fall)\b", r"\bis set to\b"]

edited = ("Stock selection and sector allocation both detracted. "
          "We expect real estate to recover in the fourth quarter.")
print([m.group(0) for p in FORECAST for m in re.finditer(p, edited, re.I)])
