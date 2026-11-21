# Exercise 3.2 - Call a failing server through chat()
# Run from the root of the repository:  python chapters/ch03/python/solutions/ex3_2_retries.py
# Before you run it: start the mock with MOCK_FAIL_FIRST=2 python tools/mock_ollama.py

import sys; sys.path.insert(0, ".")
from aie.llm import chat
r = chat([{"role": "user",
           "content": "Reply with exactly these three words: Ollama is ready"}])
print(r["text"], r["seconds"])
