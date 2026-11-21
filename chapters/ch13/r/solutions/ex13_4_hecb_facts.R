# Exercise 13.4 - The facts of the HECB commentary
# Run from the root of the repository:  Rscript chapters/ch13/r/solutions/ex13_4_hecb_facts.R

source("aie_r/sqlguard.R"); source("aie_r/tools.R")
hecb <- "h.fund_code = 'HECB' AND h.month_end = '2026-09-30'"
one <- function(sql) run_sql(sql)$rows[[1]][1]      # the single value of a one-cell result
hecb_facts_for_prompt <- function() {
  p <- fund_performance("HECB", 1)
  duration <- one(paste("SELECT SUM(h.weight * s.modified_duration) / SUM(h.weight)",
                        "FROM holdings h JOIN securities s ON h.isin = s.isin WHERE", hecb))
  bbb <- one(paste("SELECT SUM(h.weight) FROM holdings h JOIN securities s ON h.isin = s.isin",
                   "WHERE", hecb, "AND s.rating IN ('BBB+', 'BBB', 'BBB-')"))
  cash <- one(paste("SELECT SUM(h.weight) FROM holdings h WHERE", hecb, "AND h.isin = 'CASH-EUR'"))
  paste(c(sprintf("- Fund return: %.2f%%", p$fund_return_pct),
          sprintf("- Benchmark return: %.2f%%", p$benchmark_return_pct),
          sprintf("- Relative return: %+.2f%%", p$relative_return_pct),
          sprintf("- Modified duration of the bonds: %.2f years", duration),
          sprintf("- Share of the bonds rated BBB+ to BBB-: %.2f%%", 100 * bbb / (1 - cash)),
          sprintf("- Cash: %.2f%%", 100 * cash)), collapse = "\n")
}
cat(hecb_facts_for_prompt(), "\n")
