# Chapter 7 - Hybrid retrieval: BM25 + embeddings, fused by reciprocal rank (needs: ollama pull nomic-embed-text)
source("aie_r/llm.R"); source("aie_r/retrieval.R")
text   <- paste(readLines("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md", encoding = "UTF-8"), collapse = "\n")
chunks <- chunk_markdown(text, "LMF")
ids    <- vapply(chunks, `[[`, "", "id")
index  <- bm25_index(chunks)
vectors <- embed(vapply(chunks, `[[`, "", "text"))

cases <- read.csv("evals/sf_prospectus_qa.csv", colClasses = "character")
cases <- cases[cases$source_section != "", ]
q_vectors <- embed(cases$question)
section_of <- function(id) sub("\\..*", "", sub(".*#", "", id))

for (k in 1:3) {
  hits <- c(bm25 = 0, embeddings = 0, hybrid = 0)
  for (i in seq_len(nrow(cases))) {
    bm <- vapply(bm25_search(index, cases$question[i], length(chunks)), function(r) r$chunk$id, "")
    em <- ids[order(-vapply(vectors, function(v) cosine_sim(q_vectors[[i]], v), 0))]
    hy <- reciprocal_rank_fusion(list(bm, em))
    for (nm in names(hits)) {
      ranking <- switch(nm, bm25 = bm, embeddings = em, hybrid = hy)
      hits[nm] <- hits[nm] + (cases$source_section[i] %in% section_of(ranking[1:k]))
    }
  }
  cat(sprintf("k=%d: bm25 %d/%d  embeddings %d/%d  hybrid %d/%d\n", k, hits[1], nrow(cases),
              hits[2], nrow(cases), hits[3], nrow(cases)))
}
