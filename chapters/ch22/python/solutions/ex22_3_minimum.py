# Exercise 22.3 - The warning check, in its minimum form (the full solution: ex22_3_missing_warning.py)
# Run from the root of the repository:  python chapters/ch22/python/solutions/ex22_3_minimum.py

import sys; sys.path.insert(0, ".")
import re
from aie.factcheck import extract_figures

WARNING = re.compile(r"past performance (does not|is not a reliable)", re.I)
RETURN_WORDS = re.compile(r"\b(return(ed)?|performance|gained|lost)\b", re.I)

def missing_warning(answer):
    has_figure = any(f.unit == "percent" for f in extract_figures(answer))
    return bool(has_figure and RETURN_WORDS.search(answer)
                and not WARNING.search(answer))
from aie.assistants import Assistant


class AssistantWithWarning(Assistant):
    """Assistant.ask(), then the past-performance warning check."""

    def ask(self, question, history=None):
        result = super().ask(question, history)
        if self.domain == "am" and missing_warning(result["answer"]):
            result["status"] = "needs_review"
            result["unsupported"].append("past performance warning missing")
        return result


for answer in ["HGEF returned 6.46% over one year to 30 September 2026.",
               "HGEF returned 6.46% over one year. Past performance does not predict future returns.",
               "HECB's ongoing charges are 0.40% a year."]:
    print(missing_warning(answer), "<-", answer)
