# Exercise 5.4 - Is run A better than run B?
# Run from the root of the repository:  python chapters/ch05/python/solutions/ex5_4_significance.py

import sys; sys.path.insert(0, ".")

from aie.evals import wilson_interval
print(wilson_interval(19, 20))
print(wilson_interval(16, 20))

from math import comb
a_only, b_only = 4, 1                      # cases only A passes, only B passes
n = a_only + b_only
p = 2 * sum(comb(n, k) for k in range(min(a_only, b_only) + 1)) / 2 ** n
print(n, round(min(p, 1.0), 3))
