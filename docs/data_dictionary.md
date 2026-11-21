# Data dictionary

All data is fictional. Layouts follow real templates, named below.

## 1. Structured finance — Larkfield Mortgage Funding 2025-1 PLC (UK RMBS)

### `larkfield_2025_1_loan_tape.csv`

One row per loan per monthly data cut-off date, from 30 June 2025 (pool cut-off) to 30 September 2026. A loan redeemed in full appears in the month of redemption with status `REDM` and no longer appears afterwards. A defaulted loan stays in the tape with status `DFLT` and a current principal balance of zero.

Field codes and names are those of Annex II (Underlying exposures information — residential real estate) of Delegated Regulation (EU) 2020/1224 in the EU, reproduced for the UK in chapter 11 of the FCA's Securitisation sourcebook (SECN 11) since 1 November 2024, with the same field codes. Collateral fields (`RREC`) sit on the same row as the loan for teaching convenience; in a regulatory submission they form a separate section.

| Code | Field name | Content in this file |
|---|---|---|
| RREL1 | Unique Identifier | Securitisation identifier and reporting month |
| RREL2 | Original Underlying Exposure Identifier | Loan identifier, `LMF25-00001` to `LMF25-02000` |
| RREL4 | Original Obligor Identifier | Borrower identifier |
| RREL6 | Data Cut-Off Date | Month-end reporting date |
| RREL7 | Pool Addition Date | 30 June 2025 for every loan |
| RREL9 | Redemption Date | Date of redemption in full, blank otherwise |
| RREL10 | Resident | `Y` |
| RREL11 | Geographic Region — Obligor | NUTS 1 code (UKC to UKM) |
| RREL12 | Geographic Region Classification | NUTS version year, 2021 |
| RREL16 | Primary Income | Annual gross income at origination, GBP |
| RREL18 | Primary Income Currency | `GBP` |
| RREL23 | Origination Date | |
| RREL24 | Maturity Date | |
| RREL25 | Original Term | Months |
| RREL27 | Purpose | `PURC` purchase, `RMRT` remortgage |
| RREL28 | Currency Denomination | `GBP` |
| RREL29 | Original Principal Balance | GBP |
| RREL30 | Current Principal Balance | GBP at the cut-off date |
| RREL35 | Amortisation Type | `FRXX` French (annuity repayment), `BLLT` bullet (interest-only) |
| RREL37 / RREL38 | Scheduled Principal / Interest Payment Frequency | `MNTH` |
| RREL39 | Payment Due | Scheduled payment for the month, GBP |
| RREL40 | Debt To Income Ratio | Current balance divided by primary income, % |
| RREL42 | Interest Rate Type | `FLCF` fixed rate with compulsory future switch to floating |
| RREL43 | Current Interest Rate | % per annum |
| RREL46 | Current Interest Rate Margin | Margin over Bank of England Base Rate that applies after the fixed period ends, %. In a real submission this reversion margin goes in RREL50 (Revision Margin 1), and RREL46 holds the margin in force today, which a fixed-rate loan does not have; the file simplifies. |
| RREL51 | Interest Revision Date 1 | End of the initial fixed-rate period |
| RREL63 | Prepayment Date | Date of redemption in full |
| RREL64 | Cumulative Prepayments | GBP since the pool cut-off date |
| RREL65 | Date Of Restructuring | Date of the last cure that was treated as a restructuring |
| RREL66 | Date Last In Arrears | |
| RREL67 | Arrears Balance | GBP |
| RREL68 | Number Of Days In Arrears | Months in arrears × 30 |
| RREL69 | Account Status | `PERF` performing, `ARRE` arrears, `RNAR` restructured — no arrears, `DFLT` defaulted under the transaction's definition (six monthly payments unpaid; in a real submission, check the ESMA code list, where `DFLT` refers to the definition of default of Article 178 of the CRR), `REDM` redeemed |
| RREL71 | Default Amount | Balance at default, GBP |
| RREL72 | Default Date | |
| RREL73 | Allocated Losses | Default amount minus recoveries, once recoveries are received |
| RREL74 | Cumulative Recoveries | GBP |
| RREL82 | Originator Name | Larkfield Building Society |
| RREL84 | Originator Establishment Country | `GB` |
| RREC6 | Geographic Region — Collateral | NUTS 1 code |
| RREC7 | Occupancy Type | `FOWN` owner-occupied |
| RREC12 | Current Loan-To-Value | % on the indexed valuation |
| RREC13 | Current Valuation Amount | Indexed valuation, GBP |
| RREC14 | Current Valuation Method | `IDXD` indexed |
| RREC16 | Original Loan-To-Value | % |
| RREC17 | Original Valuation Amount | GBP |
| RREC19 | Original Valuation Date | |
| RREC22 | Collateral Currency | `GBP` |

