# Exercise 19.2 - A rolling review rate
# Run from the root of the repository:  Rscript chapters/ch19/r/solutions/ex19_2_rolling_review_rate.R

library(jsonlite)
df <- stream_in(file("data/logs/requests_2026_10.jsonl"), verbose = FALSE)

ok <- df[df$status != "error", ]
ok$day <- substr(ok$ts, 1, 10)
rolling_review <- function(domain, window = 5) {
  x <- ok[ok$domain == domain, ]
  flagged <- tapply(x$status != "verified", x$day, sum)
  total <- tapply(x$status != "verified", x$day, length)
  roll <- function(v) stats::filter(v, rep(1, window), sides = 1)
  setNames(round(as.numeric(roll(flagged) / roll(total)), 3), names(flagged))
}
r <- rolling_review("sf"); print(r[!is.na(r) & r > 0.10])
