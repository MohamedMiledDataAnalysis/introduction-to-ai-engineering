# Exercise 14.5 - Direction words for the arrears ratio
# Run from the root of the repository:  python chapters/ch14/python/solutions/ex14_5_direction_words.py

import sys

import re
UP = ("rose", "increased", "up", "higher", "worsened")
DOWN = ("fell", "decreased", "down", "lower", "improved")

def arrears_direction_errors(text, f):
    change = f["arrears_ratio"] - f["prev_arrears_ratio"]
    errors = []
    for sentence in re.split(r"(?<=\.)\s", text):
        s = sentence.lower()
        if "arrears" not in s:
            continue
        if change < 0 and any(re.search(rf"\b{w}\b", s) for w in UP):
            errors.append(f"says up, arrears fell: {sentence}")
        if change > 0 and any(re.search(rf"\b{w}\b", s) for w in DOWN):
            errors.append(f"says down, arrears rose: {sentence}")
    return errors

sys.path.insert(0, ".")
from aie.investor_report import month_figures, template_commentary

f = month_figures("2026-09-30")
text = template_commentary(f)
print(arrears_direction_errors(text, f) or "no error")
print(arrears_direction_errors(text.replace("fell", "rose"), f))
