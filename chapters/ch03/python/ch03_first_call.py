# Chapter 3 - Ask a question about Larkfield, giving the model the relevant section
import re
import sys

sys.path.insert(0, ".")                 # so that Python finds the aie folder at the repository root
from aie.llm import chat

text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md", encoding="utf-8").read()
section = [s for s in re.split(r"\n## ", text) if s.startswith("2. The notes")][0]

reply = chat(
    system="You answer questions about a securitisation using only the text provided. "
           "If the text does not contain the answer, say so.",
    messages=[{"role": "user",
               "content": f"TEXT:\n{section}\n\nQUESTION: What is the margin on the Class B notes?"}],
)
print("Answer:       ", reply["text"].strip())
print("Model:        ", reply["provider"], reply["model"])
print("Input tokens: ", reply["input_tokens"])
print("Output tokens:", reply["output_tokens"])
print("Seconds:      ", reply["seconds"])