### Other RMBS files

| File | Content |
|---|---|
| `larkfield_2025_1_loan_cashflows.csv` | Per loan per month: interest, scheduled principal, prepayment, recovery and new default amounts collected |
| `larkfield_2025_1_notes.csv` | Per class per month: opening balance, interest due and paid, principal paid, closing balance, PDL balance, coupon. Interest is accrued by collection period (actual days ÷ 365), so the first payment, on 20 August 2025, pays 31 days (July 2025) rather than the 51 days from closing that a real deal would accrue: a simplification kept for teaching |
| `larkfield_2025_1_waterfall.csv` | Each line of the revenue and principal priority of payments for each interest payment date, plus summary lines. The line *Available principal receipts* is the principal collected in the period, before the PDL credits that items (e), (g), (i) and (k) add to it; the credits are shown as their own lines |
| `larkfield_2025_1_deal_terms.json` | Parties, note classes, margins, fees, reserve fund, fictional SONIA and Base Rate paths |
| `larkfield_2025_1_prospectus_excerpt.md` | Prospectus excerpt: structure, priority of payments, pool statistics, eligibility criteria, risk factors |

**Reconciliation used throughout the book:** for every month, notes outstanding minus the principal deficiency ledger balance equals the current balance of the non-defaulted pool, to the penny.

## 2. Structured finance — Redwater Auto Receivables Trust 2025-A (US auto ABS)

`redwater_2025_a_asset_level.csv` — one row per loan for the reporting period September 2026. Column names are the asset-level field tags of SEC Regulation AB II, Schedule AL, auto loans. Rates are decimals (0.0725 = 7.25%). `vehicleNewUsedCode`: 1 new, 2 used. `currentDelinquencyStatus`: days past due. `zeroBalanceCode` 4: charged off (1 prepaid or matured, 2 third-party sale, 3 repurchased or replaced).

## 3. Asset management — Harbourline Asset Management

| File | Content |
|---|---|
| `funds.csv` | The three funds: code, name, share class, ISIN, SFDR classification, ongoing charges, benchmark, launch date, size, risk indicator, recommended holding period |
| `security_master.csv` | 90 equities and 80 euro corporate bonds: ISIN, name, issuer, sector, country, currency, market capitalisation or amount outstanding, coupon, maturity, rating, modified duration, spread |
| `security_returns_monthly.csv` | Monthly total return in EUR for every security, for the 36 months from October 2023 to September 2026 |
| `fund_holdings_monthly.csv` | Month-end weight and market value of every holding in every fund; funds rebalance to target at each quarter-end |
| `fund_nav_monthly.csv` | NAV per share and monthly net return, after ongoing charges |
| `benchmark_returns_monthly.csv` | Monthly benchmark return for each fund |
| `transactions_2026_09.csv` | Trades in September 2026 |
| `issuer_esg.csv` | ESG score (0 to 100), carbon intensity (tCO2e per EUR million revenue), controversy flag, excluded activity |
| `hgef_attribution_2026_09.csv` | Brinson sector attribution for the global equity fund in September 2026, gross of fees; allocation + selection + interaction sum to the fund's gross return minus the benchmark return |

**Identifiers.** ISINs start with `ZZ`, a prefix that no country uses, so a fictional ISIN never matches a real security. The twelfth character is a valid ISO 6166 check digit.
