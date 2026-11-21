# Exercise 12.1 - A consistency rule for the LTV
# Run from the root of the repository:  Rscript chapters/ch12/r/solutions/ex12_1_ltv_rule.R

source("aie_r/dq.R")
tape <- read.csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv", stringsAsFactors = FALSE)

dq_rules$ltv_inconsistent <- list(
  "Original LTV (RREC16) disagrees with original balance / original valuation (RREL29 / RREC17) by more than 0.5 points",
  function(t, d) abs(100 * t$RREL29 / t$RREC17 - t$RREC16) > 0.5)

found <- run_rules(tape, "2026-09-30")
print(found[found$rule == "ltv_inconsistent", c("loan_id", "rule")], row.names = FALSE)
