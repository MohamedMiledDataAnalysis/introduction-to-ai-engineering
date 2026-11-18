"""
Generate the structured finance datasets for *Introduction to AI Engineering*.

All entities, loans and figures are fictional. The layouts follow real templates:
- UK RMBS loan-level tape: field codes and names from Annex II (RREL / RREC) of
  Delegated Regulation (EU) 2020/1224, the residential real estate template that
  the UK onshored (FCA SECN 11 Annex 2R / PRA Securitisation Part).
- US auto ABS tape: asset-level field tags from SEC Regulation AB II, Schedule AL
  (Item 1125), auto loan schema.

Run:  python scripts/make_sf_data.py      (deterministic, seed 2025)
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2025
ROOT = Path(__file__).resolve().parents[1]
OUT_RMBS = ROOT / "data" / "sf" / "rmbs"
OUT_AUTO = ROOT / "data" / "sf" / "auto"
OUT_RMBS.mkdir(parents=True, exist_ok=True)
OUT_AUTO.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------------------
# Deal parameters - Larkfield Mortgage Funding 2025-1 PLC (fictional)
# ---------------------------------------------------------------------------
DEAL = "Larkfield Mortgage Funding 2025-1 PLC"
ORIGINATOR = "Larkfield Building Society"
N_LOANS = 2000
CUTOFF_0 = pd.Timestamp("2025-06-30")       # pool cut-off date at closing
LAST_CUTOFF = pd.Timestamp("2026-09-30")
CUTOFFS = pd.date_range(CUTOFF_0, LAST_CUTOFF, freq="ME")

# Fictional rate paths (annual %, applied to the month ending on the date)
BBR = {d: r for d, r in zip(CUTOFFS, np.round(np.linspace(4.25, 3.50, len(CUTOFFS)) * 4) / 4)}
SONIA = {d: round(BBR[d] - 0.05, 4) for d in CUTOFFS}

NUTS1 = {  # UK NUTS 2021 level-1 regions with pool weights
    "UKI": 0.16, "UKJ": 0.17, "UKK": 0.10, "UKH": 0.10, "UKG": 0.09,
    "UKF": 0.08, "UKD": 0.10, "UKE": 0.08, "UKC": 0.04, "UKL": 0.05,
    "UKM": 0.03,
}


def month_add(ts: pd.Timestamp, months: int) -> pd.Timestamp:
    return (ts + pd.DateOffset(months=months)) + pd.offsets.MonthEnd(0)


# ---------------------------------------------------------------------------
# 1. Static loan characteristics at origination
# ---------------------------------------------------------------------------
orig_dates = pd.to_datetime(
    rng.integers(pd.Timestamp("2018-01-01").value // 10**9,
                 pd.Timestamp("2025-04-30").value // 10**9, N_LOANS), unit="s"
).normalize() + pd.offsets.MonthEnd(0)

term_years = rng.choice([20, 25, 30, 35], N_LOANS, p=[0.10, 0.45, 0.30, 0.15])
orig_val = np.round(rng.lognormal(np.log(310_000), 0.38, N_LOANS), -3)
orig_ltv = np.clip(rng.beta(5, 2.2, N_LOANS) * 95, 40, 95).round(2)
orig_bal = np.round(orig_val * orig_ltv / 100, -2)
amort = rng.choice(["FRXX", "BLLT"], N_LOANS, p=[0.88, 0.12])  # French (annuity) / bullet (interest-only)
purpose = rng.choice(["PURC", "RMRT"], N_LOANS, p=[0.55, 0.45])
fix_years = rng.choice([2, 5], N_LOANS, p=[0.55, 0.45])
reversion = [month_add(d, 12 * f) for d, f in zip(orig_dates, fix_years)]
year = orig_dates.year.values
base_fixed = np.select([year <= 2021, year == 2022, year >= 2023], [1.8, 3.2, 4.9])
fixed_rate = np.round(base_fixed + rng.normal(0, 0.35, N_LOANS) + (orig_ltv - 75) / 100, 2)
margin = np.round(rng.uniform(2.75, 3.75, N_LOANS), 2)  # reversion margin over BBR
income = np.round(orig_bal / rng.uniform(3.0, 4.5, N_LOANS), -2)
region = rng.choice(list(NUTS1), N_LOANS, p=np.array(list(NUTS1.values())) / sum(NUTS1.values()))
hpi_growth = {k: v for k, v in zip(NUTS1, rng.uniform(0.00, 0.035, len(NUTS1)))}  # annual

loan_ids = [f"LMF25-{i:05d}" for i in range(1, N_LOANS + 1)]
obligor_ids = [f"OBL-{i:06d}" for i in rng.permutation(np.arange(100001, 100001 + N_LOANS))]


def annuity(balance, rate_pct, n_months):
    r = rate_pct / 1200
    if n_months <= 0:
        return balance
    if r == 0:
        return balance / n_months
    return balance * r / (1 - (1 + r) ** -n_months)


# Roll each loan forward from origination to the pool cut-off date (performing),
# then simulate monthly through LAST_CUTOFF with arrears, prepayments, defaults.
state = []
for i in range(N_LOANS):
    bal = orig_bal[i]
    d = orig_dates[i]
    maturity = month_add(d, 12 * term_years[i])
    while d < CUTOFF_0:
        d = month_add(d, 1)
        rate = fixed_rate[i] if d <= reversion[i] else BBR.get(d, 4.25) + margin[i]
        n_left = (maturity.year - d.year) * 12 + (maturity.month - d.month) + 1
        if amort[i] == "FRXX":
            pay = annuity(bal, rate, n_left)
            bal = max(bal - (pay - bal * rate / 1200), 0)
    state.append(dict(bal=round(bal, 2), arrears_m=0, arrears_bal=0.0, status="PERF",
                      maturity=maturity, last_arrears=None, default_date=None,
                      default_amt=0.0, recov=0.0, redeemed=None, cum_prepay=0.0,
                      restructured=None))

rows = []
cashflows = []   # per loan per month collections, for the waterfall
recovery_queue = {}  # month -> list of (loan index, amount)

for m_idx, cut in enumerate(CUTOFFS):
    for i in range(N_LOANS):
        s = state[i]
        if s["redeemed"] is not None and s["redeemed"] < cut:
            continue
        if s["status"] == "DFLT" and s["default_date"] < cut and m_idx > 0:
            # defaulted loans stay in the tape with zero current balance until recovery
            pass
        rate = fixed_rate[i] if cut <= reversion[i] else BBR[cut] + margin[i]
        n_left = (s["maturity"].year - cut.year) * 12 + (s["maturity"].month - cut.month) + 1
        sched_int = sched_prin = coll_int = coll_prin = prepay = recov = 0.0
        if m_idx > 0 and s["status"] not in ("DFLT", "REDM"):
            bal = s["bal"]
            sched_int = bal * rate / 1200
            sched_prin = (annuity(bal, rate, n_left) - sched_int) if amort[i] == "FRXX" else 0.0
            pay_due = sched_int + sched_prin
            # arrears transitions
            a = s["arrears_m"]
            u = rng.random()
            if a == 0:
                miss = u < 0.004
                cure = False
            else:
                miss = u < 0.55
                cure = (not miss) and rng.random() < 0.45
            if miss:
                s["arrears_m"] += 1
                s["arrears_bal"] += pay_due
                s["last_arrears"] = cut
                # interest capitalises into arrears, principal not collected
            else:
                coll_int, coll_prin = sched_int, sched_prin
                s["bal"] = bal - sched_prin
                if cure and a > 0:
                    coll_int += s["arrears_bal"]   # arrears paid back as revenue (simplified)
                    s["arrears_m"], s["arrears_bal"] = 0, 0.0
                    if rng.random() < 0.25:
                        s["restructured"] = cut
            # default at six months in arrears
            if s["arrears_m"] >= 6:
                s["status"] = "DFLT"
                s["default_date"] = cut
                s["default_amt"] = round(s["bal"], 2)
                severity = rng.uniform(0.05, 0.30)
                rec_month = month_add(cut, int(rng.integers(4, 9)))
                recovery_queue.setdefault(rec_month, []).append((i, round(s["bal"] * (1 - severity), 2)))
            elif s["arrears_m"] > 0:
                s["status"] = "ARRE"
            else:
                s["status"] = "RNAR" if s["restructured"] is not None else "PERF"
            # prepayments (only for performing loans)
            if s["status"] in ("PERF", "RNAR"):
                at_reversion = (cut == reversion[i])
                p_full = 0.55 if at_reversion else 0.0065
                if rng.random() < p_full or n_left <= 1:
                    prepay = s["bal"]
                    s["cum_prepay"] += prepay
                    s["bal"] = 0.0
                    s["status"] = "REDM"
                    s["redeemed"] = cut
                elif rng.random() < 0.02:
                    part = round(s["bal"] * rng.uniform(0.02, 0.10), 2)
                    prepay = part
                    s["cum_prepay"] += part
                    s["bal"] -= part
            s["bal"] = round(max(s["bal"], 0.0), 2)
        # recoveries landing this month
        for (j, amt) in recovery_queue.get(cut, []):
            if j == i:
                recov = amt
                state[i]["recov"] += amt
        cashflows.append(dict(cutoff=cut.date(), loan=loan_ids[i], interest=round(coll_int, 2),
                              sched_principal=round(coll_prin, 2), prepayment=round(prepay, 2),
                              recovery=round(recov, 2),
                              new_default=round(s["default_amt"], 2) if s["default_date"] == cut else 0.0))
        cur_val = orig_val[i] * (1 + hpi_growth[region[i]]) ** ((cut - orig_dates[i]).days / 365.25)
        cur_bal = 0.0 if s["status"] in ("DFLT", "REDM") else s["bal"]
        rows.append({
            "RREL1": f"LARKFIELD2025-1-{cut:%Y%m}",
            "RREL2": loan_ids[i],
            "RREL4": obligor_ids[i],
            "RREL6": cut.date(),
            "RREL7": CUTOFF_0.date(),
            "RREL9": s["redeemed"].date() if s["redeemed"] is not None else None,
            "RREL10": "Y",
            "RREL11": region[i],
            "RREL12": 2021,
            "RREL16": income[i],
            "RREL18": "GBP",
            "RREL23": orig_dates[i].date(),
            "RREL24": s["maturity"].date(),
            "RREL25": int(term_years[i] * 12),
            "RREL27": purpose[i],
            "RREL28": "GBP",
            "RREL29": orig_bal[i],
            "RREL30": round(cur_bal, 2),
            "RREL35": amort[i],
            "RREL37": "MNTH",
            "RREL38": "MNTH",
            "RREL39": round(sched_int + sched_prin, 2),
            "RREL40": round(100 * cur_bal / income[i], 2),
            "RREL42": "FLCF",
            "RREL43": round(rate, 2),
            "RREL46": margin[i],
            "RREL51": reversion[i].date(),
            "RREL63": s["redeemed"].date() if s["redeemed"] is not None else None,
            "RREL64": round(s["cum_prepay"], 2),
            "RREL65": s["restructured"].date() if s["restructured"] is not None else None,
            "RREL66": s["last_arrears"].date() if s["last_arrears"] is not None else None,
            "RREL67": round(s["arrears_bal"], 2) if s["status"] == "ARRE" else 0.0,
            "RREL68": int(s["arrears_m"] * 30) if s["status"] in ("ARRE", "DFLT") else 0,
            "RREL69": s["status"],
            "RREL71": s["default_amt"] if s["status"] == "DFLT" else 0.0,
            "RREL72": s["default_date"].date() if s["default_date"] is not None else None,
            "RREL73": round(s["default_amt"] - s["recov"], 2) if (s["status"] == "DFLT" and s["recov"] > 0) else 0.0,
            "RREL74": round(s["recov"], 2),
            "RREL82": ORIGINATOR,
            "RREL84": "GB",
            # Collateral section (RREC) carried on the same row for teaching convenience
            "RREC6": region[i],
            "RREC7": "FOWN",
            "RREC12": round(100 * cur_bal / cur_val, 2),
            "RREC13": round(cur_val, -3),
            "RREC14": "IDXD",
            "RREC16": orig_ltv[i],
            "RREC17": orig_val[i],
            "RREC19": orig_dates[i].date(),
            "RREC22": "GBP",
        })

tape = pd.DataFrame(rows)
tape.to_csv(OUT_RMBS / "larkfield_2025_1_loan_tape.csv", index=False)
cf = pd.DataFrame(cashflows)
cf.to_csv(OUT_RMBS / "larkfield_2025_1_loan_cashflows.csv", index=False)

# ---------------------------------------------------------------------------
# 2. Notes and monthly waterfall (priority of payments)
# ---------------------------------------------------------------------------
pool0 = tape.loc[tape.RREL6 == CUTOFF_0.date(), "RREL30"].sum()
NOTES = {  # class: (share of pool, margin over SONIA %)
    "A": (0.88, 0.55), "B": (0.05, 1.10), "C": (0.04, 1.60), "D": (0.03, 2.40),
}
note_bal = {k: round(pool0 * v[0], 2) for k, v in NOTES.items()}
note_bal["D"] = round(pool0 - sum(note_bal[k] for k in "ABC"), 2)  # notes sum exactly to the pool
initial_notes = dict(note_bal)
RF_REQUIRED = round(0.015 * pool0, 2)
reserve = RF_REQUIRED          # funded at closing
pdl = {k: 0.0 for k in NOTES}  # principal deficiency ledger per class
TRUSTEE_FEE, CASH_MANAGER_FEE, SERVICER_BPS = 2000.0, 1500.0, 15

wf_rows, note_rows = [], []
for m_idx, cut in enumerate(CUTOFFS):
    if m_idx == 0:
        for k in NOTES:
            note_rows.append(dict(cutoff=cut.date(), cls=k, opening=note_bal[k], principal_paid=0.0,
                                  interest_due=0.0, interest_paid=0.0, closing=note_bal[k],
                                  pdl_balance=0.0, coupon_pct=round(SONIA[cut] + NOTES[k][1], 4)))
        continue
    prev = CUTOFFS[m_idx - 1]
    days = (cut - prev).days
    c = cf[cf.cutoff == cut.date()]
    prior_pool = tape.loc[tape.RREL6 == prev.date(), "RREL30"].sum()
    rev = round(c.interest.sum() + c.recovery.sum(), 2)
    prin = round(c.sched_principal.sum() + c.prepayment.sum(), 2)
    new_def = round(c.new_default.sum(), 2)
    # losses debited to the PDL in reverse order of seniority
    loss = new_def
    for k in ["D", "C", "B", "A"]:
        room = note_bal[k] - pdl[k]
        take = min(loss, room)
        pdl[k] = round(pdl[k] + take, 2)
        loss = round(loss - take, 2)
    lines = []
    avail = rev

    def pay(label, due, from_reserve=False):
        global avail, reserve
        paid = min(avail, due)
        avail = round(avail - paid, 2)
        drawn = 0.0
        if from_reserve and paid < due:
            drawn = min(reserve, due - paid)
            reserve = round(reserve - drawn, 2)
            paid += drawn
        lines.append(dict(cutoff=cut.date(), waterfall="Revenue", item=label, due=round(due, 2),
                          paid=round(paid, 2), reserve_drawn=round(drawn, 2)))
        return round(paid, 2)

    servicer_fee = round(prior_pool * SERVICER_BPS / 10000 * days / 365, 2)
    pay("(a) Trustee fee", TRUSTEE_FEE, True)
    pay("(b) Cash manager fee", CASH_MANAGER_FEE, True)
    pay("(c) Servicer fee", servicer_fee, True)
    int_due, int_paid, pdl_cure = {}, {}, 0.0
    letters = iter("defghijklmnop")
    for k in NOTES:
        cpn = SONIA[cut] + NOTES[k][1]
        int_due[k] = round(note_bal[k] * cpn / 100 * days / 365, 2)
        int_paid[k] = pay(f"({next(letters)}) Class {k} interest", int_due[k], k in ("A", "B"))
        cure = pay(f"({next(letters)}) Class {k} PDL", pdl[k])
        pdl[k] = round(pdl[k] - cure, 2)
        pdl_cure += cure
    pay(f"({next(letters)}) Replenish reserve fund", 0.0)
    top_up = min(avail, RF_REQUIRED - reserve)
    lines[-1]["due"] = round(RF_REQUIRED - reserve, 2)
    lines[-1]["paid"] = round(top_up, 2)
    reserve = round(reserve + top_up, 2)
    avail = round(avail - top_up, 2)
    lines.append(dict(cutoff=cut.date(), waterfall="Revenue", item=f"({next(letters)}) Residual to certificate holders",
                      due=round(avail, 2), paid=round(avail, 2), reserve_drawn=0.0))
    excess = avail
    # principal waterfall - sequential
    p_avail = round(prin + pdl_cure, 2)
    p_letter = iter("abcd")
    for k in NOTES:
        paid = min(p_avail, note_bal[k])
        lines.append(dict(cutoff=cut.date(), waterfall="Principal", item=f"({next(p_letter)}) Class {k} principal",
                          due=round(note_bal[k], 2), paid=round(paid, 2), reserve_drawn=0.0))
        opening = note_bal[k]
        note_bal[k] = round(note_bal[k] - paid, 2)
        p_avail = round(p_avail - paid, 2)
        note_rows.append(dict(cutoff=cut.date(), cls=k, opening=opening, principal_paid=round(paid, 2),
                              interest_due=int_due[k], interest_paid=int_paid[k], closing=note_bal[k],
                              pdl_balance=pdl[k], coupon_pct=round(SONIA[cut] + NOTES[k][1], 4)))
    wf_rows += lines
    wf_rows.append(dict(cutoff=cut.date(), waterfall="Summary", item="Available revenue receipts", due=rev, paid=rev, reserve_drawn=0.0))
    wf_rows.append(dict(cutoff=cut.date(), waterfall="Summary", item="Available principal receipts", due=prin, paid=prin, reserve_drawn=0.0))
    wf_rows.append(dict(cutoff=cut.date(), waterfall="Summary", item="New defaults debited to PDL", due=new_def, paid=new_def, reserve_drawn=0.0))
    wf_rows.append(dict(cutoff=cut.date(), waterfall="Summary", item="Reserve fund closing balance", due=RF_REQUIRED, paid=reserve, reserve_drawn=0.0))
    wf_rows.append(dict(cutoff=cut.date(), waterfall="Summary", item="Excess spread released", due=excess, paid=excess, reserve_drawn=0.0))

wf = pd.DataFrame(wf_rows)
wf.to_csv(OUT_RMBS / "larkfield_2025_1_waterfall.csv", index=False)
notes = pd.DataFrame(note_rows)
notes.to_csv(OUT_RMBS / "larkfield_2025_1_notes.csv", index=False)

# Invariant used throughout the book: notes outstanding - PDL = performing pool balance
check = []
for cut in CUTOFFS:
    n = notes[notes.cutoff == cut.date()]
    pool = tape.loc[tape.RREL6 == cut.date(), "RREL30"].sum()
    check.append(round(n.closing.sum() - n.pdl_balance.sum() - pool, 2))
assert max(abs(x) for x in check) < 1.0, check

deal_terms = dict(
    deal=DEAL, originator=ORIGINATOR, servicer=ORIGINATOR, cash_manager="Northgate Trust Services Limited",
    trustee="Northgate Trustees Limited", closing_date="2025-06-30", first_ipd="2025-07-31",
    payment_frequency="Monthly", pool_cutoff_balance=round(pool0, 2),
    notes={k: dict(initial_balance=initial_notes[k], index="Compounded Daily SONIA", margin_pct=NOTES[k][1])
           for k in NOTES},
    reserve_fund_required=RF_REQUIRED, servicer_fee_bps=SERVICER_BPS,
    trustee_fee_monthly=TRUSTEE_FEE, cash_manager_fee_monthly=CASH_MANAGER_FEE,
    sonia_path_pct={str(k.date()): v for k, v in SONIA.items()},
    bbr_path_pct={str(k.date()): v for k, v in BBR.items()},
)
(OUT_RMBS / "larkfield_2025_1_deal_terms.json").write_text(json.dumps(deal_terms, indent=2))

# ---------------------------------------------------------------------------
# 3. US auto ABS - Reg AB II Schedule AL style asset-level file (one period)
# ---------------------------------------------------------------------------
N_AUTO = 1500
period_end = date(2026, 9, 30)
makes = {"Toyota": ["Camry", "RAV4", "Corolla"], "Ford": ["F-150", "Escape", "Explorer"],
         "Honda": ["Civic", "CR-V", "Accord"], "Chevrolet": ["Silverado", "Equinox", "Malibu"],
         "Nissan": ["Rogue", "Altima", "Sentra"], "Hyundai": ["Tucson", "Elantra", "Santa Fe"]}
make = rng.choice(list(makes), N_AUTO, p=[0.22, 0.20, 0.18, 0.16, 0.12, 0.12])
model = [rng.choice(makes[mk]) for mk in make]
new_used = rng.choice(["1", "2"], N_AUTO, p=[0.45, 0.55])  # 1 = new, 2 = used
orig = pd.to_datetime(rng.integers(pd.Timestamp("2022-01-01").value // 10**9,
                                   pd.Timestamp("2025-03-31").value // 10**9, N_AUTO), unit="s").normalize()
term = rng.choice([48, 60, 72, 75, 84], N_AUTO, p=[0.08, 0.27, 0.40, 0.13, 0.12])
amt = np.round(rng.lognormal(np.log(31_000), 0.35, N_AUTO), 2)
fico = np.clip(rng.normal(705, 55, N_AUTO), 540, 850).astype(int)
apr = np.round(np.clip(18 - (fico - 540) * 0.045 + rng.normal(0, 1.2, N_AUTO), 1.9, 23.9), 2)
age_m = ((pd.Timestamp(period_end) - orig).days / 30.44).astype(int)
r = apr / 1200
pmt = amt * r / (1 - (1 + r) ** -term)
beg = np.round(amt * (1 + r) ** (age_m - 1) - pmt * (((1 + r) ** (age_m - 1) - 1) / r), 2)
beg = np.clip(beg, 0, None)
delinq_days = rng.choice([0, 30, 60, 90, 120], N_AUTO, p=[0.925, 0.04, 0.017, 0.01, 0.008])
paid = np.where(delinq_days == 0, pmt, 0)
end = np.round(np.clip(beg - (paid - beg * r), 0, None), 2)
chargeoff = np.where((delinq_days == 120) & (rng.random(N_AUTO) < 0.6), end, 0.0)
end = np.where(chargeoff > 0, 0.0, end)
auto = pd.DataFrame({
    "assetTypeNumber": "Auto loan",
    "assetNumber": [f"RWAR25A-{i:06d}" for i in range(1, N_AUTO + 1)],
    "reportingPeriodBeginningDate": "2026-09-01",
    "reportingPeriodEndingDate": str(period_end),
    "originatorName": "Redwater Auto Finance LLC",
    "originationDate": orig.strftime("%m/%Y"),
    "originalLoanAmount": amt,
    "originalLoanTerm": term,
    "loanMaturityDate": [(d + pd.DateOffset(months=int(t))).strftime("%m/%Y") for d, t in zip(orig, term)],
    "originalInterestRatePercentage": apr / 100,
    "interestCalculationTypeCode": "2",
    "originalInterestRateTypeCode": "1",
    "vehicleManufacturerName": make,
    "vehicleModelName": model,
    "vehicleNewUsedCode": new_used,
    "vehicleModelYear": [int(d.year - (0 if nu == "1" else rng.integers(1, 6))) for d, nu in zip(orig, new_used)],
    "vehicleValueAmount": np.round(amt / rng.uniform(0.85, 1.15, N_AUTO), 2),
    "obligorCreditScoreType": "FICO 8",
    "obligorCreditScore": fico,
    "paymentToIncomePercentage": np.round(rng.uniform(0.04, 0.16, N_AUTO), 4),
    "reportingPeriodBeginningLoanBalanceAmount": beg,
    "nextReportingPeriodPaymentAmountDue": np.round(pmt, 2),
    "reportingPeriodInterestRatePercentage": apr / 100,
    "scheduledInterestAmount": np.round(beg * r, 2),
    "scheduledPrincipalAmount": np.round(pmt - beg * r, 2),
    "totalActualAmountPaid": np.round(paid, 2),
    "reportingPeriodActualEndBalanceAmount": end,
    "currentDelinquencyStatus": delinq_days,
    "chargedoffPrincipalAmount": np.round(chargeoff, 2),
    "zeroBalanceCode": np.where(chargeoff > 0, "4", ""),     # 4 = charged-off (Schedule AL item 3(f)(24)(ii))
})
auto = auto[auto.reportingPeriodBeginningLoanBalanceAmount > 0].reset_index(drop=True)  # loans paid off before the period are not reported
auto.to_csv(OUT_AUTO / "redwater_2025_a_asset_level.csv", index=False)

print(f"RMBS tape rows: {len(tape):,}  loans: {N_LOANS}  months: {len(CUTOFFS)}")
print(f"Pool at cut-off: GBP {pool0:,.2f}; at {LAST_CUTOFF.date()}: GBP "
      f"{tape.loc[tape.RREL6 == LAST_CUTOFF.date(), 'RREL30'].sum():,.2f}")
print(f"Max |notes - PDL - pool| over all months: {max(abs(x) for x in check):.2f}")
print(f"Auto loans: {len(auto)}")
