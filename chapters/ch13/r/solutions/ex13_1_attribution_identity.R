# Exercise 13.1 - The attribution identity
# Run from the root of the repository:  Rscript chapters/ch13/r/solutions/ex13_1_attribution_identity.R

attr <- read.csv("data/am/hgef_attribution_2026_09.csv")
total_active <- sum(attr$allocation + attr$selection + attr$interaction)
nav <- read.csv("data/am/fund_nav_monthly.csv")
net <- nav$net_return[nav$fund_code == "HGEF" & nav$month_end == "2026-09-30"]
bm  <- read.csv("data/am/benchmark_returns_monthly.csv")
bench <- bm$HGEF[bm$month_end == "2026-09-30"]
cat(round(100 * total_active, 4), round(100 * (net + 0.0075 / 12 - bench), 4), "\n")
