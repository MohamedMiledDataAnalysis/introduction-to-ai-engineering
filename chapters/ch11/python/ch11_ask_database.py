# Chapter 11 - Ask a question in English; get SQL, a guarded result and a checked sentence
import sys

sys.path.insert(0, ".")
from aie.text_to_sql import ask_database, explain_result

q = "What is the weight of Information Technology in the Global Equity Fund?"
out = ask_database(q)
print("SQL:    ", out.get("sql"))
print("Result: ", out.get("result", out.get("error")))
if "result" in out and "error" not in out["result"]:
    sentence, unsupported = explain_result(q, out)
    print("Answer: ", sentence)
    print("Unsupported figures:", unsupported or "none")
