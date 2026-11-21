# Exercise 12.2 - A repayment loan whose balance rose
# Run from the root of the repository:  Rscript chapters/ch12/r/solutions/ex12_2_balance_rose.R

tape <- read.csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv", stringsAsFactors = FALSE)

prev <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
prev <- prev[prev$RREL6 == "2026-08-31", c("RREL2", "RREL30")]
names(prev)[2] <- "RREL30_prev"
m <- merge(tape, prev, by = "RREL2", all.x = TRUE)
print(m[m$RREL35 == "FRXX" & !is.na(m$RREL30_prev) & m$RREL30 > m$RREL30_prev + 1,
        c("RREL2", "RREL30", "RREL30_prev", "RREL69")])
