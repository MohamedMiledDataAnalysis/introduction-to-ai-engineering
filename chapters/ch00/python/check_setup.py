# Chapter 0 - Check that Python, pandas and Ollama work together
# Run from the root of the repository:  python chapters/ch00/python/check_setup.py
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
    "messages": [{"role": "user", "content": "Reply with exactly these three words: Ollama is ready"}],
    "stream": False,
}
try:
    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()
    print("Model reply:", response.json()["message"]["content"].strip())
except requests.exceptions.ConnectionError:
    print("Ollama is not running. Start the Ollama application, then run this script again.")
except requests.exceptions.HTTPError as err:
    print("Ollama answered with an error:", err)
    print(f"Check that you downloaded the model with: ollama pull {MODEL}")
