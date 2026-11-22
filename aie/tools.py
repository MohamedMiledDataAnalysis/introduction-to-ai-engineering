"""
Tools: Python functions a model may ask to run, described by JSON schemas.
Each tool computes from the book's data; the model never computes figures itself.
"""
import json
import re
from functools import lru_cache

import pandas as pd

from aie.validate import validate

DATES = None


@lru_cache(maxsize=None)
def _tape():
    return pd.read_csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")


@lru_cache(maxsize=None)
def _notes():
    return pd.read_csv("data/sf/rmbs/larkfield_2025_1_notes.csv")


@lru_cache(maxsize=None)
def _waterfall():
    return pd.read_csv("data/sf/rmbs/larkfield_2025_1_waterfall.csv")


@lru_cache(maxsize=None)
def _nav():
    return pd.read_csv("data/am/fund_nav_monthly.csv")


@lru_cache(maxsize=None)
def _bm():
    return pd.read_csv("data/am/benchmark_returns_monthly.csv")


@lru_cache(maxsize=None)
def _holdings():
    return pd.read_csv("data/am/fund_holdings_monthly.csv")


def _check_date(date, available):
    if date not in set(available):
        raise ValueError(f"no data for {date}; available month-ends run from {min(available)} to {max(available)}")


# ---------------- structured finance ----------------
def pool_summary(cutoff_date):
    t = _tape()
    _check_date(cutoff_date, t["RREL6"])
    m = t[t["RREL6"] == cutoff_date]
    pool = m["RREL30"].sum()
    arrears = m.loc[m["RREL69"] == "ARRE", "RREL30"].sum()
    return {"cutoff_date": cutoff_date, "pool_balance_gbp": round(pool, 2),
            "loans_outstanding": int((m["RREL30"] > 0).sum()),
            "arrears_balance_gbp": round(arrears, 2), "arrears_ratio_pct": round(100 * arrears / pool, 4),
            "defaulted_loans_to_date": int((m["RREL69"] == "DFLT").sum())}


def note_balance(note_class, cutoff_date):
    n = _notes()
    _check_date(cutoff_date, n["cutoff"])
    row = n[(n["cutoff"] == cutoff_date) & (n["cls"] == note_class)]
    if row.empty:
        raise ValueError(f"unknown class {note_class}; classes are A, B, C, D")
    r = row.iloc[0]
    return {"class": note_class, "cutoff_date": cutoff_date, "opening_gbp": round(r.opening, 2),
            "principal_paid_gbp": round(r.principal_paid, 2), "interest_paid_gbp": round(r.interest_paid, 2),
            "closing_gbp": round(r.closing, 2), "coupon_pct": r.coupon_pct}


def waterfall_summary(cutoff_date):
    w = _waterfall()
    _check_date(cutoff_date, w["cutoff"])
    m = w[(w["cutoff"] == cutoff_date) & (w["waterfall"] == "Summary")]
    names = {"Available revenue receipts": "revenue_receipts_gbp",
             "Available principal receipts": "principal_receipts_gbp",
             "New defaults debited to PDL": "new_defaults_gbp",
             "Reserve fund closing balance": "reserve_fund_balance_gbp",
             "Excess spread released": "excess_spread_gbp"}
    return {"cutoff_date": cutoff_date, **{names[r["item"]]: round(r["paid"], 2) for _, r in m.iterrows()}}


# ---------------- asset management ----------------
def fund_performance(fund_code, months):
    nav, bm = _nav(), _bm()
    f = nav[nav["fund_code"] == fund_code]
    if f.empty:
        raise ValueError(f"unknown fund {fund_code}; funds are HGEF, HECB, HBMA")
    if months not in (1, 3, 12, 36):
        raise ValueError("months must be 1, 3, 12 or 36")
    fr = (1 + f["net_return"].iloc[-months:]).prod() - 1
    br = (1 + bm[fund_code].iloc[-months:]).prod() - 1
    return {"fund_code": fund_code, "period_months": months, "period_end": f["month_end"].iloc[-1],
            "fund_return_pct": round(100 * fr, 4), "benchmark_return_pct": round(100 * br, 4),
            "relative_return_pct": round(100 * (fr - br), 4)}


