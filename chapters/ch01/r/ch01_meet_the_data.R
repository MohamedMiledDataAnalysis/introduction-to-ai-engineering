# Chapter 1 - Applied example: meet the two datasets and reconcile them
# Run from the root of the repository:  Rscript chapters/ch01/r/ch01_meet_the_data.R

# ---- Structured finance: Larkfield Mortgage Funding 2025-1 ----
tape  <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
notes <- read.csv("data/sf/rmbs/larkfield_2025_1_notes.csv")

cut  <- "2026-09-30"
pool <- sum(tape$RREL30[tape$RREL6 == cut])
n    <- notes[notes$cutoff == cut, ]
notes_out <- sum(n$closing)
pdl       <- sum(n$pdl_balance)

gbp <- function(x) format(round(x, 2), big.mark = ",", nsmall = 2)
cat("Larkfield 2025-1 at", cut, "\n")
cat("  Pool balance (RREL30):   GBP", gbp(pool), "\n")
cat("  Notes outstanding:       GBP", gbp(notes_out), "\n")
cat("  PDL balance:             GBP", gbp(pdl), "\n")
cat("  Notes - PDL - pool:      GBP", gbp(notes_out - pdl - pool), "\n")

# ---- Asset management: Harbourline Global Equity Fund ----
nav <- read.csv("data/am/fund_nav_monthly.csv")
bm  <- read.csv("data/am/benchmark_returns_monthly.csv")

fund_1m <- nav$net_return[nav$fund_code == "HGEF" & nav$month_end == cut]
bm_1m   <- bm$HGEF[bm$month_end == cut]

pct <- function(x) sprintf("%.2f%%", 100 * x)
cat("\nHarbourline Global Equity Fund, September 2026\n")
cat("  Fund return (net):      ", pct(fund_1m), "\n")
cat("  Benchmark return:       ", pct(bm_1m), "\n")
cat("  Relative return:        ", sprintf("%+.2f%%", 100 * (fund_1m - bm_1m)), "\n")
