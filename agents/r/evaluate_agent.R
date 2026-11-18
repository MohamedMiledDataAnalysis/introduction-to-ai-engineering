# Evaluate one of the final-project agents on its evaluation set: answers, tools used and status.
# Run from the repository root:  Rscript agents/r/evaluate_agent.R sf     (or am)
source("aie_r/assistants.R"); source("aie_r/evals.R")
args <- commandArgs(trailingOnly = TRUE); domain <- if (length(args)) args[1] else "sf"
cases <- read.csv(sprintf("evals/%s_agent_eval.csv", domain), colClasses = "character")
a <- new_assistant(domain)
rows <- lapply(seq_len(nrow(cases)), function(i) {
  r <- ask_assistant(a, cases$question[i])
  tools <- setdiff(vapply(r$trace, `[[`, "", "name"), "verification")
  data.frame(id = cases$id[i], answer = r$answer, status = r$status, tools = paste(tools, collapse = ";"),
             right_tool = cases$expected_tool[i] == "" || cases$expected_tool[i] %in% tools, tokens = r$tokens)
})
out <- do.call(rbind, rows)
res <- run_eval(cases, setNames(as.list(out$answer), out$id))
out <- merge(out, res[, c("id", "passed", "reason")], by = "id")
write.csv(out, sprintf("evals/candidates/%s_agent_run_%s.csv", domain, format(Sys.time(), "%Y%m%d_%H%M")), row.names = FALSE)
ci <- wilson_interval(sum(out$passed), nrow(out))
cat(sprintf("%s agent, prompt %s\n  correct answers : %d/%d (95%% interval %.0f%%-%.0f%%)\n  right tool used : %d/%d\n",
            toupper(domain), a$version, sum(out$passed), nrow(out), 100 * ci[1], 100 * ci[2], sum(out$right_tool), nrow(out)))
print(table(out$status))
for (i in which(!out$passed | !out$right_tool))
  cat(sprintf("  %s %s | tools: %s | %s\n", out$id[i], out$reason[i], out$tools[i], substr(out$answer[i], 1, 80)))
