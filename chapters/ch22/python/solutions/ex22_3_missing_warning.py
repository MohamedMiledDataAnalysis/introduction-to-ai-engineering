# Exercise 22.3 - The past-performance warning as a check, broad and narrow
# Run from the root of the repository:  python chapters/ch22/python/solutions/ex22_3_missing_warning.py
import json
import re
import sys

sys.path.insert(0, ".")
from aie.agent import facts_from_results
from aie.factcheck import check_text, extract_figures
from aie.tools import fund_performance

WARNING = re.compile(r"past performance (does not|is not a reliable)", re.I)
RETURN_WORDS = re.compile(r"\b(return(ed)?|performance|gained|lost)\b", re.I)


def missing_warning(answer):
    """The book's check: a percentage, a performance word, and no warning."""
    has_figure = any(f.unit == "percent" for f in extract_figures(answer))
    return bool(has_figure and RETURN_WORDS.search(answer)
                and not WARNING.search(answer))


def missing_warning_narrow(answer, results):
    """The trade-off of the book: fire only if the answer quotes a return that a fund_performance call returned."""
    returns = {k: v for k, v in facts_from_results(results).items() if k.endswith("return_pct")}
    quotes_a_return = any(hits for _, hits in check_text(answer, returns))
    return bool(quotes_a_return and not WARNING.search(answer))


def apply_warning_check(result, domain="am"):
    """What Assistant.ask() does after the forbidden-phrase check (the book's integration)."""
    if domain == "am" and missing_warning(result["answer"]):
        result["status"] = "needs_review"
        result["unsupported"].append("past performance warning missing")
    return result


# 1. The four sentences of the book
book = ["HGEF returned 6.46% over one year to 30 September 2026.",
        "HGEF returned 6.46% over one year to 30 September 2026. Past performance does not predict future returns.",
        "HECB's ongoing costs are 0.40%.",
        "Ongoing costs of 0.40% reduce the return each year."]
print("The four sentences of the book:")
for s in book:
    print(f"  {str(missing_warning(s)):<6} {s}")

# 2. A larger set of answers, each labelled with the right decision, and the trace the agent would have
perf = [("fund_performance", json.dumps(fund_performance("HGEF", 12))),
        ("fund_performance", json.dumps(fund_performance("HECB", 12)))]
labelled = [  # (answer, a warning is required?)
    ("HGEF returned 6.46% over one year, against 7.86% for its benchmark.", True),
    ("HGEF returned 6.46% over one year. Past performance is not a reliable indicator of future results.", False),
    ("HGEF trailed its benchmark by 1.40% over one year.", True),
    ("HECB's ongoing costs are 0.40%.", False),
    ("Ongoing costs of 0.40% reduce the return each year.", False),
    ("The fund's largest holding is 4.2% of the portfolio.", False),
    ("HGEF's performance fee is 0%; there is none.", False),
    ("Information technology is 16.08% of HGEF, against 17.34% for the benchmark.", False),
]
print("\nBroad and narrow check on labelled answers:")
broad_err = narrow_err = 0
for answer, required in labelled:
    b, n = missing_warning(answer), missing_warning_narrow(answer, perf)
    broad_err += b != required
    narrow_err += n != required
    print(f"  required {str(required):<5} broad {str(b):<5} narrow {str(n):<5} {answer[:70]}")
print(f"Wrong decisions: broad {broad_err} of {len(labelled)}, narrow {narrow_err} of {len(labelled)}")

# 3. The integration: an agent result before and after the check
r = apply_warning_check({"answer": book[0], "status": "verified", "unsupported": []})
print("\nAfter the check:", r["status"], r["unsupported"])
