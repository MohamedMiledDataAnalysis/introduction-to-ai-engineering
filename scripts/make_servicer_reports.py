"""
Monthly servicer reports for Larkfield 2025-1 as PDF files (fictional), July to September 2026,
written from the loan tape and cash flows. The September report contains one discrepancy with the
tape, on purpose: prepayments are overstated by GBP 12,000.00 (Chapter 16).
Run:  python scripts/make_servicer_reports.py
"""
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/sf/rmbs/servicer_reports"
OUT.mkdir(parents=True, exist_ok=True)
tape = pd.read_csv(ROOT / "data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
cf = pd.read_csv(ROOT / "data/sf/rmbs/larkfield_2025_1_loan_cashflows.csv")
styles = getSampleStyleSheet()
DISCREPANCY = {"2026-09-30": 12_000.00}


def money(x):
    return f"GBP {x:,.2f}"


for cutoff, label in [("2026-07-31", "July 2026"), ("2026-08-31", "August 2026"), ("2026-09-30", "September 2026")]:
    m = tape[tape.RREL6 == cutoff]
    c = cf[cf.cutoff == cutoff]
    arr = m[m.RREL69 == "ARRE"]
    months = (arr.RREL68 // 30).clip(upper=4)
    prepay = c.prepayment.sum() + DISCREPANCY.get(cutoff, 0.0)
    story = [Paragraph("Larkfield Building Society — Mortgage Servicing", styles["Title"]),
             Paragraph(f"Monthly servicer report to the Issuer and the Cash Manager: Larkfield Mortgage Funding 2025-1 PLC. "
                       f"Collection period: {label}. Fictional document for teaching.", styles["Normal"]),
             Spacer(1, 10), Paragraph("1. Collections", styles["Heading2"])]
    rows = [["Item", "Amount"], ["Interest collected", money(c.interest.sum())],
            ["Scheduled principal collected", money(c.sched_principal.sum())],
            ["Prepayments and redemptions", money(prepay)], ["Recoveries on defaulted loans", money(c.recovery.sum())]]
    story.append(Table(rows, colWidths=[260, 160], style=TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (1, 1), (1, -1), "RIGHT")])))
    story += [Spacer(1, 10), Paragraph("2. Portfolio", styles["Heading2"]),
              Paragraph(f"At the end of the collection period the portfolio comprised {int((m.RREL30 > 0).sum()):,} loans "
                        f"with an aggregate current balance of {money(m.RREL30.sum())}. "
                        f"{int((m.RREL69 == 'REDM').sum())} loans redeemed in full during the period.", styles["Normal"]),
              Spacer(1, 10), Paragraph("3. Arrears", styles["Heading2"])]
    rows = [["Months in arrears", "Loans", "Balance"]] + \
           [[lab, str(int((months == k).sum())), money(arr.RREL30[months == k].sum())]
            for k, lab in [(1, "1"), (2, "2"), (3, "3"), (4, "4 to 5")]]
    story.append(Table(rows, colWidths=[160, 100, 160], style=TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT")])))
    newdef = c.new_default.sum()
    story += [Spacer(1, 10), Paragraph("4. Defaults", styles["Heading2"]),
              Paragraph(f"New defaults in the period: {int((c.new_default > 0).sum())} loans, {money(newdef)}." if newdef
                        else "There were no new defaults in the period.", styles["Normal"])]
    SimpleDocTemplate(str(OUT / f"servicer_report_{cutoff[:7].replace('-', '_')}.pdf"), pagesize=A4).build(story)
    print("written", cutoff)
