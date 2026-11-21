# Exercise 8.1 - The arrears_buckets tool
# Run from the root of the repository:  python chapters/ch08/python/solutions/ex8_1_arrears_buckets.py

import sys

sys.path.insert(0, ".")
from aie.tools import REGISTRY, run_tool

print(REGISTRY["arrears_buckets"][1])
print(run_tool({"name": "arrears_buckets", "arguments": {"cutoff_date": "2026-09-30"}}))
print(run_tool({"name": "arrears_buckets", "arguments": {"cutoff_date": "2026-09"}}))
