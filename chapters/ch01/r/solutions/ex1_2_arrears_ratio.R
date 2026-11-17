# Exercise 1.2 - Arrears ratio by balance at 30 September 2026
tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
sep  <- tape[tape$RREL6 == "2026-09-30", ]
arrears <- sum(sep$RREL30[sep$RREL69 == "ARRE"])
pool    <- sum(sep$RREL30)
cat(sprintf("Balance in arrears: GBP %s\n", format(arrears, big.mark = ",", nsmall = 2)))
cat(sprintf("Pool balance:       GBP %s\n", format(pool, big.mark = ",", nsmall = 2)))
cat(sprintf("Arrears ratio:      %.2f%%\n", 100 * arrears / pool))
