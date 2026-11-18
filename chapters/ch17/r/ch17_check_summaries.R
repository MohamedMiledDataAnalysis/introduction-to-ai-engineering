# Chapter 17 - Check summaries of research notes: faithful, consistent, complete, short
source("aie_r/summary_check.R"); library(jsonlite)
key_facts <- fromJSON("data/am/research/key_facts.json",
                      simplifyVector = FALSE)
summaries <- fromJSON("evals/candidates/research_summaries.json",
                      simplifyVector = FALSE)
for (nid in names(summaries)) {
  note <- paste(readLines(sprintf("data/am/research/%s.md", nid),
                          encoding = "UTF-8"), collapse = "\n")
  for (label in names(summaries[[nid]])) {
    p <- check_summary(summaries[[nid]][[label]], note, key_facts[[nid]])
    cat(sprintf("%s summary %s: %s\n", nid, label,
                if (length(p)) "REJECTED" else "accepted"))
    for (x in p) cat("    -", x, "\n")
  }
}