def top_holdings(fund_code, n=10):
    h = _holdings()
    last = h["month_end"].max()
    m = h[(h["fund_code"] == fund_code) & (h["month_end"] == last) & (h["isin"] != "CASH-EUR")]
    if m.empty:
        raise ValueError(f"unknown fund {fund_code}; funds are HGEF, HECB, HBMA")
    top = m.nlargest(int(n), "weight")
    return {"fund_code": fund_code, "as_of": last,
            "holdings": [{"name": r["name"], "sector": r["sector"], "weight_pct": round(100 * r["weight"], 2)}
                         for _, r in top.iterrows()]}


REGISTRY = {
    "pool_summary": (pool_summary, "Pool balance, loans outstanding, arrears balance and ratio of the Larkfield "
                     "2025-1 mortgage pool at a month-end cut-off date.",
                     {"type": "object", "properties": {
                         "cutoff_date": {"type": "string", "pattern": "20[0-9]{2}-[0-9]{2}-[0-9]{2}"}},
                      "required": ["cutoff_date"], "additionalProperties": False}),
    "note_balance": (note_balance, "Opening and closing balance, principal and interest paid, and coupon of one "
                     "class of Larkfield 2025-1 notes for one collection period, named by its end "
                     "date; the closing balance is after that period's payment, made on the 20th of "
                     "the next month.",
                     {"type": "object", "properties": {
                         "note_class": {"type": "string", "enum": ["A", "B", "C", "D"]},
                         "cutoff_date": {"type": "string", "pattern": "20[0-9]{2}-[0-9]{2}-[0-9]{2}"}},
                      "required": ["note_class", "cutoff_date"], "additionalProperties": False}),
    "waterfall_summary": (waterfall_summary, "Revenue and principal receipts, new defaults, reserve fund balance "
                          "and excess spread of Larkfield 2025-1 for one collection period, named by its end date; "
                          "they are paid out on the 20th of the next month.",
                          {"type": "object", "properties": {
                              "cutoff_date": {"type": "string", "pattern": "20[0-9]{2}-[0-9]{2}-[0-9]{2}"}},
                           "required": ["cutoff_date"], "additionalProperties": False}),
    "fund_performance": (fund_performance, "Net return of a Harbourline fund and of its benchmark over the last "
                         "1, 3, 12 or 36 months to the latest month-end.",
                         {"type": "object", "properties": {
                             "fund_code": {"type": "string", "enum": ["HGEF", "HECB", "HBMA"]},
                             "months": {"type": "integer", "enum": [1, 3, 12, 36]}},
                          "required": ["fund_code", "months"], "additionalProperties": False}),
    "top_holdings": (top_holdings, "The largest holdings of a Harbourline fund at the latest month-end.",
                     {"type": "object", "properties": {
                         "fund_code": {"type": "string", "enum": ["HGEF", "HECB", "HBMA"]},
                         "n": {"type": "integer", "minimum": 1}},
                      "required": ["fund_code"], "additionalProperties": False}),
}


def tool_specs(names=None):
    """The tool descriptions in the format Ollama (and OpenAI-compatible APIs) expect."""
    names = names or list(REGISTRY)
    return [{"type": "function", "function": {"name": n, "description": REGISTRY[n][1], "parameters": REGISTRY[n][2]}}
            for n in names]


def run_tool(call, allowed=None):
    """Execute one tool call {'name':..., 'arguments':{...}}. Errors are returned as text for the model to read."""
    name, args = call.get("name"), call.get("arguments") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return json.dumps({"error": "arguments are not valid JSON"})
    if name not in REGISTRY or (allowed is not None and name not in allowed):
        return json.dumps({"error": f"unknown tool {name}"})
    fn, _, schema = REGISTRY[name]
    problems = validate(args, schema)
    if problems:
        return json.dumps({"error": "invalid arguments: " + "; ".join(problems)})
    try:
        return json.dumps(fn(**args))
    except (ValueError, KeyError, TypeError) as err:
        return json.dumps({"error": str(err)})


