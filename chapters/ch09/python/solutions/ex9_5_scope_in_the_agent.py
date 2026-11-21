# Exercise 9.5 - Refuse fund questions in the agent
# Run from the root of the repository:  python chapters/ch09/python/solutions/ex9_5_scope_in_the_agent.py

import re
import sys

sys.path.insert(0, ".")
from aie.agent import Agent

AM_TERMS = re.compile(r"\b(harbourline|hgef|hecb|hbma)\b", re.I)


class ScopedAgent(Agent):
    """The Larkfield agent, which refuses Harbourline questions before any model call."""

    def run(self, question, history=None):
        if (not set(self.tool_names) & {"fund_performance", "top_holdings"}
                and AM_TERMS.search(question)):
            return self._end("This assistant covers Larkfield Mortgage Funding "
                             "2025-1 only.", [], 0, 0, "out_of_scope")
        return super().run(question, history)


agent = ScopedAgent("You answer questions on Larkfield Mortgage Funding 2025-1.",
                    ["pool_summary", "note_balance"])
r = agent.run("What was HGEF's return in September?")
print(r["status"], "|", r["answer"], "| steps:", r["steps"])
