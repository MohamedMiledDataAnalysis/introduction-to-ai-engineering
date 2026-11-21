# Exercise 8.2 - A tool outside the allowed list
# Run from the root of the repository:  python chapters/ch08/python/solutions/ex8_2_allowed_tools.py

import sys; sys.path.insert(0, ".")
from aie.tools import run_tool

print(run_tool({"name": "pool_summary",
                "arguments": {"cutoff_date": "2026-09-30"}},
               allowed=["fund_performance", "top_holdings"]))
