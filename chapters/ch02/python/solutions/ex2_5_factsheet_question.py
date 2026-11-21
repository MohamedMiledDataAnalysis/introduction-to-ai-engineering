# Exercise 2.5 - Ask a question about the factsheet
# Run from the root of the repository:  python chapters/ch02/python/solutions/ex2_5_factsheet_question.py

import sys

import pandas as pd
import requests

MODEL = "qwen3.5:4b"
OLLAMA_URL = "http://localhost:11434/api/chat"

print("Python version:", sys.version.split()[0])
print("pandas version:", pd.__version__)

tape = pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
print("Loan tape rows:", len(tape))

payload = {
    "model": MODEL,
    "messages": [{"role": "user",
                  "content": "Reply with exactly these three words: Ollama is ready"}],
    "stream": False,
    "think": False,     # answer directly; Chapter 3 explains
}
factsheet = open("data/am/documents/hgef_factsheet_2026_09.md",
                 encoding="utf-8").read()
payload["messages"] = [{"role": "user", "content": factsheet
    + "\n\nQuestion: What is the fund's one-year return?"}]
reply = requests.post(OLLAMA_URL, json=payload, timeout=300).json()
print(reply["message"]["content"])
print("Input tokens:", reply["prompt_eval_count"],
      "| output tokens:", reply["eval_count"])
