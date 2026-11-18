# Exercise 23.1 - the Reserve fund tile
# Run from the repository root:  LANG=C.UTF-8 Rscript tests/solutions/test_ex23_1.R
library(shiny)
Sys.setenv(AIE_ROOT = getwd())
app <- suppressPackageStartupMessages(source("apps/solutions/ex23_1/app.R")$value)
testServer(app, {
  for (d in c("2026-09-30", "2026-03-31", "2025-07-31")) {
    session$setInputs(date = d)
    cat(d, "| reserve fund tile:", output$kpi_reserve, "| raw value:", format(figures()$reserve, nsmall = 2), "\n")
    stopifnot(output$kpi_reserve == "£6.08m")          # never drawn: the same at every date
  }
})
cat("Exercise 23.1 test passed\n")
