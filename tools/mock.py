"""Start the mock model on a free port for a test, and point aie.llm at it.

    from tools.mock import start_mock
    with start_mock("tools/scripts/ch21_scenarios.json"):
        ...   # every chat() call in this block reaches the mock, even while Ollama runs

The mock is ready when the block starts (the port answers), and stopped when it ends.
"""
import contextlib
import os
import socket
import subprocess
import sys
import tempfile
import time

import aie.llm


@contextlib.contextmanager
def start_mock(script=None, fail_first=0):
    port_file = tempfile.mktemp(suffix=".port")
    env = {**os.environ, "MOCK_PORT": "0", "MOCK_PORT_FILE": port_file, "MOCK_FAIL_FIRST": str(fail_first)}
    if script:
        env["MOCK_SCRIPT"] = script
    proc = subprocess.Popen([sys.executable, "tools/mock_ollama.py"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    old_url = aie.llm.OLLAMA_URL
    try:
        deadline = time.monotonic() + 15
        port = None
        while time.monotonic() < deadline:          # wait until the mock has written its port and accepts calls
            if port is None and os.path.exists(port_file) and open(port_file).read().strip():
                port = int(open(port_file).read())
            if port is not None:
                with contextlib.suppress(OSError), socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    break
            time.sleep(0.05)
        else:
            raise RuntimeError("the mock did not start within 15 seconds")
        aie.llm.OLLAMA_URL = f"http://localhost:{port}"
        yield aie.llm.OLLAMA_URL
    finally:
        aie.llm.OLLAMA_URL = old_url
        proc.terminate()
        proc.wait()
        with contextlib.suppress(OSError):
            os.remove(port_file)
