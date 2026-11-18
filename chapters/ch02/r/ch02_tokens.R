# Chapter 2 - How much text fits in a model's context window?
prospectus <- paste(readLines("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
                              encoding = "UTF-8"), collapse = "\n")
tape      <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
one_month <- tape[tape$RREL6 == "2026-09-30", ]
tmp <- tempfile(fileext = ".csv")
write.csv(one_month, tmp, row.names = FALSE, na = "", quote = FALSE)
csv_text <- paste(readLines(tmp), collapse = "\n")

chars_per_token <- 4       # budgeting rule for English text; measure the real figure with your model
context_window  <- 32000   # tokens; check the figure for your model and settings

for (item in list(list("Prospectus excerpt", prospectus), list("Loan tape, one month", csv_text))) {
  n   <- nchar(item[[2]])
  est <- n / chars_per_token
  cat(sprintf("%-22s %10s characters  ~%9s tokens  %6.1f x the window\n", item[[1]],
              format(n, big.mark = ","), format(round(est), big.mark = ","), est / context_window))
}
per_row <- nchar(csv_text) / nrow(one_month) / chars_per_token
cat(sprintf("\nOne loan row: ~%.0f tokens; rows that fit in the window: ~%s\n",
            per_row, format(round(context_window / per_row), big.mark = ",")))
