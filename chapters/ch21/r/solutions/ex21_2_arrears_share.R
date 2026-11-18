# Exercise 21.2 - Share of the arrears balance three months or more in arrears, and the new evaluation case
# Run from the root of the repository:  Rscript chapters/ch21/r/solutions/ex21_2_arrears_share.R
suppressPackageStartupMessages(source("aie_r/agent.R"))
cut <- "2026-09-30"

# 1. The figures, from the tool the agent would call
result <- arrears_buckets(cut)
bal <- vapply(result$buckets, `[[`, 0, "balance_gbp")
lab <- vapply(result$buckets, `[[`, "", "bucket")
total <- sum(bal); three_plus <- sum(bal[lab %in% c("3 months", "4-5 months")])
share <- round(100 * three_plus / total, 2)
for (i in seq_along(bal))
  cat(sprintf("%-11s%3d loans  £%14s\n", lab[i], result$buckets[[i]]$loans, formatC(bal[i], format = "f", digits = 2, big.mark = ",")))
cat(sprintf("Three months or more: £%s of £%s = %.2f%%\n", formatC(three_plus, format = "f", digits = 2, big.mark = ","),
            formatC(total, format = "f", digits = 2, big.mark = ","), share))

# 2. Checks: the two tools agree, and the share sits where it must
stopifnot(round(total, 2) == pool_summary(cut)$arrears_balance_gbp)
share_3m_only <- round(100 * bal[3] / total, 2)
stopifnot(share_3m_only < share, share < 100)
cat(sprintf("Checks passed: buckets total = pool_summary arrears balance; %.2f%% < %.2f%% < 100%%\n", share_3m_only, share))

# 3. Design A: the tool as it is. A model that divides writes a figure no tool returned
answer <- sprintf("At 30 September 2026, %.2f%% of the arrears balance was three months or more in arrears.", share)
as_result <- function(r) list(list(name = "arrears_buckets", result = as.character(toJSON(r, auto_unbox = TRUE, digits = NA))))
u <- verify_answer(answer, as_result(result))
cat("Design A, unsupported figures:", if (length(u)) paste(u, collapse = ", ") else "none", "\n")

# 4. Design B: the tool also returns the shares, computed by code
arrears_buckets_with_shares <- function(cutoff_date, cumulative = TRUE) {
  r <- arrears_buckets(cutoff_date)
  b <- vapply(r$buckets, `[[`, 0, "balance_gbp"); tot <- sum(b)
  for (i in seq_along(b)) {
    r$buckets[[i]]$share_of_arrears_pct <- round(100 * b[i] / tot, 2)
    if (cumulative) r$buckets[[i]]$this_or_longer_share_of_arrears_pct <- round(100 * sum(b[i:length(b)]) / tot, 2)
  }
  r
}
for (cumulative in c(FALSE, TRUE)) {
  u <- verify_answer(answer, as_result(arrears_buckets_with_shares(cut, cumulative)))
  cat(sprintf("Design %s, unsupported figures: %s\n",
              if (cumulative) "B2, with cumulative shares" else "B1, shares per bucket only",
              if (length(u)) paste(u, collapse = ", ") else "none"))
}

# 5. The evaluation case, added to a copy of the evaluation set
ev <- read.csv("evals/sf_agent_eval.csv", stringsAsFactors = FALSE, colClasses = "character")
ev <- rbind(ev, data.frame(id = "A13",
  question = "What share of the pool's arrears balance was three months or more in arrears at 30 September 2026?",
  answer_type = "number", expected = sprintf("%.2f", share), tolerance = "0.005", keywords = "",
  expected_tool = "arrears_buckets"))
dir.create("evals/solutions", showWarnings = FALSE)
write.csv(ev, "evals/solutions/sf_agent_eval_ex21_2_r.csv", row.names = FALSE, na = "")
cat(sprintf("evals/solutions/sf_agent_eval_ex21_2_r.csv: %d cases, the last one A13 (expected %.2f)\n", nrow(ev), share))
