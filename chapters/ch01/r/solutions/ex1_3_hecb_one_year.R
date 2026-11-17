# Exercise 1.3 - One-year return of the euro corporate bond fund, checked against the factsheet
nav <- read.csv("data/am/fund_nav_monthly.csv")
bm  <- read.csv("data/am/benchmark_returns_monthly.csv")

fund  <- tail(nav$net_return[nav$fund_code == "HECB"], 12)
bench <- tail(bm$HECB, 12)
fund_1y  <- prod(1 + fund) - 1
bench_1y <- prod(1 + bench) - 1
cat(sprintf("Fund 1 year:      %.2f%%\n", 100 * fund_1y))
cat(sprintf("Benchmark 1 year: %.2f%%\n", 100 * bench_1y))
cat(sprintf("Relative:         %+.2f%%\n", 100 * (fund_1y - bench_1y)))
cat(sprintf("Relative from the rounded figures: %+.2f%%\n",
            round(100 * fund_1y, 2) - round(100 * bench_1y, 2)))
