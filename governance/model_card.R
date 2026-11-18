# Assemble the documentation of one AI use case from the repository's own evidence.
source("aie_r/evals.R"); source("aie_r/monitor.R"); source("aie_r/prompts.R")

model_card <- function(use_case_id, eval_file, answers_file, log_file) {
  inv <- read.csv("governance/inventory.csv", stringsAsFactors = FALSE)
  u <- inv[inv$id == use_case_id, ]
  cases <- read.csv(eval_file, colClasses = "character")
  cand <- read.csv(answers_file, colClasses = "character")
  res <- run_eval(cases, setNames(as.list(cand$answer), cand$id))
  ci <- wilson_interval(sum(res$passed), nrow(res))
  m <- daily_metrics(load_log(log_file)); m <- m[m$domain == u$domain, ]
  fields <- c("purpose", "users", "decision_impact", "model", "human_review", "data", "owner", "risk_tier")
  label <- function(k) { k <- gsub("_", " ", k); paste0(toupper(substr(k, 1, 1)), substring(k, 2)) }
  c(sprintf("# Model card — %s %s", use_case_id, u$name), "", "| Item | Value |", "|---|---|",
    sprintf("| %s | %s |", vapply(fields, label, ""), unlist(u[fields])),
    sprintf("| Prompt version | %s (hash %s) |", u$prompt, load_prompt(u$prompt)$hash), "",
    "## Evaluation", "", sprintf("- Evaluation set: `%s`, %d cases.", eval_file, nrow(res)),
    sprintf("- Result: %d/%d passed (95%% interval %.0f%% to %.0f%%).", sum(res$passed), nrow(res), 100 * ci[1], 100 * ci[2]),
    sprintf("- Failed cases: %s.", paste(res$id[!res$passed], collapse = ", ")), "",
    "## Monitoring (period of the log)", "",
    sprintf("- Requests: %d; days: %d.", sum(m$requests), length(unique(m$day))),
    sprintf("- Error rate: %.1f%%.", 100 * sum(m$error_rate * m$requests) / sum(m$requests)),
    sprintf("- Review rate (median day): %.1f%%; worst day: %.1f%%.", 100 * median(m$review_rate), 100 * max(m$review_rate)),
    sprintf("- Median response time (median day): %.1f s.", median(m$p50_seconds)))
}

if (sys.nframe() == 0) {
  card <- model_card("AI-SF-01", "evals/sf_prospectus_qa.csv", "evals/candidates/prospectus_qa_run_a.csv",
                     "data/logs/requests_2026_10.jsonl")
  cat(card, sep = "\n")
}
