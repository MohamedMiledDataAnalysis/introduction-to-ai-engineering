# Exercise 22.2 - Ongoing costs of two funds
# Run from the root of the repository:  python chapters/ch22/python/solutions/ex22_2_ongoing_costs.py

import sys; sys.path.insert(0, ".")
from aie.tools import run_tool

print(run_tool({"name": "search_fund_documents",
                "arguments": {"query": "ongoing costs", "fund_code": "HGEF"}}))
print(run_tool({"name": "search_fund_documents",
                "arguments": {"query": "ongoing costs", "fund_code": "HECB"}}))
