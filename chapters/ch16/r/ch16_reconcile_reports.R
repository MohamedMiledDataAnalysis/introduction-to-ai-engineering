# Chapter 16 - Reconcile extracted servicer report figures with the report text and with the loan data
source("aie_r/servicer_pdf.R")
options(width = 120, scipen = 20)
extractions <- fromJSON("evals/candidates/servicer_report_extractions.json", simplifyVector = FALSE)
for (cutoff in names(extractions)) {
  ex <- extractions[[cutoff]]
  text <- pdf_text_all(sprintf("data/sf/rmbs/servicer_reports/servicer_report_%s.pdf", gsub("-", "_", substr(cutoff, 1, 7))))
  cat("\n", ex$collection_period, "\n", sep = "")
  print(reconcile_report(ex, text, cutoff), row.names = FALSE)
}
