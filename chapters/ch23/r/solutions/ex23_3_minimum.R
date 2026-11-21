# Exercise 23.3 - The application without its service, in its minimum form
# Run from the root of the repository:  Rscript chapters/ch23/r/solutions/ex23_3_minimum.R

library(shiny)
Sys.setenv(AIE_ROOT = getwd(), AIE_SERVICE_URL = "http://127.0.0.1:9")
app <- source("apps/sf_app/app.R")$value
testServer(app, {
  session$setInputs(date = "2026-03-31")
  stopifnot(output$kpi_arrears == "1.80%")                       # dashboard works
  session$setInputs(question = "What was the arrears ratio in September 2026?", ask = 1)
  stopifnot(log()[[1]]$r$status == "error")                      # assistant fails gracefully
})
