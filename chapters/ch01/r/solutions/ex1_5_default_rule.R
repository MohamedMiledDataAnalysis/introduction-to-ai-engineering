# Exercise 1.5 - Check the prospectus definition of a Defaulted Loan against the tape
tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
defaulted <- tape[tape$RREL69 == "DFLT", ]
cat("Rows with status DFLT:       ", nrow(defaulted), "\n")
cat("Distinct defaulted loans:    ", length(unique(defaulted$RREL2)), "\n")
cat("Minimum days in arrears:     ", min(defaulted$RREL68), "\n")
cat("Rows breaking the rule:      ", sum(defaulted$RREL68 < 180), "\n")
