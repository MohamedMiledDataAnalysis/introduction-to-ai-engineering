# Exercise 4.5 - The extraction without the JSON schema
# Run from the root of the repository:  python chapters/ch04/python/solutions/ex4_5_without_schema.py

import json
import sys

sys.path.insert(0, ".")
from aie.llm import chat
from aie.prompts import load_prompt, render
from aie.validate import parse_json_reply, validate

template, version = load_prompt("extract_servicer_note_v1")
schema = json.load(open("prompts/servicer_note_schema.json"))
notes = [json.loads(line) for line in
         open("data/sf/rmbs/servicer_notes_2026_09.jsonl", encoding="utf-8")]

fields = ["loan_id", "months_in_arrears", "arrears_balance", "action",
          "promise_date"]
correct = {f: 0 for f in fields}
invalid = 0
for note in notes:
    reply = chat([{"role": "user",
                   "content": render(template, note_text=note["text"])}],
                 format=None)          # the schema is not sent
    try:
        obj = parse_json_reply(reply["text"])
    except ValueError:
        invalid += 1
        continue
    if validate(obj, schema):
        invalid += 1
        continue
    for f in fields:
        correct[f] += obj.get(f) == note["truth"][f]

print(f"Prompt version {version}; {len(notes)} notes; "
      f"{invalid} invalid replies")
for f in fields:
    print(f"  {f:<18} {correct[f]:>2}/{len(notes)} correct")
