# Exercise 19.1 - The outage of 7 October
# Run from the root of the repository:  Rscript chapters/ch19/r/solutions/ex19_1_outage.R

library(jsonlite)
df  <- stream_in(file("data/logs/requests_2026_10.jsonl"), verbose = FALSE)
err <- df[df$status == "error", ]
cat(min(err$ts), max(err$ts), "\n"); print(table(err$domain)); print(range(err$seconds))
