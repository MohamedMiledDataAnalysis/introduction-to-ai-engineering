# Chapter 15 - Check three KID extractions against the document, the ISIN rule and the fund master data
source("aie_r/kid_extract.R")
funds <- read.csv("data/am/funds.csv", stringsAsFactors = FALSE)
candidates <- fromJSON("evals/candidates/kid_extractions.json",
                       simplifyVector = FALSE)
truth <- fromJSON("evals/kid_truth.json", simplifyVector = FALSE)
for (code in names(candidates)) {
  obj <- candidates[[code]]
  document <- paste(readLines(sprintf("data/am/documents/%s_kid.md",
    tolower(code)), encoding = "UTF-8"), collapse = "\n")
  problems <- check_extraction(obj, document,
                               funds[funds$fund_code == code, ])
  wrong <- names(obj)[!mapply(function(a, b) isTRUE(all.equal(a, b)),
                              obj, truth[[code]][names(obj)])]
  cat(sprintf("%s: %s   (fields actually wrong: %s)\n", code,
              if (length(problems)) "REJECTED" else "accepted",
              if (length(wrong)) paste(wrong, collapse = ", ") else "none"))
  for (p in problems) cat("   -", p, "\n")
}
