# Chapter 7 - Chunk the prospectus, retrieve with BM25 and measure the hit rate on the evaluation set
source("aie_r/retrieval.R")
text   <- paste(readLines("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md", encoding = "UTF-8"), collapse = "\n")
chunks <- chunk_markdown(text, "LMF")
cat(length(chunks), "chunks:", paste(vapply(chunks, `[[`, "", "id"), collapse = ", "), "\n")

index <- bm25_index(chunks)
cases <- read.csv("evals/sf_prospectus_qa.csv", colClasses = "character")
cases <- cases[cases$source_section != "", ]

for (k in 1:3) {
  found_ok <- vapply(seq_len(nrow(cases)), function(i) {
    res <- bm25_search(index, cases$question[i], k)
    secs <- vapply(res, function(r) sub("\\..*", "", sub(".*#", "", r$chunk$id)), "")
    cases$source_section[i] %in% secs
  }, TRUE)
  cat(sprintf("hit rate at k=%d: %d/%d = %.0f%%   missed: %s\n", k, sum(found_ok), nrow(cases),
              100 * mean(found_ok), paste(cases$id[!found_ok], collapse = ", ")))
}
q <- cases$question[cases$id == "Q16"]
cat("\nQ16:", q, "\n")
for (r in bm25_search(index, q, 3)) cat(sprintf("  %6.3f  %-8s %s\n", r$score, r$chunk$id, r$chunk$title))
