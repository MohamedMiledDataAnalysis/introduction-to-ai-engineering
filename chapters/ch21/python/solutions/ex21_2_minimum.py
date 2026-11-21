# Exercise 21.2 - The share, in its minimum form (the full solution: ex21_2_arrears_share.py)
# Run from the root of the repository:  python chapters/ch21/python/solutions/ex21_2_minimum.py

import sys; sys.path.insert(0, ".")

from aie.tools import arrears_buckets
b = arrears_buckets("2026-09-30")["buckets"]
three_plus = sum(x["balance_gbp"] for x in b if x["bucket"] in ("3 months", "4-5 months"))
total = sum(x["balance_gbp"] for x in b)
print(three_plus, total, round(100 * three_plus / total, 2))
