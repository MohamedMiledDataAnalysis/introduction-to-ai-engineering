# Exercise 24.4 - The Approve button, tested in its minimum form
# Run from the root of the repository:  Rscript chapters/ch24/r/solutions/ex24_4_minimum.R

library(shiny)
Sys.setenv(AIE_ROOT = getwd())
app <- source("apps/solutions/ex24_4/app.R")$value

testServer(app, cat(check_ok(), grepl("disabled", as.character(output$approve_ui$html)), "\n"))
