# Chapter 2 - Which section of the prospectus is closest to a question?
# Bag-of-words vectors weighted by TF-IDF, compared with cosine similarity.
text     <- paste(readLines("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
                            encoding = "UTF-8"), collapse = "\n")
sections <- strsplit(text, "\n## ", fixed = TRUE)[[1]][-1]
titles   <- sub("\n.*", "", sections)

stop_words <- c("the", "of", "to", "and", "a", "in", "on", "is", "by", "for", "each", "or",
                "be", "are", "it", "its", "at", "as", "an", "any", "all", "this", "that",
                "with", "can", "how")
tokens <- function(s) {
  w <- regmatches(tolower(s), gregexpr("[a-z]+", tolower(s)))[[1]]
  w[!w %in% stop_words]
}

docs  <- lapply(sections, function(s) table(tokens(s)))
n     <- length(docs)
vocab <- unique(unlist(lapply(docs, names)))
df    <- sapply(vocab, function(w) sum(sapply(docs, function(d) w %in% names(d))))
idf   <- log(n / df) + 1

vec <- function(counts) {
  v <- as.numeric(counts) * idf[names(counts)]
  v[is.na(v)] <- 0
  names(v) <- names(counts)
  v
}
cosine <- function(u, v) {
  common <- intersect(names(u), names(v))
  dot <- sum(u[common] * v[common])
  if (dot == 0) return(0)
  dot / (sqrt(sum(u^2)) * sqrt(sum(v^2)))
}

question <- "How can the reserve fund be used?"
q <- vec(table(tokens(question)))
scores <- sapply(docs, function(d) cosine(q, vec(d)))
ord <- order(scores, decreasing = TRUE)[1:3]
cat("Question:", question, "\n")
for (i in ord) cat(sprintf("  %.3f  %s\n", scores[i], titles[i]))
