# Exercise 21.2 - Share of the arrears balance three months or more in arrears, and the new evaluation case
# Run from the root of the repository:  python chapters/ch21/python/solutions/ex21_2_arrears_share.py
import csv
import json
import sys

sys.path.insert(0, ".")
from aie.agent import Agent
from aie.tools import arrears_buckets, pool_summary

CUT = "2026-09-30"

# 1. The figures, from the tool the agent would call
result = arrears_buckets(CUT)
buckets = result["buckets"]
total = sum(x["balance_gbp"] for x in buckets)
three_plus = sum(x["balance_gbp"] for x in buckets if x["bucket"] in ("3 months", "4-5 months"))
share = round(100 * three_plus / total, 2)
for x in buckets:
    print(f"{x['bucket']:<11}{x['loans']:>3} loans  £{x['balance_gbp']:>14,.2f}")
print(f"Three months or more: £{three_plus:,.2f} of £{total:,.2f} = {share:.2f}%")

# 2. Checks: the two tools agree, and the share sits where it must
assert round(total, 2) == pool_summary(CUT)["arrears_balance_gbp"], "buckets and pool_summary disagree"
share_3m_only = round(100 * buckets[2]["balance_gbp"] / total, 2)
assert share_3m_only < share < 100
print(f"Checks passed: buckets total = pool_summary arrears balance; {share_3m_only:.2f}% < {share:.2f}% < 100%")

# 3. Design A: the tool as it is. A model that divides writes a figure no tool returned
answer = f"At 30 September 2026, {share:.2f}% of the arrears balance was three months or more in arrears."
verifier = Agent("", [])
u = verifier._verify(answer, [("arrears_buckets", json.dumps(result))])
print("Design A, unsupported figures:", ", ".join(u) or "none")

# 4. Design B: the tool also returns the shares, computed by code
def arrears_buckets_with_shares(cutoff_date, cumulative=True):
    r = arrears_buckets(cutoff_date)
    tot = sum(x["balance_gbp"] for x in r["buckets"])
    for i, x in enumerate(r["buckets"]):
        x["share_of_arrears_pct"] = round(100 * x["balance_gbp"] / tot, 2)
        if cumulative:   # share of the arrears balance in this bucket or a longer one
            x["this_or_longer_share_of_arrears_pct"] = round(100 * sum(y["balance_gbp"] for y in r["buckets"][i:]) / tot, 2)
    return r

for cumulative in (False, True):
    r = arrears_buckets_with_shares(CUT, cumulative)
    label = "B2, with cumulative shares" if cumulative else "B1, shares per bucket only"
    u = verifier._verify(answer, [("arrears_buckets", json.dumps(r))])
    print(f"Design {label}, unsupported figures:", ", ".join(u) or "none")

# 5. The evaluation case, added to a copy of the evaluation set
rows = list(csv.DictReader(open("evals/sf_agent_eval.csv", encoding="utf-8")))
rows.append({"id": "A13",
             "question": "What share of the pool's arrears balance was three months or more in arrears at 30 September 2026?",
             "answer_type": "number", "expected": f"{share:.2f}", "tolerance": "0.005", "keywords": "",
             "expected_tool": "arrears_buckets"})
with open("evals/solutions/sf_agent_eval_ex21_2.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(f"evals/solutions/sf_agent_eval_ex21_2.csv: {len(rows)} cases, the last one A13 (expected {share:.2f})")
