# Exercise 23.4 - the review queue
# Needs the mock model replaying the scripted answer with a wrong figure. From the repository root:
#   MOCK_SCRIPT=tools/scripts/ch23_review.json python tools/mock_ollama.py &
#   LANG=C.UTF-8 Rscript tests/solutions/test_ex23_4.R
library(shiny)
Sys.setenv(AIE_ROOT = getwd())
unlink("logs/review_queue.csv")                                          # start from an empty queue
app <- suppressPackageStartupMessages(source("apps/solutions/ex23_4/app.R")$value)
testServer(app, {
  session$setInputs(question = "How many loans were two months in arrears at 30 September 2026?", ask = 1)
  r <- log()[[1]]$r
  cat(r$status, "|", paste(r$unsupported, collapse = ", "), "\n")
  stopifnot(r$status == "needs_review")
  session$setInputs(question = "Should I buy the Class B notes?", ask = 2)
  cat("Advice question:", log()[[1]]$r$status, "\n")
})
q <- read.csv("logs/review_queue.csv")
print(q[, c("question", "unsupported")], row.names = FALSE)
stopifnot(nrow(q) == 1, q$unsupported == "£1,098,476.03")                # only needs_review answers enter the queue
cat("Exercise 23.4 test passed\n")
