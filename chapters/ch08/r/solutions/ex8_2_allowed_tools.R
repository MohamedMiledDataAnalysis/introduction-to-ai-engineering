# Exercise 8.2 - A tool outside the allowed list
# Run from the root of the repository:  Rscript chapters/ch08/r/solutions/ex8_2_allowed_tools.R

source("aie_r/tools.R")

cat(run_tool(list(name = "pool_summary", arguments = list(cutoff_date = "2026-09-30")),
             allowed = c("fund_performance", "top_holdings")))

cat("\n")
