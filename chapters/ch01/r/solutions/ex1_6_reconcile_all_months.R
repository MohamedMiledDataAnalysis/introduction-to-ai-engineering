# Exercise 1.6 - Reconcile notes, PDL and pool for every month
tape  <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
notes <- read.csv("data/sf/rmbs/larkfield_2025_1_notes.csv")

pool      <- tapply(tape$RREL30, tape$RREL6, sum)
notes_out <- tapply(notes$closing, notes$cutoff, sum)
pdl       <- tapply(notes$pdl_balance, notes$cutoff, sum)

check <- round(notes_out - pdl - pool, 2)
print(check)
cat("Largest absolute difference:", max(abs(check)), "\n")
