# Chapter 7 - Check that answers cite the passages they were given, and that their figures are in them
source("aie_r/retrieval.R")
text  <- paste(readLines(
  "data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
  encoding = "UTF-8"), collapse = "\n")
index <- bm25_index(chunk_markdown(text, "LMF"))
retrieved <- lapply(bm25_search(index,
  "What is the Reserve Fund Required Amount?", 3), `[[`, "chunk")
cat("Retrieved:",
    paste(vapply(retrieved, `[[`, "", "id"), collapse = ", "), "\n")

answers <- list(
  "A grounded"     = "The Reserve Fund Required Amount is £6,082,667.80, equal to 1.50% of the pool [LMF#3].",
  "B no citation"  = "The Reserve Fund Required Amount is £6,082,667.80.",
  "C wrong figure" = "The Reserve Fund Required Amount is £6,028,667.80 [LMF#3].",
  "D cites unseen" = "The reserve fund is replenished at item (l) [LMF#6.3]."
)
for (name in names(answers)) {
  p <- check_citations(answers[[name]], retrieved)
  cat(sprintf("%-16s %s\n", name,
              if (length(p) == 0) "grounded" else paste(p, collapse = "; ")))
}
