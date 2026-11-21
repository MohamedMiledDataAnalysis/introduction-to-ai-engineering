# Exercise 7.1 - One index for three KIDs
# Run from the root of the repository:  Rscript chapters/ch07/r/solutions/ex7_1_three_kids.R

source("aie_r/retrieval.R")
chunks <- list()
for (code in c("hgef", "hecb", "hbma")) {
  text <- paste(readLines(sprintf("data/am/documents/%s_kid.md", code),
                          encoding = "UTF-8"), collapse = "\n")
  chunks <- c(chunks, chunk_markdown(text, toupper(code)))
}
index <- bm25_index(chunks)
for (h in bm25_search(index, "What are the ongoing costs of the euro corporate bond fund?", 3))
  cat(h$score, h$chunk$id, "\n")
