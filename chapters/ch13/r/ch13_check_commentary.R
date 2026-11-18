# Chapter 13 - Build the facts of the HGEF commentary and check two drafts: value, label and direction
source("aie_r/commentary.R")
hf <- hgef_facts(); attr <- hf$attr[order(hf$attr$total), ]
cat("Largest detractors (bp):", paste(sprintf("%s %.1f", head(attr$sector, 3), 10000 * head(attr$total, 3)), collapse = "; "), "\n")
text <- paste(readLines("evals/drafts/hgef_commentary_2026_09.txt", encoding = "UTF-8"), collapse = "\n")
for (d in strsplit(trimws(text), "\n\\s*\n")[[1]]) {
  cat("\n", sub("\n.*", "", d), "\n", sep = "")
  for (r in check_commentary(sub("^[^\n]*\n", "", d), hf$facts))
    cat(sprintf("  %-7s %s\n", r$raw, if (is.na(r$problem)) paste("OK ", paste(r$hits, collapse = ", ")) else paste("PROBLEM:", r$problem)))
}
