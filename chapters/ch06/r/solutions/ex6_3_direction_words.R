# Exercise 6.3 - Direction words must agree with the sign
# Run from the root of the repository:  Rscript chapters/ch06/r/solutions/ex6_3_direction_words.R

source("aie_r/factcheck.R")
nav <- read.csv("data/am/fund_nav_monthly.csv")
bm  <- read.csv("data/am/benchmark_returns_monthly.csv")
f <- nav$net_return[nav$fund_code == "HGEF"]; b <- bm$HGEF
last <- length(f)
facts <- list(
  "fund 1 month"      = list(value = 100 * f[last], unit = "percent"),
  "benchmark 1 month" = list(value = 100 * b[length(b)], unit = "percent"),
  "relative 1 month"  = list(value = 100 * (f[last] - b[length(b)]), unit = "percent"))

positive <- c("outperformed", "outperforming", "ahead of", "beat", "above")
negative <- c("lagged", "lagging", "behind", "underperformed", "below")
direction_errors <- function(text, facts, window = 40) {
  errors <- character(0)
  for (r in check_text(text, facts)) for (name in r$hits) {
    if (!startsWith(name, "relative")) next
    context <- tolower(substr(text, max(1, r$figure$start - window), r$figure$start - 1))
    has <- function(words) any(vapply(words, grepl, TRUE, x = context, fixed = TRUE))
    v <- facts[[name]]$value
    if (v < 0 && has(positive)) errors <- c(errors, paste0(r$figure$raw, ": says ahead, fact is negative"))
    if (v > 0 && has(negative)) errors <- c(errors, paste0(r$figure$raw, ": says behind, fact is positive"))
  }
  errors
}

for (draft in c("In September the fund returned 4.53% against 5.03% for its benchmark, lagging by 0.50%.",
                 "In September the fund returned 4.53% against 5.03% for its benchmark, outperforming by 0.50%."))
  print(direction_errors(draft, facts))
