"""Data-quality rules for a received loan tape. Each rule returns the rows that break it."""
import pandas as pd

RULES = {
    "negative_balance": ("Current balance (RREL30) is negative",
                         lambda t, d: t["RREL30"] < 0),
    "balance_above_original": ("Current balance exceeds the original balance by more than 10% on a repayment loan",
                               lambda t, d: (t["RREL35"] == "FRXX") & (t["RREL30"] > 1.10 * t["RREL29"])),
    "maturity_before_origination": ("Maturity date (RREL24) is before the origination date (RREL23)",
                                    lambda t, d: pd.to_datetime(t["RREL24"]) <= pd.to_datetime(t["RREL23"])),
    "default_without_180_days": ("Status DFLT with fewer than 180 days in arrears (prospectus: six payments)",
                                 lambda t, d: (t["RREL69"] == "DFLT") & (t["RREL68"] < 180)),
    "arrears_without_balance": ("Status ARRE with no arrears balance (RREL67)",
                                lambda t, d: (t["RREL69"] == "ARRE") & (t["RREL67"].fillna(0) <= 0)),
    "ltv_implausible": ("Current LTV (RREC12) above 150%",
                        lambda t, d: t["RREC12"] > 150),
    "rate_out_of_range": ("Current interest rate (RREL43) outside 0% to 15%",
                          lambda t, d: (t["RREL43"] < 0) | (t["RREL43"] > 15)),
    "missing_region": ("Geographic region (RREL11) is missing",
                       lambda t, d: t["RREL11"].isna()),
    "performing_with_days_in_arrears": ("Status PERF or RNAR with days in arrears (RREL68) above 0",
                                        lambda t, d: t["RREL69"].isin(["PERF", "RNAR"]) & (t["RREL68"] > 0)),
    "original_ltv_above_95": ("Original LTV (RREC16) above the 95% eligibility limit",
                              lambda t, d: t["RREC16"] > 95),
    "wrong_cutoff_date": ("Data cut-off date (RREL6) differs from the reporting date",
                          lambda t, d: t["RREL6"] != d),
    "duplicate_loan": ("Loan identifier (RREL2) appears more than once",
                       lambda t, d: t["RREL2"].duplicated(keep=False)),
}


def run_rules(tape, cutoff_date):
    """Return one row per (loan, rule) breach."""
    found = []
    for rule, (description, test) in RULES.items():
        mask = test(tape, cutoff_date).fillna(False)
        for loan in tape.loc[mask, "RREL2"].unique():
            found.append({"loan_id": loan, "rule": rule, "description": description})
    return pd.DataFrame(found, columns=["loan_id", "rule", "description"])
