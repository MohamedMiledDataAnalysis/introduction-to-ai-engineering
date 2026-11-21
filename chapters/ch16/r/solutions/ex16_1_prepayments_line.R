# Exercise 16.1 - The prepayments line in each library
# Run from the root of the repository:  Rscript chapters/ch16/r/solutions/ex16_1_prepayments_line.R

source("aie_r/servicer_pdf.R")
lines <- strsplit(pdf_text_all(
  "data/sf/rmbs/servicer_reports/servicer_report_2026_09.pdf"), "\n")[[1]]
print(grep("Prepayments", lines, value = TRUE))
