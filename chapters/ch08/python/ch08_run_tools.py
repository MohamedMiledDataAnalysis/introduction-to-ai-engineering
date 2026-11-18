# Chapter 8 - Run tool calls of the kind a model emits, including bad ones
import sys

sys.path.insert(0, ".")
from aie.tools import run_tool, tool_specs

print("Tools offered to the model:",
      [t["function"]["name"] for t in tool_specs()])
calls = [
    {"name": "pool_summary", "arguments": {"cutoff_date": "2026-09-30"}},
    {"name": "note_balance",
     "arguments": {"note_class": "A", "cutoff_date": "2026-09-30"}},
    {"name": "fund_performance",
     "arguments": {"fund_code": "HGEF", "months": 12}},
    {"name": "note_balance",
     "arguments": {"note_class": "E", "cutoff_date": "2026-09-30"}},
    {"name": "pool_summary", "arguments": {"cutoff_date": "2026-10-31"}},
    {"name": "delete_loans", "arguments": {}},
]
for c in calls:
    print(f"\n{c['name']}({c['arguments']})\n  -> {run_tool(c)}")
