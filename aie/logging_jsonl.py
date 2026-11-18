"""Append one JSON line per request to a log file: the raw material of monitoring (Chapter 19)."""
import json
import time
from pathlib import Path

LOG = Path("logs/requests.jsonl")


def log_event(**fields):
    LOG.parent.mkdir(exist_ok=True)
    fields.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(fields, default=str) + "\n")
