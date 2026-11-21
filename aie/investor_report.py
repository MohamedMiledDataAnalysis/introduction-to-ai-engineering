"""The monthly Larkfield investor report: tables computed by code, a commentary drafted by the model."""
import pandas as pd

from aie.factcheck import check_text

TAPE = "data/sf/rmbs/larkfield_2025_1_loan_tape.csv"
CF = "data/sf/rmbs/larkfield_2025_1_loan_cashflows.csv"
NOTES = "data/sf/rmbs/larkfield_2025_1_notes.csv"
WF = "data/sf/rmbs/larkfield_2025_1_waterfall.csv"


def month_figures(cutoff):
    tape, cf, notes, wf = pd.read_csv(TAPE), pd.read_csv(CF), pd.read_csv(NOTES), pd.read_csv(WF)
    dates = sorted(tape["RREL6"].unique())
    prev = dates[dates.index(cutoff) - 1]
    m, p = tape[tape["RREL6"] == cutoff], tape[tape["RREL6"] == prev]
    c = cf[cf["cutoff"] == cutoff]
    pool, prev_pool = m["RREL30"].sum(), p["RREL30"].sum()
    arr = m[m["RREL69"] == "ARRE"]
    months = (arr["RREL68"] // 30).clip(upper=4)
    buckets = [(lab, int((months == k).sum()), arr.loc[months == k, "RREL30"].sum())
               for k, lab in [(1, "1 month"), (2, "2 months"), (3, "3 months"), (4, "4-5 months")]]
    smm = c["prepayment"].sum() / (prev_pool - c["sched_principal"].sum())
    w = wf[wf["cutoff"] == cutoff]
    summary = w[w["waterfall"] == "Summary"].set_index("item")["paid"]
    n = notes[notes["cutoff"] == cutoff].set_index("cls")
    prev_arrears = p.loc[p["RREL69"] == "ARRE", "RREL30"].sum() / prev_pool
    return {
        "cutoff": cutoff, "previous": prev, "pool": pool, "prev_pool": prev_pool,
        "loans": int((m["RREL30"] > 0).sum()), "arrears_ratio": 100 * arr["RREL30"].sum() / pool,
        "prev_arrears_ratio": 100 * prev_arrears, "buckets": buckets,
        "cpr": 100 * (1 - (1 - smm) ** 12), "revenue": summary["Available revenue receipts"],
        "principal": summary["Available principal receipts"], "new_defaults": summary["New defaults debited to PDL"],
        "reserve": summary["Reserve fund closing balance"], "excess_spread": summary["Excess spread released"],
        "notes": n, "waterfall": w[w["waterfall"] != "Summary"],
    }


def reconcile(f):
    """Checks that must pass before the report is released."""
    n = f["notes"]
    w = f["waterfall"]
    rev = w[w["waterfall"] == "Revenue"]
    prin = w[w["waterfall"] == "Principal"]
    pdl_cures = rev[rev["item"].str.contains("PDL")]["paid"].sum()
    return {                                      # bool(): True/False, not numpy's np.True_
        "notes - PDL = pool": bool(round(n["closing"].sum() - n["pdl_balance"].sum() - f["pool"], 2) == 0),
        "revenue paid = revenue available + reserve drawn":
            bool(round(rev["paid"].sum() - f["revenue"] - rev["reserve_drawn"].sum(), 2) == 0),
        "principal paid = principal available + PDL cures":
            bool(round(prin["paid"].sum() - f["principal"] - pdl_cures, 2) == 0),
    }


def facts(f):
    """Every figure the commentary may quote, with the words that must surround it."""
    n = f["notes"]
    return {
        "pool balance": (f["pool"], "money"), "loans": (f["loans"], "number"),
        "arrears ratio": (f["arrears_ratio"], "percent"), "previous arrears ratio": (f["prev_arrears_ratio"], "percent"),
        "CPR": (f["cpr"], "percent"), "revenue receipts": (f["revenue"], "money"),
        "principal receipts": (f["principal"], "money"), "excess spread": (f["excess_spread"], "money"),
        "reserve fund": (f["reserve"], "money"), "new defaults": (f["new_defaults"], "money"),
        "Class A closing": (n.loc["A", "closing"], "money"), "Class A principal paid": (n.loc["A", "principal_paid"], "money"),
    }


def facts_for_prompt(f):
    change = f["arrears_ratio"] - f["prev_arrears_ratio"]
    return "\n".join([
        f"- Period: collection period ending {f['cutoff']}",
        f"- Pool balance: £{f['pool'] / 1e6:.2f} million ({f['loans']:,} loans)",
        f"- Arrears ratio: {f['arrears_ratio']:.2f}% ({'up' if change > 0 else 'down'} from "
        f"{f['prev_arrears_ratio']:.2f}% the previous month)",
        f"- Annualised prepayment rate (CPR): {f['cpr']:.1f}%",
        f"- Revenue receipts: £{f['revenue'] / 1e6:.2f} million; principal receipts: £{f['principal'] / 1e6:.2f} million",
        f"- New defaults debited to the principal deficiency ledger: £{f['new_defaults']:,.2f}",
        f"- Class A notes: £{f['notes'].loc['A', 'principal_paid'] / 1e6:.2f} million repaid; closing balance "
        f"£{f['notes'].loc['A', 'closing'] / 1e6:.2f} million",
        f"- Reserve fund: £{f['reserve']:,.2f}, at its required amount",
        f"- Excess spread released to the residual certificate holders: £{f['excess_spread'] / 1e6:.2f} million",
    ])


def template_commentary(f):
    change = f["arrears_ratio"] - f["prev_arrears_ratio"]
    return (f"In the period ending {f['cutoff']}, principal receipts of £{f['principal'] / 1e6:.2f} million were applied "
            f"sequentially and repaid £{f['notes'].loc['A', 'principal_paid'] / 1e6:.2f} million of Class A notes. "
            f"The arrears ratio {'rose' if change > 0 else 'fell'} to {f['arrears_ratio']:.2f}% from "
            f"{f['prev_arrears_ratio']:.2f}%, and the annualised prepayment rate was {f['cpr']:.1f}%. "
            f"The reserve fund stands at its required amount of £{f['reserve']:,.2f}.")


def render_markdown(f, commentary):
    n = f["notes"]
    lines = [f"# Larkfield Mortgage Funding 2025-1 PLC — Investor report", "",
             f"Collection period ending {f['cutoff']}, paid on the 20th of the following month. "
             "Fictional document for teaching.", "",
             "## Commentary", "", commentary, "",
             "## Pool", "", "| Item | Value |", "|---|---:|",
             f"| Current balance | £{f['pool']:,.2f} |", f"| Loans outstanding | {f['loans']:,} |",
             f"| Arrears ratio | {f['arrears_ratio']:.2f}% |", f"| Annualised prepayment rate (CPR) | {f['cpr']:.1f}% |",
             "", "## Arrears", "", "| Months in arrears | Loans | Balance |", "|---|---:|---:|"]
    lines += [f"| {lab} | {k} | £{b:,.2f} |" for lab, k, b in f["buckets"]]
    lines += ["", "## Notes", "", "| Class | Opening | Principal paid | Interest paid | Closing | Coupon |",
              "|---|---:|---:|---:|---:|---:|"]
    lines += [f"| {c} | £{r.opening:,.2f} | £{r.principal_paid:,.2f} | £{r.interest_paid:,.2f} | £{r.closing:,.2f} | "
              f"{r.coupon_pct:.2f}% |" for c, r in n.iterrows()]
    lines += ["", "## Priority of payments", "", "| Waterfall | Item | Due | Paid |", "|---|---|---:|---:|"]
    lines += [f"| {r.waterfall} | {r.item} | £{r.due:,.2f} | £{r.paid:,.2f} |" for r in f["waterfall"].itertuples()]
    return "\n".join(lines) + "\n"


def check_commentary(text, f):
    return [(fig.raw, hits) for fig, hits in check_text(text, facts(f))]
