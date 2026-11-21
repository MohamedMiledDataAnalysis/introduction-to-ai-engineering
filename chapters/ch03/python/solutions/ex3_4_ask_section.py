# Exercise 3.4 - Ask one section of the prospectus
# Run from the root of the repository:  python chapters/ch03/python/solutions/ex3_4_ask_section.py

import re, sys
sys.path.insert(0, ".")
from aie.llm import chat

PROSPECTUS = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
                  encoding="utf-8").read()
SECTIONS = {s.split("\n")[0]: s for s in re.split(r"\n## ", PROSPECTUS)[1:]}

def ask_section(section_title, question):
    if section_title not in SECTIONS:
        raise KeyError(f"no section titled {section_title!r}; "
                       f"choose from {list(SECTIONS)}")
    reply = chat(
        system="Answer only from the text provided. If the text does not "
               "contain the answer, say so.",
        messages=[{"role": "user", "content":
                   f"TEXT:\n{SECTIONS[section_title]}\n\nQUESTION: {question}"}])
    return reply["text"].strip()

print(ask_section("3. Reserve fund",
                  "What is the Reserve Fund Required Amount?"))
