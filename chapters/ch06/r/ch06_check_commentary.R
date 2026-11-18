# Chapter 6 - Check every figure in two draft commentaries against facts computed from the data
source("aie_r/factcheck.R")
cut   <- "2026-09-30"
tape  <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
wf    <- read.csv("data/sf/rmbs/larkfield_2025_1_waterfall.csv")
notes <- read.csv("data/sf/rmbs/larkfield_2025_1_notes.csv")

sep  <- tape[tape$RREL6 == cut, ]
w    <- setNames(wf$paid[wf$cutoff == cut], wf$item[wf$cutoff == cut])
n    <- notes[notes$cutoff == cut, ]
pool <- sum(sep$RREL30)
fact <- function(value, unit) list(value = value, unit = unit)
facts <- list(
  "revenue receipts"   = fact(w[["Available revenue receipts"]], "money"),
  "principal receipts" = fact(w[["Available principal receipts"]], "money"),
  "Class A principal paid"  = fact(n$principal_paid[n$cls == "A"], "money"),
  "Class A closing balance" = fact(n$closing[n$cls == "A"], "money"),
  "pool balance"  = fact(pool, "money"),
  "arrears ratio" = fact(100 * sum(sep$RREL30[sep$RREL69 == "ARRE"]) / pool,
                         "percent"),
  "reserve fund balance" = fact(w[["Reserve fund closing balance"]], "money"),
  "excess spread"        = fact(w[["Excess spread released"]], "money")
)

text   <- paste(readLines("evals/drafts/larkfield_commentary_2026_09.txt",
                          encoding = "UTF-8"), collapse = "\n")
drafts <- strsplit(trimws(text), "\n\\s*\n")[[1]]
for (d in drafts) {
  title <- sub("\n.*", "", d); body <- sub("^[^\n]*\n", "", d)
  cat(title, "\n")
  for (r in check_text(body, facts)) {
    cat(sprintf("  %-18s %s\n", r$figure$raw,
      if (length(r$hits)) paste("OK  ", paste(r$hits, collapse = ", "))
      else "NOT SUPPORTED"))
  }
  bad <- forbidden_phrases(body)
  cat("  Forbidden phrases:",
      if (length(bad)) paste(bad, collapse = ", ") else "none", "\n\n")
}
