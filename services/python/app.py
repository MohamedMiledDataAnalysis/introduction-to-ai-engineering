"""
The AI engineering service: the two agents and their tools behind an HTTP API.
Run from the repository root:  uvicorn services.python.app:app --port 8000
"""
import os
import sys
import time
import uuid

sys.path.insert(0, ".")
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from aie.agent import Agent
from aie.logging_jsonl import log_event
from aie.tools import run_tool

API_KEY = os.environ.get("AIE_API_KEY", "dev-key-change-me")
SF_TOOLS = ["pool_summary", "note_balance", "waterfall_summary", "search_prospectus"]
AM_TOOLS = ["fund_performance", "top_holdings"]
SYSTEMS = {
    "sf": ("You are an assistant for Larkfield Mortgage Funding 2025-1. Use the tools for every figure and search the "
           "prospectus for rules. Cite passage identifiers such as [LMF#3]. Never compute or estimate a figure."),
    "am": ("You are an assistant for Harbourline funds. Use the tools for every figure. Never compute or estimate a "
           "figure, never forecast and never recommend an investment."),
}
AGENTS = {"sf": Agent(SYSTEMS["sf"], SF_TOOLS), "am": Agent(SYSTEMS["am"], AM_TOOLS)}

app = FastAPI(title="Introduction to AI Engineering service", version="1.0.0")


def check_key(x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid API key")


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    user: str = Field(default="anonymous", max_length=100)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/{domain}/ask", dependencies=[Depends(check_key)])
def ask(domain: str, q: Question):
    if domain not in AGENTS:
        raise HTTPException(status_code=404, detail="domain must be 'sf' or 'am'")
    request_id, start = str(uuid.uuid4()), time.perf_counter()
    try:
        result = AGENTS[domain].run(q.question)
    except Exception as err:                       # the model server is down, or another failure
        log_event(request_id=request_id, domain=domain, user=q.user, question=q.question, status="error",
                  error=str(err)[:300], seconds=round(time.perf_counter() - start, 3))
        raise HTTPException(status_code=503, detail="the assistant is unavailable; please try again later")
    log_event(request_id=request_id, domain=domain, user=q.user, question=q.question, status=result["status"],
              steps=result["steps"], tokens=result["tokens"], unsupported=result["unsupported"],
              tools=[t[0] for t in result["trace"]], answer=result["answer"],
              seconds=round(time.perf_counter() - start, 3))
    return {"request_id": request_id, "answer": result["answer"], "status": result["status"],
            "unsupported": result["unsupported"], "tools_used": [t[0] for t in result["trace"]]}


@app.get("/tools/{name}", dependencies=[Depends(check_key)])
def tool(name: str, cutoff_date: str = None, note_class: str = None, fund_code: str = None, months: int = None):
    args = {k: v for k, v in dict(cutoff_date=cutoff_date, note_class=note_class, fund_code=fund_code,
                                  months=months).items() if v is not None}
    import json
    out = json.loads(run_tool({"name": name, "arguments": args}, allowed=SF_TOOLS + AM_TOOLS))
    if "error" in out:
        raise HTTPException(status_code=400, detail=out["error"])
    return out
