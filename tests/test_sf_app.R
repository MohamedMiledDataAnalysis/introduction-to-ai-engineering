# Test the SF app's server logic without a browser:  Rscript tests/test_sf_app.R
library(shiny)
Sys.setenv(AIE_ROOT = getwd())
app <- source("apps/sf_app/app.R")$value      # the app object, built from the repository root
testServer(app, {
  session$setInputs(date = "2026-09-30", rdate = "2026-09-30")
  stopifnot(output$kpi_arrears == "0.84%", output$kpi_cpr == "14.8%")
  cat("KPI arrears:", output$kpi_arrears, "| CPR:", output$kpi_cpr, "| pool:", output$kpi_pool, "\n")
  cat("Rule breaches on the received tape:", nrow(flags), "\n")
  cat("Template email check:", output$email_check, "\n")
  session$setInputs(question = "Should I buy the Class B notes?", ask = 1)
  cat("Assistant status for an advice question:", log()[[1]]$r$status, "\n")
})
cat("SF app server tests passed\n")
