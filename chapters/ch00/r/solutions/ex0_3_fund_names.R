# Exercise 0.3 - Read the funds file in R
# Run from the root of the repository:  Rscript chapters/ch00/r/solutions/ex0_3_fund_names.R

funds <- read.csv("data/am/funds.csv")
print(funds$name)
