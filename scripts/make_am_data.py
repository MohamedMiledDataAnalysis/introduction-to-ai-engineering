"""
Generate the asset management datasets for *Introduction to AI Engineering*.

All firms, funds, issuers and figures are fictional. Identifiers use the
country prefix ZZ, which no ISO 3166 country uses, so a fictional ISIN can
never collide with a real security; the check digit follows ISO 6166.
Document layouts follow real templates: the PRIIPs Key Information Document
(Delegated Regulation (EU) 2017/653), the SFDR periodic disclosure for
Article 8 products (Delegated Regulation (EU) 2022/1288, Annex IV) and a
standard monthly fund factsheet.

Run:  python scripts/make_am_data.py      (deterministic, seed 2025)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2025
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "am"
(OUT / "documents").mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(SEED)

MONTHS = pd.date_range("2023-10-31", "2026-09-30", freq="ME")   # 36 month-ends
LAST = MONTHS[-1]


def isin(nsin9: str, prefix: str = "ZZ") -> str:
    """Return a 12-character ISIN with a valid ISO 6166 check digit."""
    body = prefix + nsin9
    digits = "".join(str(int(ch, 36)) for ch in body)
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            d = d - 9 if d > 9 else d
        total += d
    return body + str((10 - total % 10) % 10)


# ---------------------------------------------------------------------------
# 1. Security master
# ---------------------------------------------------------------------------
SECTORS = ["Information Technology", "Financials", "Health Care", "Industrials",
           "Consumer Discretionary", "Communication Services", "Consumer Staples",
           "Energy", "Materials", "Utilities", "Real Estate"]
SECTOR_W = np.array([0.24, 0.15, 0.11, 0.11, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03, 0.03])
COUNTRIES = ["US", "JP", "GB", "FR", "DE", "CH", "NL", "CA", "AU", "SE"]
COUNTRY_P = [0.62, 0.07, 0.05, 0.04, 0.04, 0.04, 0.03, 0.05, 0.03, 0.03]
CCY = {"US": "USD", "JP": "JPY", "GB": "GBP", "FR": "EUR", "DE": "EUR", "CH": "CHF",
       "NL": "EUR", "CA": "CAD", "AU": "AUD", "SE": "SEK"}

stems = ["Arden", "Brightwater", "Calder", "Dunmore", "Elsworth", "Fenwick", "Glenhaven",
         "Holloway", "Ivybridge", "Juniper", "Kestrel", "Linton", "Marlowe", "Northfield",
         "Oakridge", "Pembury", "Quayside", "Redfern", "Stanmore", "Thornbury", "Upland",
         "Vantor", "Westcombe", "Yarrow", "Zephyr", "Ashgrove", "Blackmoor", "Corbett",
         "Driftwood", "Eastleigh"]
suffix = {"Information Technology": ["Systems", "Semiconductors", "Software"],
          "Financials": ["Bank", "Insurance", "Capital"], "Health Care": ["Pharma", "Medical", "Biosciences"],
          "Industrials": ["Engineering", "Logistics", "Aerospace"], "Consumer Discretionary": ["Retail", "Motors", "Leisure"],
          "Communication Services": ["Media", "Telecom", "Networks"], "Consumer Staples": ["Foods", "Brands", "Beverages"],
          "Energy": ["Energy", "Petroleum", "Offshore"], "Materials": ["Chemicals", "Mining", "Materials"],
          "Utilities": ["Power", "Water", "Utilities"], "Real Estate": ["Properties", "REIT", "Estates"]}

N_EQ = 90
eq_sector = rng.choice(SECTORS, N_EQ, p=SECTOR_W)
used = set()
eq_names = []
for s in eq_sector:
    while True:
        nm = f"{rng.choice(stems)} {rng.choice(suffix[s])}"
        if nm not in used:
            used.add(nm)
            break
    eq_names.append(nm)
eq_country = rng.choice(COUNTRIES, N_EQ, p=COUNTRY_P)
eq_mcap = np.round(rng.lognormal(np.log(60), 1.0, N_EQ), 1)  # EUR bn
eq = pd.DataFrame({
    "isin": [isin(f"E{i:08d}") for i in range(1, N_EQ + 1)],
    "name": eq_names, "asset_class": "Equity", "sector": eq_sector,
    "country": eq_country, "currency": [CCY[c] for c in eq_country],
    "market_cap_eur_bn": eq_mcap,
})

N_BD = 80
bd_issuer = rng.choice(eq.loc[eq.country.isin(["FR", "DE", "NL", "GB", "US", "CH", "SE"]), "name"].tolist()
                       + [f"{s} Holdings" for s in stems[:12]], N_BD)
rating = rng.choice(["AA", "A+", "A", "A-", "BBB+", "BBB", "BBB-"], N_BD, p=[0.05, 0.10, 0.15, 0.18, 0.20, 0.18, 0.14])
r_rank = {"AA": 0, "A+": 1, "A": 2, "A-": 3, "BBB+": 4, "BBB": 5, "BBB-": 6}
mat_years = rng.uniform(1.5, 12, N_BD)
maturity = [(LAST + pd.DateOffset(days=int(y * 365.25))).date() for y in mat_years]
coupon = np.round(np.clip(2.0 + 0.25 * np.array([r_rank[r] for r in rating]) + rng.normal(0, 0.6, N_BD), 0.5, 6.0) * 8) / 8
spread_bp = np.round(55 + 18 * np.array([r_rank[r] for r in rating]) + 4 * mat_years + rng.normal(0, 12, N_BD))
duration = np.round(mat_years * 0.88, 2)
bd_sector = [eq.loc[eq.name == i, "sector"].iloc[0] if (eq.name == i).any() else "Financials" for i in bd_issuer]
bd = pd.DataFrame({
    "isin": [isin(f"B{i:08d}") for i in range(1, N_BD + 1)],
    "name": [f"{iss} {c:.3f}% {m:%m/%Y}".replace(".000%", "%") for iss, c, m in zip(bd_issuer, coupon, pd.to_datetime(maturity))],
    "issuer": bd_issuer, "asset_class": "Fixed Income", "sector": bd_sector,
    "currency": "EUR", "coupon_pct": coupon, "maturity": maturity, "rating": rating,
    "modified_duration": duration, "spread_bp": spread_bp,
    "amount_outstanding_eur_m": rng.choice([500, 600, 750, 800, 1000, 1250], N_BD),
})

esg = pd.DataFrame({
    "issuer": pd.concat([eq.name, bd.issuer]).unique(),
})
esg["esg_score"] = np.round(np.clip(rng.normal(62, 14, len(esg)), 15, 95), 1)       # 0-100, higher is better
esg["carbon_intensity_tco2e_per_eur_m"] = np.round(rng.lognormal(np.log(90), 1.1, len(esg)), 1)
esg["controversy_flag"] = rng.random(len(esg)) < 0.06
esg["excluded_activity"] = np.where(rng.random(len(esg)) < 0.03, "Thermal coal > 10% revenue", "")

# ---------------------------------------------------------------------------
# 2. Monthly security returns (factor model) - EUR terms
# ---------------------------------------------------------------------------
T = len(MONTHS)
mkt = rng.normal(0.008, 0.038, T)
sec_f = {s: rng.normal(0, 0.018, T) for s in SECTORS}
beta = rng.uniform(0.7, 1.35, N_EQ)
eq_ret = np.array([beta[i] * mkt + sec_f[eq_sector[i]] + rng.normal(0, 0.045, T) for i in range(N_EQ)]).T
d_yield = rng.normal(-0.0002, 0.0018, T)      # monthly change in Bund yield (decimal)
d_spread = rng.normal(0, 0.0007, T)
bd_ret = np.array([coupon[i] / 1200 - duration[i] * d_yield - duration[i] * d_spread * (1 + r_rank[rating[i]] / 6)
                   + rng.normal(0, 0.002, T) for i in range(N_BD)]).T
returns = pd.concat([
    pd.DataFrame(eq_ret, index=MONTHS, columns=eq["isin"]),
    pd.DataFrame(bd_ret, index=MONTHS, columns=bd["isin"]),
], axis=1).round(6)
returns.index.name = "month_end"
returns.reset_index().melt(id_vars="month_end", var_name="isin", value_name="total_return_eur") \
    .to_csv(OUT / "security_returns_monthly.csv", index=False)

# ---------------------------------------------------------------------------
# 3. Funds, benchmarks, holdings
# ---------------------------------------------------------------------------
FUNDS = {
    "HGEF": dict(name="Harbourline Global Equity Fund", share_class="I EUR Acc", isin=isin("F00000001"),
                 sfdr="Article 8", ocf=0.0075, benchmark="Harbourline Global Equity Reference Index",
                 launch="2019-03-29", aum_eur_m=1450.0, sri=4, rhp_years=5),
    "HECB": dict(name="Harbourline Euro Corporate Bond Fund", share_class="I EUR Acc", isin=isin("F00000002"),
                 sfdr="Article 8", ocf=0.0040, benchmark="Harbourline Euro Corporate Reference Index",
                 launch="2017-09-29", aum_eur_m=980.0, sri=2, rhp_years=3),
    "HBMA": dict(name="Harbourline Balanced Multi-Asset Fund", share_class="I EUR Acc", isin=isin("F00000003"),
                 sfdr="Article 6", ocf=0.0060, benchmark="55% HGERI / 40% HECRI / 5% EUR cash",
                 launch="2020-06-30", aum_eur_m=620.0, sri=3, rhp_years=4),
}
pd.DataFrame([dict(fund_code=k, **{kk: vv for kk, vv in v.items()}) for k, v in FUNDS.items()]) \
    .to_csv(OUT / "funds.csv", index=False)

eq_bm_w = eq.market_cap_eur_bn / eq.market_cap_eur_bn.sum()
bd_bm_w = bd.amount_outstanding_eur_m / bd.amount_outstanding_eur_m.sum()
bm_eq = (returns[eq["isin"]].values * eq_bm_w.values).sum(axis=1)
bm_bd = (returns[bd["isin"]].values * bd_bm_w.values).sum(axis=1)
cash = np.full(T, 0.0025)  # 3% p.a. approx monthly
bm = pd.DataFrame({"month_end": MONTHS, "HGEF": bm_eq, "HECB": bm_bd,
                   "HBMA": 0.55 * bm_eq + 0.40 * bm_bd + 0.05 * cash}).round({"HGEF": 6, "HECB": 6, "HBMA": 6})
bm.to_csv(OUT / "benchmark_returns_monthly.csv", index=False)

# Portfolio construction: active tilts towards high ESG scores and lower carbon
esg_map = esg.set_index("issuer")
eq_quality = eq.name.map(esg_map.esg_score).values
eq_excl = eq.name.map(esg_map.excluded_activity).values != ""
bd_excl = bd.issuer.map(esg_map.excluded_activity).values != ""


def pick_weights(n_pick, base_w, score, excluded, conc=1.0):
    idx = np.where(~excluded)[0]
    pref = base_w[idx] ** 0.6 * (score[idx] / 60) ** 2 * rng.uniform(0.6, 1.4, len(idx))
    chosen = idx[np.argsort(-pref)[:n_pick]]
    w = pref[np.argsort(-pref)[:n_pick]] ** conc
    return chosen, w / w.sum()


hold_rows = []
fund_ret = {}
# HGEF: 50 equities + 1.5% cash
c_eq, w_eq = pick_weights(50, eq_bm_w.values, eq_quality, eq_excl)
# HECB: 45 bonds + 2% cash
bd_score = bd.issuer.map(esg_map.esg_score).values
c_bd, w_bd = pick_weights(45, bd_bm_w.values, bd_score, bd_excl)
# HBMA: 25 equities, 20 bonds, 5% cash
c_eq2, w_eq2 = pick_weights(25, eq_bm_w.values, eq_quality, eq_excl, conc=0.8)
c_bd2, w_bd2 = pick_weights(20, bd_bm_w.values, bd_score, bd_excl, conc=0.8)

target = {
    "HGEF": [(eq["isin"].values[c_eq], w_eq * 0.985)],
    "HECB": [(bd["isin"].values[c_bd], w_bd * 0.98)],
    "HBMA": [(eq["isin"].values[c_eq2], w_eq2 * 0.55), (bd["isin"].values[c_bd2], w_bd2 * 0.40)],
}
cash_w = {"HGEF": 0.015, "HECB": 0.02, "HBMA": 0.05}

for code, parts in target.items():
    isins = np.concatenate([p[0] for p in parts])
    tw = np.concatenate([p[1] for p in parts])
    w = tw.copy()
    cw = cash_w[code]
    nav = 100.0
    navs = []
    for t, m in enumerate(MONTHS):
        r = returns.loc[m, isins].values
        gross = (w * r).sum() + cw * cash[t]
        net = gross - FUNDS[code]["ocf"] / 12
        nav = nav * (1 + net)
        navs.append((m.date(), round(nav, 4), round(net, 6)))
        # drift weights
        grown = w * (1 + r)
        cgrown = cw * (1 + cash[t])
        tot = grown.sum() + cgrown
        w, cw = grown / tot, cgrown / tot
        if m.month in (3, 6, 9, 12):        # quarterly rebalance to target at month-end
            w, cw = tw.copy(), cash_w[code]
        for j, s in enumerate(isins):
            hold_rows.append(dict(month_end=m.date(), fund_code=code, isin=s,
                                  weight=round(w[j], 6)))
        hold_rows.append(dict(month_end=m.date(), fund_code=code, isin="CASH-EUR", weight=round(cw, 6)))
    fund_ret[code] = pd.DataFrame(navs, columns=["month_end", "nav_per_share", "net_return"])

nav_df = pd.concat([d.assign(fund_code=k) for k, d in fund_ret.items()])[["month_end", "fund_code", "nav_per_share", "net_return"]]
nav_df.to_csv(OUT / "fund_nav_monthly.csv", index=False)

holdings = pd.DataFrame(hold_rows)
master = pd.concat([eq, bd], ignore_index=True)
holdings = holdings.merge(master[["isin", "name", "asset_class", "sector", "currency"]], on="isin", how="left")
holdings.loc[holdings["isin"] == "CASH-EUR", ["name", "asset_class", "sector", "currency"]] = ["Cash and equivalents", "Cash", "Cash", "EUR"]
aum_final = {k: v["aum_eur_m"] for k, v in FUNDS.items()}
holdings["market_value_eur"] = (holdings.weight * holdings.fund_code.map(aum_final) * 1e6).round(2)
holdings.to_csv(OUT / "fund_holdings_monthly.csv", index=False)

master.to_csv(OUT / "security_master.csv", index=False)
esg.to_csv(OUT / "issuer_esg.csv", index=False)

# ---------------------------------------------------------------------------
# 4. Transactions in the last month (HGEF and HECB)
# ---------------------------------------------------------------------------
tx = []
trade_days = pd.bdate_range("2026-09-01", "2026-09-30")
for code, pool in [("HGEF", eq["isin"].values[c_eq]), ("HECB", bd["isin"].values[c_bd])]:
    for k in range(28 if code == "HGEF" else 18):
        s = rng.choice(pool)
        side = rng.choice(["BUY", "SELL"])
        notional = round(float(rng.uniform(0.5, 9.0)) * 1e6, 2)
        tx.append(dict(trade_id=f"TRD-{code}-{k + 1:04d}", trade_date=trade_days[rng.integers(len(trade_days))].date(),
                       fund_code=code, isin=s, side=side, notional_eur=notional,
                       broker=rng.choice(["Ellery Securities", "Mayfair Markets", "Rhine Brokerage"]),
                       commission_eur=round(notional * (0.0004 if code == "HGEF" else 0.0), 2)))
pd.DataFrame(tx).sort_values(["trade_date", "trade_id"]).to_csv(OUT / "transactions_2026_09.csv", index=False)

# ---------------------------------------------------------------------------
# 5. Brinson attribution for HGEF, last month (reference answer for evaluations)
# ---------------------------------------------------------------------------
h_last = holdings[(holdings.fund_code == "HGEF") & (holdings.month_end == LAST.date())]
prev = MONTHS[-2]
h_prev = holdings[(holdings.fund_code == "HGEF") & (holdings.month_end == prev.date())]   # beginning-of-month weights
r_last = returns.loc[LAST]
pw = h_prev.set_index("isin").weight
attr = []
for s in SECTORS:
    p_isins = [i for i in pw.index if i != "CASH-EUR" and eq.set_index("isin").sector.get(i) == s]
    wp = pw[p_isins].sum() if p_isins else 0.0
    rp = (pw[p_isins] * r_last[p_isins]).sum() / wp if wp > 0 else 0.0
    b_isins = eq["isin"][eq.sector == s]
    wb = eq_bm_w[eq.sector == s].sum()
    rb = (eq_bm_w[eq.sector == s].values * r_last[b_isins].values).sum() / wb
    attr.append(dict(sector=s, portfolio_weight=wp, benchmark_weight=wb, portfolio_return=rp, benchmark_return=rb))
attr.append(dict(sector="Cash", portfolio_weight=pw["CASH-EUR"], benchmark_weight=0.0,
                 portfolio_return=cash[-1], benchmark_return=cash[-1]))
attr = pd.DataFrame(attr)
RB = bm.set_index("month_end").loc[LAST, "HGEF"]
attr["allocation"] = (attr.portfolio_weight - attr.benchmark_weight) * (attr.benchmark_return - RB)
attr["selection"] = attr.benchmark_weight * (attr.portfolio_return - attr.benchmark_return)
attr["interaction"] = (attr.portfolio_weight - attr.benchmark_weight) * (attr.portfolio_return - attr.benchmark_return)
attr.round(6).to_csv(OUT / "hgef_attribution_2026_09.csv", index=False)

# ---------------------------------------------------------------------------
# 6. Documents: factsheet, KIDs, SFDR periodic disclosure
# ---------------------------------------------------------------------------
def perf(code):
    d = fund_ret[code].set_index("month_end").net_return
    b = bm.set_index("month_end")[code]
    b.index = b.index.date
    out = {}
    for label, n in [("1 month", 1), ("3 months", 3), ("1 year", 12)]:
        out[label] = ((1 + d.iloc[-n:]).prod() - 1, (1 + b.iloc[-n:]).prod() - 1)
    ytd = [i for i in d.index if i.year == LAST.year]
    out["Year to date"] = ((1 + d[ytd]).prod() - 1, (1 + b[ytd]).prod() - 1)
    out["3 years p.a."] = ((1 + d).prod() ** (12 / len(d)) - 1, (1 + b).prod() ** (12 / len(b)) - 1)
    vol = d.std() * np.sqrt(12)
    te = (d.values - b.values).std(ddof=1) * np.sqrt(12)        # sample standard deviation, as for the volatility
    return out, vol, te


for code, f in FUNDS.items():
    out, vol, te = perf(code)
    hl = holdings[(holdings.fund_code == code) & (holdings.month_end == LAST.date())]
    top = hl[hl["isin"] != "CASH-EUR"].nlargest(10, "weight")
    sect = hl.groupby("sector").weight.sum().sort_values(ascending=False)
    lines = [f"# {f['name']} — Monthly factsheet, 30 September 2026", "",
             "> FICTIONAL DOCUMENT FOR TEACHING. Harbourline Asset Management does not exist.", "",
             "**For professional investors only.** A factsheet for retail investors must also show past "
             "performance over complete 12-month periods: for a UCITS, the last ten years or since launch.", "",
             "| Item | Detail |", "|---|---|",
             f"| Share class | {f['share_class']} |", f"| ISIN | {f['isin']} |",
             f"| Launch date | {f['launch']} |", f"| Fund size | EUR {f['aum_eur_m']:,.0f} m |",
             f"| Benchmark | {f['benchmark']} |", f"| SFDR classification | {f['sfdr']} |",
             f"| Ongoing charges | {f['ocf']:.2%} |", f"| Summary risk indicator | {f['sri']} on a scale of 1 to 7 |",
             f"| NAV per share | EUR {fund_ret[code].nav_per_share.iloc[-1]:,.4f} |", "",
             "## Performance (net of fees, EUR)", "", "| Period | Fund | Benchmark | Relative |", "|---|---:|---:|---:|"]
    for k, (a, b) in out.items():
        lines.append(f"| {k} | {a:.2%} | {b:.2%} | {a - b:+.2%} |")
    lines += ["", f"Annualised volatility (3 years): {vol:.2%}. Annualised tracking error (3 years): {te:.2%}.", "",
              "Past performance does not predict future returns.", "",
              "## Top 10 holdings", "", "| Holding | Sector | Weight |", "|---|---|---:|"]
    for _, r in top.iterrows():
        lines.append(f"| {r['name']} | {r.sector} | {r.weight:.2%} |")
    lines += ["", "## Sector allocation", "", "| Sector | Weight |", "|---|---:|"]
    for s, w in sect.items():
        lines.append(f"| {s} | {w:.2%} |")
    lines += ["", "## Manager commentary", "", "[COMMENTARY]", ""]
    (OUT / "documents" / f"{code.lower()}_factsheet_2026_09.md").write_text("\n".join(lines))

KID_SCEN = {  # per EUR 10,000 invested: (after 1 year, after RHP), return figures per year
    "HGEF": dict(stress=(3_120, 2_640), unfavourable=(8_190, 9_310), moderate=(10_640, 14_020), favourable=(13_870, 18_350),
                 entry=0.0, exit=0.0, ongoing=0.0075, transaction=0.0011, min_inv="EUR 1,000,000"),
    "HECB": dict(stress=(7_640, 7_980), unfavourable=(8_920, 9_410), moderate=(10_210, 10_690), favourable=(10_980, 11_620),
                 entry=0.0, exit=0.0, ongoing=0.0040, transaction=0.0006, min_inv="EUR 1,000,000"),
    "HBMA": dict(stress=(5_210, 5_030), unfavourable=(8_650, 9_520), moderate=(10_430, 11_840), favourable=(12_160, 14_210),
                 entry=0.0, exit=0.0, ongoing=0.0060, transaction=0.0009, min_inv="EUR 500,000"),
}
OBJ = {
    "HGEF": "to grow the value of your investment over at least five years by investing in shares of companies worldwide. The fund invests at least 95% of its assets in shares. It promotes environmental and social characteristics by excluding companies that derive more than 10% of their revenue from thermal coal and by keeping a weighted average carbon intensity below that of its benchmark.",
    "HECB": "to provide income and growth over at least three years by investing in investment-grade corporate bonds denominated in euro. The fund invests at least 90% of its assets in bonds rated BBB- or above. It promotes environmental and social characteristics by excluding issuers that derive more than 10% of their revenue from thermal coal and by keeping a weighted average ESG score above that of its benchmark.",
    "HBMA": "to grow the value of your investment over at least four years by investing in a mix of shares and euro investment-grade bonds. The fund holds between 45% and 65% in shares, between 30% and 50% in bonds and up to 10% in cash.",
}
for code, f in FUNDS.items():
    k = KID_SCEN[code]
    rhp = f["rhp_years"]
    perf_years = 2025 - int(f["launch"][:4])       # complete calendar years of performance, up to 2025 (PRIIPs Annex VIII)
    ann = lambda end: (end / 10_000) ** (1 / rhp) - 1
    tot_cost_1y = 10_000 * (k["ongoing"] + k["transaction"])
    text = f"""# Key Information Document — {f['name']}, {f['share_class']}

