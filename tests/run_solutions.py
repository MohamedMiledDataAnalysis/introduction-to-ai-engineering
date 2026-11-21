"""Run every correction script under chapters/*/{python,r}/solutions/ against the mock model.
A script whose header says "Before you run it: start the mock with VAR=value ..." gets that mock;
one that needs the service of Chapter 18 gets it. Every script must end without an error.
Run from the root of the repository, with Ollama stopped (the mock takes its port):
    python tests/run_solutions.py [filter]"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env0 = dict(os.environ, LANG="C.UTF-8", PYTHONIOENCODING="utf-8")


def start(cmd, env):
    p = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    return p


def needs(script):
    head = "\n".join(l for l in script.read_text(encoding="utf-8").splitlines()[:5] if l.startswith("#"))
    m = re.search(r"Before you run it: (.*)", head)
    return m.group(1) if m else ""


scripts = sorted(ROOT.glob("chapters/*/python/solutions/*.py")) + sorted(ROOT.glob("chapters/*/r/solutions/*.R"))
if len(sys.argv) > 1:
    scripts = [s for s in scripts if sys.argv[1] in str(s)]
failed = []
for s in scripts:
    rel = s.relative_to(ROOT)
    pre = needs(s)
    mock_env = dict(env0)
    for var, val in re.findall(r"\b(MOCK_\w+)=(\S+)", pre):
        mock_env[var] = val
    procs = [start([sys.executable, "tools/mock_ollama.py"], mock_env)]
    if "Python service" in pre:
        procs.append(start([sys.executable, "-m", "uvicorn", "services.python.app:app", "--port", "8000"], env0))
        time.sleep(3)
    if "R service" in pre:
        procs.append(start(["Rscript", "-e", "plumber::pr_run(plumber::pr('services/r/plumber.R'), port = 8001)"], env0))
        time.sleep(5)
    cmd = [sys.executable, str(rel)] if s.suffix == ".py" else ["Rscript", str(rel)]
    t = time.time()
    try:
        r = subprocess.run(cmd, cwd=ROOT, env=env0, capture_output=True, text=True, timeout=600)
        ok, err = r.returncode == 0, (r.stderr.strip().splitlines() or [""])[-1]
    except subprocess.TimeoutExpired:
        ok, err = False, "timeout"
    for p in procs:
        p.terminate(); p.wait()
    print(f"{'ok  ' if ok else 'FAIL'} {time.time() - t:5.1f} s  {rel}" + ("" if ok else f"   {err[:150]}"), flush=True)
    if not ok:
        failed.append(str(rel))
print(f"\n{len(scripts) - len(failed)}/{len(scripts)} correction scripts ran without error")
sys.exit(1 if failed else 0)
