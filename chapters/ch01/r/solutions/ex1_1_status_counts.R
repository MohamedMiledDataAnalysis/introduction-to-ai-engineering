# Exercise 1.1 - Number of loans by account status at 30 September 2026
# Run from the root of the repository:  Rscript chapters/ch01/r/solutions/ex1_1_status_counts.R

tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep  <- tape[tape$RREL6 == "2026-09-30", ]
print(sort(table(sep$RREL69), decreasing = TRUE))