> FICTIONAL DOCUMENT FOR TEACHING. Harbourline Asset Management S.A. does not exist.

## Purpose
This document provides you with key information about this investment product. It is not marketing material. The information is required by law to help you understand the nature, risks, costs, potential gains and losses of this product and to help you compare it with other products.

## Product
**Product:** {f['name']}, {f['share_class']} (ISIN {f['isin']}), a sub-fund of Harbourline Funds SICAV.
**Manufacturer:** Harbourline Asset Management S.A., Luxembourg.
**Date of production:** 30 September 2026.

## What is this product?
**Type:** Shares of a sub-fund of a Luxembourg SICAV qualifying as a UCITS.
**Objectives:** The objective of the fund is {OBJ[code]} The fund is actively managed with reference to the {f['benchmark']}.
**Intended retail investor:** Investors with at least basic knowledge of funds, who can bear losses, and who plan to stay invested for at least {rhp} years. Minimum initial investment: {k['min_inv']}.

## What are the risks and what could I get in return?
**Risk indicator:** {f['sri']} on a scale of 1 (lower risk) to 7 (higher risk). The summary risk indicator assumes you keep the product for {rhp} years.

**Performance scenarios** (investment of EUR 10,000; recommended holding period {rhp} years)

| Scenario | | If you exit after 1 year | If you exit after {rhp} years |
|---|---|---:|---:|
| Minimum | There is no minimum guaranteed return. You could lose some or all of your investment. | | |
| Stress | What you might get back after costs | EUR {k['stress'][0]:,} | EUR {k['stress'][1]:,} |
| | Average return each year | {k['stress'][0] / 10_000 - 1:.1%} | {ann(k['stress'][1]):.1%} |
| Unfavourable | What you might get back after costs | EUR {k['unfavourable'][0]:,} | EUR {k['unfavourable'][1]:,} |
| | Average return each year | {k['unfavourable'][0] / 10_000 - 1:.1%} | {ann(k['unfavourable'][1]):.1%} |
| Moderate | What you might get back after costs | EUR {k['moderate'][0]:,} | EUR {k['moderate'][1]:,} |
| | Average return each year | {k['moderate'][0] / 10_000 - 1:.1%} | {ann(k['moderate'][1]):.1%} |
| Favourable | What you might get back after costs | EUR {k['favourable'][0]:,} | EUR {k['favourable'][1]:,} |
| | Average return each year | {k['favourable'][0] / 10_000 - 1:.1%} | {ann(k['favourable'][1]):.1%} |

