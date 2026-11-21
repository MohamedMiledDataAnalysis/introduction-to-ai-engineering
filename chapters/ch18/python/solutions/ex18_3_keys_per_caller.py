# Exercise 18.3 - Test one key per caller
# Run from the root of the repository:  python chapters/ch18/python/solutions/ex18_3_keys_per_caller.py

import os
import sys

sys.path.insert(0, ".")
os.environ["AIE_API_KEYS"] = '{"sf-shiny": "k1", "am-shiny": "k2"}'   # before the service is imported
from fastapi.testclient import TestClient

from services.solutions.ex18_3.app import app

client = TestClient(app)
for key in ("k1", "k2", "k3"):
    r = client.get("/tools/pool_summary", params={"cutoff_date": "2026-09-30"},
                   headers={"x-api-key": key})
    print(key, r.status_code, r.json().get("detail", "accepted"))
