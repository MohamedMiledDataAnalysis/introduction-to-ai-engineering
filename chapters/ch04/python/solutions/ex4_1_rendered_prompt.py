# Exercise 4.1 - The prompt as the model receives it
# Run from the root of the repository:  python chapters/ch04/python/solutions/ex4_1_rendered_prompt.py

import json, sys
sys.path.insert(0, ".")
from aie.prompts import load_prompt, render

template, version = load_prompt("extract_servicer_note_v1")
notes = [json.loads(l) for l in
         open("data/sf/rmbs/servicer_notes_2026_09.jsonl", encoding="utf-8")]
note = next(n for n in notes if n["note_id"] == "N002")
print(render(template, note_text=note["text"]))
