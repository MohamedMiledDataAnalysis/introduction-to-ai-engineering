# Daily monitoring metrics from the request log, and alert rules.
library(jsonlite)
price_per_m_tokens <- 3.00   # illustrative blended price, USD per million tokens, for a paid model
thresholds <- c(error_rate = 0.02, review_rate = 0.10, p95_seconds = 12.0)

load_log <- function(path) {
  df <- stream_in(file(path), verbose = FALSE)
  df$day <- as.Date(substr(df$ts, 1, 10))
  df
}

daily_metrics <- function(df) {
  keys <- unique(df[, c("day", "domain")]); keys <- keys[order(keys$day, keys$domain), ]
  rows <- lapply(seq_len(nrow(keys)), function(i) {
    x <- df[df$day == keys$day[i] & df$domain == keys$domain[i], ]; ok <- x[x$status != "error", ]
    data.frame(day = keys$day[i], domain = keys$domain[i], requests = nrow(x),
               error_rate = round(mean(x$status == "error"), 4),
               review_rate = if (nrow(ok)) round(mean(ok$status != "verified"), 4) else 0,
               p50_seconds = if (nrow(ok)) round(median(ok$seconds), 4) else 0,
               p95_seconds = if (nrow(ok)) round(unname(quantile(ok$seconds, 0.95)), 4) else 0,
               avg_tokens = if (nrow(ok)) round(mean(ok$tokens), 4) else 0,
               cost_usd = round(sum(x$tokens) / 1e6 * price_per_m_tokens, 4))
  })
  do.call(rbind, rows)
}

alerts <- function(m) {
  out <- list()
  for (metric in names(thresholds)) {
    hit <- m[m[[metric]] > thresholds[[metric]], ]
    if (nrow(hit)) out[[metric]] <- data.frame(day = hit$day, domain = hit$domain, metric = metric,
                                               value = hit[[metric]], limit = thresholds[[metric]])
  }
  res <- do.call(rbind, out); res[order(res$day, res$domain), ]
}
