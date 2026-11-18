# Chapter 2 - A tiny next-word model built from the Larkfield prospectus
text  <- tolower(paste(readLines(
  "data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
  encoding = "UTF-8"), collapse = " "))
words <- regmatches(text, gregexpr("[a-z]+", text))[[1]]
cat("Words in the prospectus excerpt:", length(words), "\n")

# Count which word follows which (bigram counts)
pairs   <- data.frame(w1 = head(words, -1), w2 = tail(words, -1))
context <- "class"
counts  <- sort(table(pairs$w2[pairs$w1 == context]), decreasing = TRUE)
total   <- sum(counts)
cat(sprintf("\nWords that follow '%s' (%d occurrences):\n", context, total))
for (i in 1:4) {
  cat(sprintf("  %-10s %3d   p = %.3f\n", names(counts)[i], counts[i],
              counts[i] / total))
}

# Temperature: divide the log-probabilities by T, then renormalise
with_temperature <- function(p, t) {
  logits <- log(p) / t
  e <- exp(logits - max(logits))
  e / sum(e)
}
probs <- as.numeric(counts) / total
names(probs) <- names(counts)
temps <- c(0.5, 1.0, 2.0)
tab <- sapply(temps, function(t) with_temperature(probs, t))
cat("\nProbability of the four most likely words at three temperatures:\n")
cat(sprintf("  %-10s%-10s%-10s%-10s\n", "word", "T=0.5", "T=1", "T=2"))
for (w in names(probs)[1:4]) {
  cat(sprintf("  %-10s%-10.3f%-10.3f%-10.3f\n", w, tab[w, 1], tab[w, 2],
              tab[w, 3]))
}
