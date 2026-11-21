# Exercise 18.4 - Median and maximum response time
# Run from the root of the repository:  python chapters/ch18/python/solutions/ex18_4_response_times.py
# Before you run it: start the Python service (Chapter 18), with Ollama or the mock running

import statistics, time, requests
BASE, KEY = "http://localhost:8000", {"x-api-key": "dev-key-change-me"}
times = []
for _ in range(20):
    t = time.perf_counter()
    requests.post(f"{BASE}/sf/ask", json={"question":
        "What was the arrears ratio at 30 September 2026?"}, headers=KEY,
        timeout=600)
    times.append(time.perf_counter() - t)
print(f"median {statistics.median(times):.2f} s, max {max(times):.2f} s")
