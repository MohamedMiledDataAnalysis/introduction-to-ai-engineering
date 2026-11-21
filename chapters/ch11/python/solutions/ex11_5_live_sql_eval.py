# Exercise 11.5 - Your model on the ten SQL questions
# Run from the root of the repository:  python chapters/ch11/python/solutions/ex11_5_live_sql_eval.py

import sys

import pandas as pd

sys.path.insert(0, ".")
from aie.sqlguard import run_sql, same_result
from aie.text_to_sql import ask_database

cases = pd.read_csv("evals/am_sql_qa.csv")
score = 0
for c in cases.itertuples():
    out = ask_database(c.question)
    ok = "result" in out and same_result(run_sql(c.reference_sql),
                                         out["result"], bool(c.ordered))
    score += ok
    if not ok:
        print(c.id, out.get("sql"), out.get("result", {}).get("error"))
print(score, "/", len(cases))
