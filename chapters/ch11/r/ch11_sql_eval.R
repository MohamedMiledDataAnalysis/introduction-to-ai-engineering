# Chapter 11 - Check model-written SQL: guard it, run it read-only, compare its result with the reference
source("aie_r/sqlguard.R")
cases <- read.csv("evals/am_sql_qa.csv", stringsAsFactors = FALSE)
cands <- read.csv("evals/candidates/am_sql_candidates.csv",
                  stringsAsFactors = FALSE)
cands <- setNames(cands$sql, cands$id)
passed <- 0
for (i in seq_len(nrow(cases))) {
  ref <- run_sql(cases$reference_sql[i]); got <- run_sql(cands[[cases$id[i]]])
  ok <- same_result(ref, got, ordered = cases$ordered[i] == 1)
  passed <- passed + ok
  detail <- if (!is.null(got$error)) got$error else
    paste("first row:", paste(got$rows[1, ], collapse = ", "))
  cat(sprintf("%s %s  reference first row: %s\n      candidate %s\n",
              cases$id[i], if (ok) "PASS" else "FAIL",
              paste(ref$rows[1, ], collapse = ", "), detail))
}
cat(sprintf("\n%d/%d candidate queries return the reference result\n",
            passed, nrow(cases)))
