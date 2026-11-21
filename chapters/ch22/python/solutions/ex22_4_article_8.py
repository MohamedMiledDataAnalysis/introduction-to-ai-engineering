# Exercise 22.4 - Is HGEF an Article 8 fund?
# Run from the root of the repository:  python chapters/ch22/python/solutions/ex22_4_article_8.py

import sys; sys.path.insert(0, ".")
from aie.tools import run_tool

print(run_tool({"name": "search_fund_documents",
                "arguments": {"query": "Is HGEF an Article 8 fund? "
                                       "sustainability characteristics met",
                              "fund_code": "HGEF", "k": 3}}))
