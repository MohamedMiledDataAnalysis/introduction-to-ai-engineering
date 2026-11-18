"""
A month of service logs (October 2026) for Chapter 19, simulated: 18 working days of questions to /sf/ask
and /am/ask. Three events are built in: a model outage on 7 October (afternoon), a new prompt version on
19 October that raises the share of answers needing review, and growing input tokens on the AM side.
Run:  python scripts/make_request_log.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(2025)
ROOT = Path(__file__).resolve().parents[1]
days = pd.bdate_range("2026-10-01", "2026-10-26")
rows = []
for d in days:
    for domain in ("sf", "am"):
        n = int(rng.poisson(22 if domain == "sf" else 15))
        for _ in range(n):
            ts = d + pd.Timedelta(hours=float(rng.uniform(8, 18)))
            prompt = "a41c2e09f7" if d < pd.Timestamp("2026-10-19") else "c7d03b51e2"
            outage = d == pd.Timestamp("2026-10-07") and ts.hour >= 14
            base_tokens = 2600 if domain == "sf" else 1800 + 45 * (d - days[0]).days
            tokens = int(rng.normal(base_tokens, 300))
            if outage:
                status, seconds, tokens = "error", round(float(rng.uniform(3.0, 3.4)), 3), 0
            else:
                p_review = 0.05 if prompt == "a41c2e09f7" or domain == "am" else 0.19
                r = rng.random()
                status = "needs_review" if r < p_review else "stopped" if r < p_review + 0.01 else "verified"
                seconds = round(float(rng.lognormal(np.log(4.0), 0.35)) * tokens / 2600, 3)
            rows.append({"ts": ts.strftime("%Y-%m-%dT%H:%M:%S"), "domain": domain, "caller": f"{domain}-shiny",
                         "prompt": prompt, "model": "qwen3.5:4b", "status": status, "tokens": tokens, "seconds": seconds})
rows.sort(key=lambda r: r["ts"])
out = ROOT / "data/logs/requests_2026_10.jsonl"
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print(len(rows), "requests written to", out.relative_to(ROOT))