## What happens if Harbourline Asset Management S.A. is unable to pay out?
The assets of the fund are held separately by the depositary, Ellery Depositary Bank S.A. A default of the manufacturer does not cause a loss to the fund. There is no compensation or guarantee scheme.

## What are the costs?
**Costs over time** (investment of EUR 10,000)

| | If you exit after 1 year | If you exit after {rhp} years |
|---|---:|---:|
| Total costs | EUR {tot_cost_1y:,.0f} | EUR {sum(tot_cost_1y * (1 + ann(k['moderate'][1])) ** t for t in range(rhp)):,.0f} |
| Annual cost impact | {k['ongoing'] + k['transaction']:.2%} | {k['ongoing'] + k['transaction']:.2%} each year |

**Composition of costs**

| One-off costs upon entry or exit | | |
|---|---|---:|
| Entry costs | We do not charge an entry fee. | EUR 0 |
| Exit costs | We do not charge an exit fee. | EUR 0 |
| **Ongoing costs taken each year** | | |
| Management fees and other administrative or operating costs | {k['ongoing']:.2%} of the value of your investment per year. | EUR {10_000 * k['ongoing']:,.0f} |
| Transaction costs | {k['transaction']:.2%} of the value of your investment per year, an estimate of the costs incurred when we buy and sell the underlying investments. | EUR {10_000 * k['transaction']:,.0f} |
| **Incidental costs** | | |
| Performance fees | There is no performance fee for this product. | EUR 0 |

