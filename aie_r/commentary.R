# Facts for a fund commentary, and a checker that verifies value, label and direction of every figure.
source("aie_r/factcheck.R")
positive_words <- c("contributed", "added", "helped", "ahead", "outperform", "beat", "positive")
negative_words <- c("detracted", "cost", "hurt", "weighed", "behind", "lag", "underperform", "negative", "subtracted")

hgef_facts <- function(month = "2026-09-30") {
  nav <- read.csv("data/am/fund_nav_monthly.csv"); bm <- read.csv("data/am/benchmark_returns_monthly.csv")
  fund <- nav$net_return[nav$fund_code == "HGEF" & nav$month_end == month]
  bench <- bm$HGEF[bm$month_end == month]
  attr <- read.csv("data/am/hgef_attribution_2026_09.csv")
  attr$total <- attr$allocation + attr$selection + attr$interaction
  f <- function(value, unit, keys, signed) list(value = value, unit = unit, keys = keys, signed = signed)
  facts <- list("fund return" = f(100 * fund, "percent", c("fund", "returned", "return"), FALSE),
                "benchmark return" = f(100 * bench, "percent", c("benchmark", "index"), FALSE),
                "relative return" = f(100 * (fund - bench), "percent",
                                      c("relative", "benchmark", "lag", "behind", "ahead", "outperform", "underperform"), TRUE))
  for (i in seq_len(nrow(attr))) {
    s <- attr$sector[i]; keys <- c(tolower(s), tolower(strsplit(s, " ")[[1]][1]))
    facts[[paste(s, "effect")]] <- f(100 * attr$total[i], "percent", keys, TRUE)
    for (part in c("allocation", "selection", "interaction"))           # the three parts of the total effect
      facts[[paste(s, part, "effect")]] <- f(100 * attr[[part]][i], "percent",
        if (part == "allocation") c(part, "underweight", "overweight") else part, TRUE)
    facts[[paste(s, "active weight")]] <- f(100 * (attr$portfolio_weight[i] - attr$benchmark_weight[i]), "percent",
                                            c(keys, "weight", "overweight", "underweight"), FALSE)
    facts[[paste(s, "fund weight")]] <- f(100 * attr$portfolio_weight[i], "percent", c(keys, "weight", "overweight", "underweight", "against"), FALSE)
    facts[[paste(s, "benchmark weight")]] <- f(100 * attr$benchmark_weight[i], "percent", c(keys, "weight", "overweight", "underweight", "against"), FALSE)
  }
  list(facts = facts, attr = attr)
}

check_commentary <- function(text, facts, window = 90) {
  figs <- extract_figures(text)
  out <- list(); from <- 1
  for (i in seq_len(nrow(figs))) {
    pos <- regexpr(figs$raw[i], substring(text, from), fixed = TRUE) + from - 1
    from <- pos + nchar(figs$raw[i])
    before <- tolower(substr(text, max(1, pos - window), pos - 1))
    sentence <- tail(c("", strsplit(before, "[.;]\\s")[[1]]), 1)
    clause <- tail(c("", strsplit(sentence, ",\\s")[[1]]), 1)
    label_hits <- function(ctx) names(facts)[vapply(facts, function(x) figure_matches(figs[i, ], x$value, x$unit) &&
                                   any(vapply(x$keys, function(k) grepl(k, ctx, fixed = TRUE), TRUE)), TRUE)]
    hits <- label_hits(clause); if (!length(hits)) hits <- label_hits(sentence)
    problem <- if (length(hits)) NA else "no fact with this value and label"
    for (h in hits) {
      x <- facts[[h]]
      if (x$signed && x$value < 0 && any(vapply(positive_words, grepl, TRUE, clause, fixed = TRUE)))
        problem <- paste0("says positive, ", h, " is negative")
      if (x$signed && x$value > 0 && any(vapply(negative_words, grepl, TRUE, clause, fixed = TRUE)))
        problem <- paste0("says negative, ", h, " is positive")
    }
    out[[i]] <- list(raw = figs$raw[i], hits = hits, problem = problem)
  }
  out
}

facts_for_prompt <- function(attr, fund, bench) {
  lines <- c(sprintf("- Fund return: %.2f%%", 100 * fund), sprintf("- Benchmark return: %.2f%%", 100 * bench),
             sprintf("- Relative return: %+.2f%%", 100 * (fund - bench)))
  r <- attr[attr$sector != "Cash", ]; r <- r[order(r$total), ]
  pick <- rbind(head(r, 2), r[rev(tail(seq_len(nrow(r)), 2)), ])
  for (i in seq_len(nrow(pick))) {
    side <- if (pick$portfolio_weight[i] > pick$benchmark_weight[i]) "overweight" else "underweight"
    lines <- c(lines, sprintf(paste0("- %s: total effect %+.1fbp (%s), of which allocation %+.1fbp, selection %+.1fbp, ",
                                     "interaction %+.1fbp; the fund was %s (%.2f%% against %.2f%%)"),
                              pick$sector[i], 10000 * pick$total[i], if (pick$total[i] > 0) "contributed" else "detracted",
                              10000 * pick$allocation[i], 10000 * pick$selection[i], 10000 * pick$interaction[i],
                              side, 100 * pick$portfolio_weight[i], 100 * pick$benchmark_weight[i]))
  }
  paste(lines, collapse = "\n")
}

draft_commentary <- function(month = "2026-09-30") {
  source("aie_r/llm.R"); source("aie_r/prompts.R")
  hf <- hgef_facts(month)
  p <- load_prompt("fund_commentary_v1")
  prompt <- render(p$text, fund_name = "Harbourline Global Equity Fund", month = "September 2026",
                   facts = facts_for_prompt(hf$attr, hf$facts[["fund return"]]$value / 100,
                                            hf$facts[["benchmark return"]]$value / 100))
  text <- trimws(chat(list(list(role = "user", content = prompt)), temperature = 0.3)$text)
  list(text = text, report = check_commentary(text, hf$facts), prompt = p$hash)
}
