# Chapter 8 - Ask a question; the model calls tools for the figures
import sys

sys.path.insert(0, ".")
from aie.toolloop import ask_with_tools

trace = []
answer = ask_with_tools(
    "What was the Class A note balance after the payment for the collection "
    "period ending 30 September 2026, and the arrears ratio of the pool at "
    "that date?", trace=trace)
for name, args, result in trace:
    print(f"tool  {name}({args})\n      -> {result[:110]}...")
print("\nanswer:", answer)
