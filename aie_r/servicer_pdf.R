# Read a servicer report PDF, extract its figures into a schema, and reconcile them with the loan data.
library(pdftools); library(jsonlite)
pdf_text_all <- function(path) paste(pdf_text(path), collapse = "\n")

independent_figures <- function(cutoff) {
  tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv"); cf <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_cashflows.csv")
  m <- tape[tape$RREL6 == cutoff, ]; c <- cf[cf$cutoff == cutoff, ]
  list(interest_collected_gbp = round(sum(c$interest), 2), scheduled_principal_gbp = round(sum(c$sched_principal), 2),
       prepayments_gbp = round(sum(c$prepayment), 2), recoveries_gbp = round(sum(c$recovery), 2),
       loans_outstanding = sum(m$RREL30 > 0), pool_balance_gbp = round(sum(m$RREL30), 2),
       new_defaults_gbp = round(sum(c$new_default), 2))
}

figure_in_text <- function(value, text, field) {
  written <- if (field == "loans_outstanding") formatC(value, format = "d", big.mark = ",")
             else formatC(value, format = "f", digits = 2, big.mark = ",")
  grepl(written, text, fixed = TRUE)
}

reconcile_report <- function(extracted, text, cutoff, tolerance = 0.01) {
  ind <- independent_figures(cutoff)
  do.call(rbind, lapply(names(ind), function(field) {
    got <- extracted[[field]]; diff <- round(got - ind[[field]], 2)
    in_report <- got == 0 || figure_in_text(got, text, field)
    verdict <- if (!in_report) "extraction error: value not in the report" else
               if (abs(diff) <= tolerance) "agrees" else "REPORT DISAGREES WITH LOAN DATA"
    data.frame(field = field, extracted = got, loan_data = ind[[field]], difference = diff, verdict = verdict)
  }))
}