## How long should I hold it and can I take money out early?
**Recommended holding period: {rhp} years.** You can redeem your shares on any Luxembourg business day without penalty.

## How can I complain?
Write to Harbourline Asset Management S.A., Complaints Officer, 12 rue de la Fonderie, L-1531 Luxembourg (fictional address), or email complaints@harbourline.example.

## Other relevant information
The prospectus, annual and semi-annual reports and past performance over the last {perf_years} years are available at www.harbourline.example.
"""
    (OUT / "documents" / f"{code.lower()}_kid.md").write_text(text)

# SFDR periodic disclosure (Article 8) - HGEF, financial year to 30 September 2026
h = holdings[(holdings.fund_code == "HGEF") & (holdings.month_end == LAST.date()) & (holdings["isin"] != "CASH-EUR")]
h = h.merge(eq[["isin", "name"]], on="isin", suffixes=("", "_m"))
w = h.weight / h.weight.sum()
waci_fund = (w * h.name.map(esg_map.carbon_intensity_tco2e_per_eur_m)).sum()
waci_bm = (eq_bm_w * eq.name.map(esg_map.carbon_intensity_tco2e_per_eur_m)).sum()
excl_count = int(eq_excl.sum())
ref = holdings[(holdings.fund_code == "HGEF") & (holdings.isin != "CASH-EUR")
               & (holdings.month_end > pd.Timestamp("2025-09-30").date())]
avg = ref.groupby("isin").weight.sum() / ref.month_end.nunique()        # average weight over the 12 month-ends
avg = avg.nlargest(15).rename("avg").reset_index().merge(eq[["isin", "name", "sector", "country"]], on="isin")
top15 = "\n".join(f"| {r['name']} | {r.sector} | {r.avg:.2%} | {r.country} |" for _, r in avg.iterrows())
sfdr = f"""# Periodic disclosure for the financial products referred to in Article 8 of Regulation (EU) 2019/2088

