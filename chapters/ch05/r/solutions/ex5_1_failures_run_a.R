# Exercise 5.1 - Run A's failures and their reasons
# Run from the root of the repository:  Rscript chapters/ch05/r/solutions/ex5_1_failures_run_a.R

source("aie_r/evals.R")
cases <- read.csv("evals/sf_prospectus_qa.csv", colClasses = "character")
results <- list()
for (run in c("a", "b")) {
  cand <- read.csv(sprintf("evals/candidates/prospectus_qa_run_%s.csv",
                           run), colClasses = "character")
  answers <- setNames(as.list(cand$answer), cand$id)
  res <- run_eval(cases, answers)
  results[[run]] <- res
  cat(sprintf("Run %s: %d/%d passed (%.0f%%)\n", toupper(run),
              sum(res$passed), nrow(res), 100 * mean(res$passed)))
  print(aggregate(passed ~ answer_type, data = res,
        FUN = function(x) c(sum = sum(x), count = length(x))))
  cat("\n")
}
cat("Failures in run A:\n")
print(results$a[!results$a$passed, c("id", "reason")], row.names = FALSE)
cat("Failures in run B:\n")
print(results$b[!results$b$passed, c("id", "reason")], row.names = FALSE)
cmp <- compare_runs(results$a, results$b)
cat("\nRegressions from A to B:", paste(cmp$regressions, collapse = ", "), "\n")
cat("Fixes from A to B:      ", paste(cmp$fixes, collapse = ", "), "\n")
