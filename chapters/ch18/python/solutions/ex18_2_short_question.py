# Exercise 18.2 - A question that is too short
# Run from the root of the repository:  python chapters/ch18/python/solutions/ex18_2_short_question.py

import sys

sys.path.insert(0, ".")
from fastapi.testclient import TestClient   # calls the service without starting a server

from services.python.app import app

client = TestClient(app)
r = client.post("/sf/ask", json={"question": "Hi"}, headers={"x-api-key": "dev-key-change-me"})
print(r.status_code, r.json())