> FICTIONAL DOCUMENT FOR TEACHING. Layout follows Annex IV of Delegated Regulation (EU) 2022/1288.

**Product name:** {FUNDS['HGEF']['name']}
**Legal entity identifier:** fictional — not provided
**Reference period:** 1 October 2025 to 30 September 2026

## Did this financial product have a sustainable investment objective?
No. It promoted environmental and social characteristics and, while it did not have as its objective a sustainable investment, it did not commit to a minimum proportion of sustainable investments.

## To what extent were the environmental and/or social characteristics promoted by this financial product met?
The fund promoted two characteristics: (1) the exclusion of companies deriving more than 10% of their revenue from thermal coal, and (2) a weighted average carbon intensity (WACI) below that of its benchmark.

### How did the sustainability indicators perform?

| Sustainability indicator | Fund | Benchmark | Met? |
|---|---:|---:|---|
| Holdings in excluded thermal coal companies | 0 | {excl_count} companies in the benchmark | Yes |
| WACI (tCO2e per EUR million revenue) at 30 September 2026 | {waci_fund:,.1f} | {waci_bm:,.1f} | {"Yes" if waci_fund < waci_bm else "No"} |

### How did this financial product consider principal adverse impacts on sustainability factors?
The investment manager monitored greenhouse gas intensity of investee companies (indicator 3 of Table 1 of Annex I) and exposure to companies active in the fossil fuel sector (indicator 4) through the exclusion list and the WACI limit.

