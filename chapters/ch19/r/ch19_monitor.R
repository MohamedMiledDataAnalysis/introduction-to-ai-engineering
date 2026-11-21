# Chapter 19 - From a month of request logs to daily metrics, alerts and explanations
source("aie_r/monitor.R")
options(width = 130)
df <- load_log("data/logs/requests_2026_10.jsonl")
m <- daily_metrics(df)
cat(sprintf("%d requests, %d days; total cost at the illustrative price: $%.2f\n\n",
            nrow(df), length(unique(df$day)), sum(m$cost_usd)))
show <- m[m$domain == "sf", -2]
names(show) <- c("day", "requests", "errors", "review", "p50_s", "p95_s", "tokens", "cost_usd")
print(show, row.names = FALSE, digits = 4)
cat("\n"); print(alerts(m), row.names = FALSE)
sf <- df[df$domain == "sf" & df$status != "error", ]
cat("\nReview rate by prompt version (SF):\n")
print(round(tapply(sf$status != "verified", sf$prompt, mean), 3))
