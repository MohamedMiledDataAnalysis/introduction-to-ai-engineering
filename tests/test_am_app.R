# Test the AM app's server logic without a browser:  Rscript tests/test_am_app.R
library(shiny)
Sys.setenv(AIE_ROOT = getwd())
app <- source("apps/am_app/app.R")$value
testServer(app, {
  session$setInputs(fund = "HGEF", months = "12")
  stopifnot(output$kpi_rel == "-1.40%")
  cat("HGEF 1 year: fund", output$kpi_fund, "| benchmark", output$kpi_bench, "| relative", output$kpi_rel, "\n")
  stopifnot(grepl("Upland Telecom", output$top))   # the Portfolio tab lists the top ten holdings
  session$setInputs(fund = "HECB")
  cat("HECB ongoing charges:", output$kpi_ocf, "\n")
  r <- check_commentary(draft, hf$facts)
  cat("Draft commentary figures checked:", length(r), "| problems:", sum(vapply(r, function(x) !is.na(x$problem), TRUE)), "\n")
  session$setInputs(question = "Will HECB outperform next year?", ask = 1)
  cat("Assistant status for a forecast question:", log()[[1]]$r$status, "\n")
  ollama_url <<- "http://127.0.0.1:9"     # nothing listens there: the model cannot be reached
  session$setInputs(question = "What was the one-year return of HGEF?", ask = 2)
  stopifnot(log()[[1]]$r$status == "error")  # an answer with status error; the session keeps running
  cat("Assistant status with the model unreachable:", log()[[1]]$r$status, "\n")
})
cat("AM app server tests passed\n")
