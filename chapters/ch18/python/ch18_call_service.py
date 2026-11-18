# Chapter 18 - Call the running service like any other application would
import requests

BASE, KEY = "http://localhost:8000", {"x-api-key": "dev-key-change-me"}
print(requests.get(f"{BASE}/health").json())
print(requests.get(f"{BASE}/tools/pool_summary", params={"cutoff_date": "2026-09-30"}, headers=KEY).json())
r = requests.get(f"{BASE}/tools/pool_summary", params={"cutoff_date": "2026-10-31"}, headers=KEY)
print(r.status_code, r.json())
r = requests.post(f"{BASE}/sf/ask", json={"question": "What was the arrears ratio at 30 September 2026?"},
                  headers={"x-api-key": "wrong"})
print(r.status_code, r.json())
r = requests.post(f"{BASE}/sf/ask", json={"question": "What was the arrears ratio at 30 September 2026?"},
                  headers=KEY, timeout=600)
print(r.status_code, r.json())