## What were the top investments of this financial product?
The list below includes the investments constituting the greatest proportion of investments of the financial product during the reference period (average of the twelve month-end weights).

| Largest investments | Sector | % Assets | Country |
|---|---|---:|---|
{top15}

## What was the proportion of sustainability-related investments?
Investments aligned with the environmental and social characteristics: {h.weight.sum():.1%}. Other investments (cash held for liquidity): {1 - h.weight.sum():.1%}.

## What actions have been taken to meet the environmental and/or social characteristics during the reference period?
The investment manager screened the investment universe against the exclusion list before each quarterly rebalancing and engaged with the five largest contributors to the fund's carbon intensity.
"""
(OUT / "documents" / "hgef_sfdr_periodic_2026.md").write_text(sfdr)

print("Securities:", len(master), "| holdings rows:", len(holdings), "| months:", T)
for code in FUNDS:
    print(code, "NAV", fund_ret[code].nav_per_share.iloc[-1], "1y",
          round((1 + fund_ret[code].net_return.iloc[-12:]).prod() - 1, 4))
gross = fund_ret["HGEF"].net_return.iloc[-1] + FUNDS["HGEF"]["ocf"] / 12
total_active = attr[["allocation", "selection", "interaction"]].sum().sum()
assert abs(total_active - (gross - RB)) < 5e-5, (total_active, gross - RB)
print("Attribution total active (gross of fees, HGEF, Sep 2026):", round(total_active, 6))
print("ISIN example:", master["isin"].iloc[0], "| WACI fund vs bm:", round(waci_fund, 1), round(waci_bm, 1))
