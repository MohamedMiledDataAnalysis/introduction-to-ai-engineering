"""Six fictional research notes on issuers held by Harbourline funds, with the key facts of each (Chapter 17)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/am/research"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(2025)
h = pd.read_csv(ROOT / "data/am/fund_holdings_monthly.csv")
eq = h[(h.month_end == "2026-09-30") & (h.fund_code == "HGEF")].nlargest(6, "weight")
facts = {}
for i, r in enumerate(eq.itertuples(), 1):
    rec = ["Buy", "Hold", "Sell"][int(rng.integers(0, 3))]
    growth = round(float(rng.uniform(-4, 14)), 1)
    margin = round(float(rng.uniform(8, 32)), 1)
    prev_margin = round(margin - float(rng.uniform(-2.5, 2.5)), 1)
    leverage = round(float(rng.uniform(0.3, 3.2)), 1)
    price = round(float(rng.uniform(20, 180)), 2)
    target = round(price * {"Buy": 1.25, "Hold": 1.03, "Sell": 0.82}[rec] * float(rng.uniform(0.95, 1.05)), 2)
    risk = rng.choice(["a slowdown in its main market", "rising input costs", "a pending regulatory review",
                       "customer concentration", "currency movements"])
    note = f"""# {r.name} — Third-quarter 2026 results

Harbourline Research (fictional, for teaching). Analyst: internal equity research. Date: 15 October 2026.

**Recommendation: {rec}. Target price: EUR {target:.2f} (current price EUR {price:.2f}).**

{r.name} reported third-quarter revenue growth of {growth:.1f}% year on year. The operating margin was {margin:.1f}%, {"up" if margin > prev_margin else "down"} from {prev_margin:.1f}% a year earlier. Net debt stands at {leverage:.1f} times EBITDA.

Management confirmed its full-year guidance. We see the main risk in {risk}. Our recommendation reflects valuation: the shares trade close to our estimate of fair value{" plus a discount" if rec == "Sell" else ""}.

The Harbourline Global Equity Fund holds {100 * r.weight:.2f}% in {r.name}.
"""
    nid = f"R{i:02d}"
    (OUT / f"{nid}.md").write_text(note, encoding="utf-8")
    facts[nid] = {"issuer": r.name, "recommendation": rec, "target_price_eur": target, "revenue_growth_pct": growth,
                  "operating_margin_pct": margin, "previous_margin_pct": prev_margin, "net_debt_to_ebitda": leverage,
                  "main_risk": str(risk), "fund_weight_pct": round(100 * r.weight, 2)}
json.dump(facts, open(OUT / "key_facts.json", "w"), indent=1)
print(json.dumps(facts["R01"], indent=1)); print(open(OUT / "R01.md").read())
