# Exercise 4.4 - The cause phrases of the notes
# Run from the root of the repository:  python chapters/ch04/python/solutions/ex4_4_reason_phrases.py

import json

notes = [json.loads(line) for line in
         open("data/sf/rmbs/servicer_notes_2026_09.jsonl", encoding="utf-8")]

import re
from collections import Counter
print(Counter(re.search(r"(?:Reason|Cause given|Circumstances): ([^.]*)",
                        n["text"]).group(1) for n in notes))
