# Chapter 3 - Does the model give the same answer twice?
import sys
from collections import Counter

sys.path.insert(0, ".")
from aie.llm import chat

PROMPT = "In one short sentence, why do UK mortgage borrowers often redeem when their fixed rate ends?"

for temperature in (0.0, 1.0):
    answers = [chat([{"role": "user", "content": PROMPT}], temperature=temperature,
                    seed=None if temperature else 42)["text"].strip() for _ in range(5)]
    print(f"Temperature {temperature}: {len(Counter(answers))} distinct answers out of 5")
