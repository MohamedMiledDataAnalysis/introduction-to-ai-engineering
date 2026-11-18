# Exercise 23.3 - the application in mode 2 with no service running
# Run from the repository root:  LANG=C.UTF-8 Rscript tests/solutions/test_ex23_3.R
library(shiny)
Sys.setenv(AIE_ROOT = getwd(), AIE_SERVICE_URL = "http://127.0.0.1:9")   # before source(): the file reads it when loaded
app <- suppressPackageStartupMessages(source("apps/solutions/ex23_3/app.R")$value)
testServer(app, {
  session$setInputs(date = "2026-03-31", rdate = "2026-03-31")
  stopifnot(output$kpi_arrears == "1.80%")                               # Dashboard works
  stopifnot(nchar(output$commentary) > 0)                                # Investor report works
  session$setInputs(question = "What was the arrears ratio in September 2026?", ask = 1)
  r <- log()[[1]]$r
  cat("Assistant status:", r$status, "\n", "Answer shown:", r$answer, "\n")
  stopifnot(r$status == "error", length(r$trace) == 0)                   # fails gracefully
})
Sys.unsetenv("AIE_SERVICE_URL")
cat("Exercise 23.3 test passed\n")
