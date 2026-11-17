# Exercise 1.1 - Number of loans by account status at 30 September 2026
tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep  <- tape[tape$RREL6 == "2026-09-30", ]
print(sort(table(sep$RREL69), decreasing = TRUE))