# ---------------- documents ----------------
@lru_cache(maxsize=None)
def _prospectus_index():
    from aie.retrieval import BM25, chunk_markdown
    text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md", encoding="utf-8").read()
    return BM25(chunk_markdown(text, "LMF"))


def search_prospectus(query, k=3):
    return {"query": query, "passages": [{"id": c["id"], "text": c["text"]}
                                         for c, _ in _prospectus_index().search(query, int(k))]}


REGISTRY["search_prospectus"] = (
    search_prospectus,
    "Search the Larkfield 2025-1 prospectus excerpt and return the most relevant passages with their "
    "identifiers (for example LMF#3). Use it for definitions, rules, fees, triggers and the priority of "
    "payments. Cite the identifiers in your answer.",
    {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer", "minimum": 1}},
     "required": ["query"], "additionalProperties": False})


# ---------------- added for the final project ----------------
def arrears_buckets(cutoff_date):
    t = _tape()
    _check_date(cutoff_date, t["RREL6"])
    m = t[(t["RREL6"] == cutoff_date) & (t["RREL69"] == "ARRE")].copy()
    m["months"] = (m["RREL68"] // 30).clip(upper=4)
    labels = {1: "1 month", 2: "2 months", 3: "3 months", 4: "4-5 months"}
    return {"cutoff_date": cutoff_date,
            "buckets": [{"bucket": lab, "loans": int((m["months"] == k).sum()),
                         "balance_gbp": round(m.loc[m["months"] == k, "RREL30"].sum(), 2)}
                        for k, lab in labels.items()]}


REGISTRY["arrears_buckets"] = (
    arrears_buckets,
    "Number of loans and current balance of the Larkfield 2025-1 loans in "
    "arrears at a month-end, by months in arrears: 1, 2, 3, and 4 to 5. "
    "Defaulted loans (6 months or more) are not included.",
    {"type": "object",
     "properties": {"cutoff_date": {"type": "string",
                    "pattern": "20[0-9]{2}-[0-9]{2}-[0-9]{2}"}},
     "required": ["cutoff_date"], "additionalProperties": False})


@lru_cache(maxsize=None)
def _fund_docs_index():
    from aie.retrieval import chunk_markdown
    chunks = []
    for code in ("hgef", "hecb", "hbma"):
        for kind, path in (("KID", f"data/am/documents/{code}_kid.md"),
                           ("factsheet", f"data/am/documents/{code}_factsheet_2026_09.md")):
            for c in chunk_markdown(open(path, encoding="utf-8").read(), f"{code.upper()}-{kind}"):
                c["fund"] = code.upper()
                c["id"] = re.sub(r"[^A-Za-z0-9#.\-]", "", c["id"].split("#")[0]) + f"#{len(chunks) + 1}"
                chunks.append(c)
    sfdr = open("data/am/documents/hgef_sfdr_periodic_2026.md", encoding="utf-8").read()
    for c in chunk_markdown(sfdr, "HGEF-SFDR"):
        c["fund"] = "HGEF"
        c["id"] = f"HGEF-SFDR#{len(chunks) + 1}"
        chunks.append(c)
    # The table of key facts before the first section (ISIN, SFDR classification, ongoing charges...) and the
    # SFDR disclosure's title and reference period are not in any '## ' section: index them as one chunk each.
    heads = [(c.upper(), "factsheet", f"data/am/documents/{c}_factsheet_2026_09.md") for c in ("hgef", "hecb", "hbma")]
    heads.append(("HGEF", "SFDR", "data/am/documents/hgef_sfdr_periodic_2026.md"))
    for code, kind, path in heads:
        head = open(path, encoding="utf-8").read().split("\n## ")[0]
        lines = [l for l in head.split("\n") if l.strip() and not l.startswith(">")]
        text = "Key facts\n" + lines[0].lstrip("# ").strip() + "\n" + "\n".join(lines[1:])
        chunks.append({"id": f"{code}-{kind}#{len(chunks) + 1}", "title": "Key facts", "text": text, "fund": code})
    return chunks


def search_fund_documents(query, fund_code, k=3):
    from aie.retrieval import BM25
    chunks = [c for c in _fund_docs_index() if c["fund"] == fund_code]     # filter by fund first (Chapter 7)
    if not chunks:
        raise ValueError(f"unknown fund {fund_code}; funds are HGEF, HECB, HBMA")
    return {"fund_code": fund_code, "passages": [{"id": c["id"], "text": c["text"]}
                                                 for c, _ in BM25(chunks).search(query, int(k))]}


def fund_characteristics(fund_code):
    h = _holdings()
    last = h["month_end"].max()
    m = h[(h["fund_code"] == fund_code) & (h["month_end"] == last)]
    if m.empty:
        raise ValueError(f"unknown fund {fund_code}; funds are HGEF, HECB, HBMA")
    sec = pd.read_csv("data/am/security_master.csv").set_index("isin")
    esg = pd.read_csv("data/am/issuer_esg.csv").set_index("issuer")
    x = m[m["isin"] != "CASH-EUR"].join(sec[["issuer", "modified_duration", "rating"]], on="isin")
    x["issuer_key"] = x["issuer"].fillna(x["name"])
    x = x.join(esg[["esg_score", "carbon_intensity_tco2e_per_eur_m"]], on="issuer_key")
    w = x["weight"] / x["weight"].sum()
    out = {"fund_code": fund_code, "as_of": last, "holdings": int(len(x)),
           "cash_weight_pct": round(100 * m.loc[m["isin"] == "CASH-EUR", "weight"].sum(), 2),
           "weighted_esg_score": round(float((w * x["esg_score"]).sum()), 1),
           "weighted_carbon_intensity": round(float((w * x["carbon_intensity_tco2e_per_eur_m"]).sum()), 1),
           "top_sectors": [{"sector": s, "weight_pct": round(100 * v, 2)}
                           for s, v in m.groupby("sector")["weight"].sum().nlargest(3).items()]}
    bonds = x[x["modified_duration"].notna()]
    if not bonds.empty:
        bw = bonds["weight"] / bonds["weight"].sum()
        out["bond_modified_duration_years"] = round(float((bw * bonds["modified_duration"]).sum()), 2)
        out["bbb_share_of_bonds_pct"] = round(100 * float(bw[bonds["rating"].str.startswith("BBB")].sum()), 2)
    return out


REGISTRY["search_fund_documents"] = (
    search_fund_documents,
    "Search the Key Information Document, the September 2026 factsheet and, for HGEF, the SFDR periodic disclosure "
    "of ONE Harbourline fund. Returns passages with identifiers to cite. Use for costs, risk indicator, objectives, "
    "sustainability characteristics and other document facts.",
    {"type": "object", "properties": {"query": {"type": "string"},
                                      "fund_code": {"type": "string", "enum": ["HGEF", "HECB", "HBMA"]},
                                      "k": {"type": "integer", "minimum": 1}},
     "required": ["query", "fund_code"], "additionalProperties": False})
REGISTRY["fund_characteristics"] = (
    fund_characteristics,
    "Portfolio characteristics of a Harbourline fund at the latest month-end: number of holdings, cash weight, "
    "weighted ESG score and carbon intensity, top three sectors, and for bond holdings the weighted modified "
    "duration and the share rated in the BBB band (BBB+ to BBB-).",
    {"type": "object", "properties": {"fund_code": {"type": "string", "enum": ["HGEF", "HECB", "HBMA"]}},
     "required": ["fund_code"], "additionalProperties": False})
