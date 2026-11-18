# Chapter 11 - Ask a question in English; get SQL and a guarded result
source("aie_r/text_to_sql.R")
q <- "What is the weight of Information Technology in the Global Equity Fund?"
out <- ask_database(q)
cat("SQL:    ", out$sql, "\n")
if (!is.null(out$result$error)) cat("Error:  ", out$result$error, "\n") else print(out$result$rows)
