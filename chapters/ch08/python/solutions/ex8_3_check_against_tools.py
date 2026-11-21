# Exercise 8.3 - Check an answer against the tool results
# Run from the root of the repository:  python chapters/ch08/python/solutions/ex8_3_check_against_tools.py
# Before you run it: start the mock with MOCK_SCRIPT=tools/scripts/ch08_two_tools.json python tools/mock_ollama.py

import sys

sys.path.insert(0, ".")
from aie.toolloop import ask_with_tools

import json
from aie.factcheck import check_text

def facts_from_trace(trace):
    facts = {}
    def walk(obj, prefix):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{prefix}[{i}]")
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            unit = ("percent" if prefix.endswith("_pct") else
                    "money" if prefix.endswith("_gbp") else "number")
            facts[prefix] = (obj, unit)
    for name, _, result in trace:
        walk(json.loads(result), name)
    return facts

def check_answer_against_tools(answer, trace):
    return [(f.raw, hits) for f, hits in
            check_text(answer, facts_from_trace(trace))]

trace = []
answer = ask_with_tools(
    "What was the Class A note balance after the payment for the collection "
    "period ending 30 September 2026, and the arrears ratio of the pool at "
    "that date?", trace=trace)
print(len(facts_from_trace(trace)), "facts")
print(check_answer_against_tools(answer, trace))
print(check_answer_against_tools(answer.replace("0.8432%", "0.8342%"), trace))
