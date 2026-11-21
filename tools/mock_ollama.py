"""
A stand-in for Ollama's HTTP API, for testing code without a real model.

It answers on http://localhost:11434 like Ollama, with deterministic replies:
- /api/chat  : replays the replies listed in a script file (MOCK_SCRIPT=path.json),
               one per request; when a JSON schema is sent as "format", a JSON
               value of that shape (nulls, first enum values, empty strings, zeros);
               or else a short canned reply.
- /api/embed : returns hashed bag-of-words vectors (64 dimensions), so texts that
               share words have similar vectors.
- MOCK_FAIL_FIRST=n makes the first n chat requests fail with HTTP 503.
- MOCK_PORT=n listens on another port (default 11434, Ollama's own port, so that
  your code reaches the mock without any change). MOCK_PORT=0 takes a free port
  and writes it to the file named by MOCK_PORT_FILE: the tests use this, so they
  run even while Ollama is running.

Run:  python tools/mock_ollama.py      (quit Ollama first: both cannot use port 11434)
It is a test double: it does not understand language. Chapter 3 explains its use.
"""
import hashlib
import json
import math
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

STATE = {"calls": 0, "failed": 0}
SCRIPT = json.load(open(os.environ["MOCK_SCRIPT"])) if os.environ.get("MOCK_SCRIPT") else None
FAIL_FIRST = int(os.environ.get("MOCK_FAIL_FIRST", "0"))


def embed(text, dims=64):
    v = [0.0] * dims
    for w in re.findall(r"[a-z]+", text.lower()):
        h = int(hashlib.md5(w.encode()).hexdigest(), 16)
        v[h % dims] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def sample(schema):
    """A value that matches a JSON schema: null where allowed, else the first enum value, "", 0, [] or {}."""
    types = schema.get("type", "object")
    types = types if isinstance(types, list) else [types]
    if "null" in types:
        return None
    if "enum" in schema:
        return schema["enum"][0]
    t = types[0]
    if t == "object":
        return {k: sample(v) for k, v in schema.get("properties", {}).items()}
    return {"string": "", "number": 0, "integer": 0, "boolean": False, "array": []}.get(t)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
        if self.path == "/api/embed":
            inputs = body["input"] if isinstance(body["input"], list) else [body["input"]]
            return self._send(200, {"model": body.get("model"), "embeddings": [embed(t) for t in inputs]})
        if self.path != "/api/chat":
            return self._send(404, {"error": "not found"})
        if STATE["failed"] < FAIL_FIRST:
            STATE["failed"] += 1
            return self._send(503, {"error": "server busy"})
        STATE["calls"] += 1
        prompt = " ".join(m.get("content", "") or "" for m in body.get("messages", []))
        if SCRIPT is not None:
            step = SCRIPT[min(STATE["calls"] - 1, len(SCRIPT) - 1)]
            message = {"role": "assistant", "content": step.get("content", "")}
            if "tool_calls" in step:
                message["tool_calls"] = [{"function": tc} for tc in step["tool_calls"]]
        elif body.get("format"):                  # structured output asked: a JSON value of the right shape
            fmt = body["format"]
            message = {"role": "assistant", "content": json.dumps(sample(fmt) if isinstance(fmt, dict) else {})}
        else:
            last = body["messages"][-1].get("content", "")
            m = re.search(r"exactly these (?:\w+ )?words: (.+)$", last)
            message = {"role": "assistant", "content": m.group(1) if m else "MOCK REPLY: " + last[:60]}
        self._send(200, {
            "model": body.get("model"), "created_at": "2026-11-17T12:00:00Z",
            "message": message, "done": True,
            "prompt_eval_count": len(prompt.split()), "eval_count": len(message["content"].split()),
            "total_duration": 1_000_000,
        })

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("MOCK_PORT", "11434"))
    try:
        server = HTTPServer(("127.0.0.1", port), Handler)
    except OSError:
        raise SystemExit(f"Port {port} is already in use, probably by Ollama. Quit Ollama first "
                         "(or set MOCK_PORT to another port and OLLAMA_URL to match).")
    port = server.server_address[1]
    if os.environ.get("MOCK_PORT_FILE"):
        with open(os.environ["MOCK_PORT_FILE"], "w") as f:
            f.write(str(port))
    print(f"Mock Ollama listening on http://localhost:{port} (Ctrl+C to stop)", flush=True)
    server.serve_forever()
