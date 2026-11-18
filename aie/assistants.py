"""The two final-project agents: scope guards before the model, the agent loop, output guards after it."""
import re

from aie.agent import Agent
from aie.factcheck import forbidden_phrases
from aie.prompts import load_prompt

OUT_OF_SCOPE_SF = "This assistant covers Larkfield Mortgage Funding 2025-1 only."
OUT_OF_SCOPE_AM = "This assistant covers the three Harbourline funds only."
NO_ADVICE = {"sf": "This assistant cannot give investment advice or forecasts. "
                   "It can describe the transaction's documents, data and past performance.",
             "am": "This assistant cannot give investment advice or forecasts. "
                   "It can describe the funds' facts, costs and past performance."}

AM_WORDS = re.compile(r"\b(harbourline|hgef|hecb|hbma|factsheet|kid|sfdr|equity fund|bond fund)\b", re.I)
SF_WORDS = re.compile(r"\b(larkfield|lmf|class [abcd]\b|tape|waterfall|prospectus|reserve fund|arrears|cpr)\b", re.I)
ADVICE = re.compile(r"\b(should (i|we|my client)|recommend|worth (buying|investing)|best fund|good investment|forecast|"
                    r"predict|will (\w+ ){1,3}(rise|fall|go up|go down|recover|outperform|underperform|beat))\b", re.I)


class Assistant:
    def __init__(self, domain):
        self.domain = domain
        if domain == "sf":
            system, self.version = load_prompt("sf_agent_system_v1")
            tools = ["pool_summary", "note_balance", "waterfall_summary", "arrears_buckets", "search_prospectus"]
        else:
            system, self.version = load_prompt("am_agent_system_v1")
            tools = ["fund_performance", "top_holdings", "fund_characteristics", "search_fund_documents"]
        self.agent = Agent(system, tools, max_steps=6)

    def guard_question(self, question):
        if self.domain == "sf" and AM_WORDS.search(question) and not SF_WORDS.search(question):
            return OUT_OF_SCOPE_SF
        if self.domain == "am" and SF_WORDS.search(question) and not AM_WORDS.search(question):
            return OUT_OF_SCOPE_AM
        if ADVICE.search(question):
            return NO_ADVICE[self.domain]
        return None

    def ask(self, question, history=None):
        refusal = self.guard_question(question)
        if refusal:
            return {"answer": refusal, "status": "declined", "steps": 0, "tokens": 0, "trace": [],
                    "unsupported": [], "prompt": self.version}
        result = self.agent.run(question, history)
        flagged = forbidden_phrases(result["answer"])
        if flagged:
            result["status"] = "needs_review"
            result["unsupported"] = result["unsupported"] + [f"forbidden phrase: {p}" for p in flagged]
        result["prompt"] = self.version
        return result
