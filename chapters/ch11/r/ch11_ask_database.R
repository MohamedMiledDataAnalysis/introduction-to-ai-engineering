# Chapter 11 - Ask a question in English; get SQL and a guarded result
# Before you run it: start the mock with the reference query of S01:
#   MOCK_SCRIPT=tools/scripts/ch11_sql.json python tools/mock_ollama.py
source("aie_r/text_to_sql.R")
q <- "What is the weight of Information Technology in the Global Equity Fund?"
out <- ask_database(q)
cat("SQL:    ", out$sql, "\n")
if (!is.null(out$result$error)) cat("Error:  ", out$result$error, "\n") else print(out$result$rows)
