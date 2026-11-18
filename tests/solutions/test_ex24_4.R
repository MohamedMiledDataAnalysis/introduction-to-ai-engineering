# Exercise 24.4 - the Approve button, tested with both drafts
# Run from the repository root:  Rscript tests/solutions/test_ex24_4.R
library(shiny)
Sys.setenv(AIE_ROOT = getwd(), AIE_USER = "test.reviewer")
unlink("logs/commentary_approvals.csv")
for (d in c("2", "1")) {
  Sys.setenv(AIE_DRAFT = d)
  app <- suppressPackageStartupMessages(source("apps/solutions/ex24_4/app.R")$value)                   # the draft is chosen when the file is loaded
  testServer(app, {
    disabled <- grepl("disabled", as.character(output$approve_ui$html))
    cat("Draft", d, "| check_ok:", check_ok(), "| button disabled:", disabled, "\n")
    stopifnot(check_ok() == (d == "1"), disabled == (d == "2"))
    session$setInputs(approve = 1)                                       # click, even on a disabled button
  })
}
a <- read.csv("logs/commentary_approvals.csv")
print(a[, c("approver", "figures_checked")], row.names = FALSE)
stopifnot(nrow(a) == 1)                                                  # only draft 1 was recorded
Sys.unsetenv(c("AIE_DRAFT", "AIE_USER"))
cat("Exercise 24.4 test passed\n")
