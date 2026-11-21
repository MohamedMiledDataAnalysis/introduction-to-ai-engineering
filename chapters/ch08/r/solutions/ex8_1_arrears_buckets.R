# Exercise 8.1 - The arrears_buckets tool
# Run from the root of the repository:  Rscript chapters/ch08/r/solutions/ex8_1_arrears_buckets.R

source("aie_r/tools.R")
cat(registry$arrears_buckets$description, "\n")
cat(run_tool(list(name = "arrears_buckets", arguments = list(cutoff_date = "2026-09-30"))), "\n")
cat(run_tool(list(name = "arrears_buckets", arguments = list(cutoff_date = "2026-09"))), "\n")
