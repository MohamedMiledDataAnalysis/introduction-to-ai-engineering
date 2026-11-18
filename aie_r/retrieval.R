# Split documents into chunks and retrieve the chunks most relevant to a question (BM25).
stop_words <- c("the", "of", "to", "and", "a", "in", "on", "is", "by", "for", "each", "or", "be", "are",
                "it", "its", "at", "as", "an", "any", "all", "this", "that", "with", "can", "how", "what",
                "which", "does", "do", "who", "when", "after", "much", "many")

tokens <- function(text) {
  w <- regmatches(tolower(text), gregexpr("[a-z0-9]+", tolower(text)))[[1]]
  w[!w %in% stop_words]
}

chunk_markdown <- function(text, doc_id, max_words = 180) {
  parts <- strsplit(paste0("\n", text), "\n## ", fixed = TRUE)[[1]][-1]
  chunks <- list()
  for (part in parts) {
    title <- trimws(sub("\n.*", "", part))
    body  <- trimws(sub("^[^\n]*\n", "", part))
    paras <- strsplit(body, "\n\\s*\n")[[1]]
    pieces <- list(); current <- character(0)
    for (p in paras) {
      if (length(current) && length(strsplit(paste(c(current, p), collapse = " "), "\\s+")[[1]]) > max_words) {
        pieces[[length(pieces) + 1]] <- paste(current, collapse = "\n\n"); current <- character(0)
      }
      current <- c(current, p)
    }
    if (length(current)) pieces[[length(pieces) + 1]] <- paste(current, collapse = "\n\n")
    num <- trimws(sub("\\..*", "", title))
    for (i in seq_along(pieces)) {
      cid <- paste0(doc_id, "#", num, if (length(pieces) > 1) paste0(".", i) else "")
      chunks[[length(chunks) + 1]] <- list(id = cid, title = title, text = paste0(title, "\n", pieces[[i]]))
    }
  }
  chunks
}

bm25_index <- function(chunks, k1 = 1.5, b = 0.75) {
  docs <- lapply(chunks, function(c) table(tokens(c$text)))
  lengths <- vapply(docs, sum, 0)
  vocab <- unique(unlist(lapply(docs, names)))
  n <- length(docs)
  df <- vapply(vocab, function(w) sum(vapply(docs, function(d) w %in% names(d), TRUE)), 0)
  list(chunks = chunks, docs = docs, lengths = lengths, avg = mean(lengths),
       idf = log(1 + (n - df + 0.5) / (df + 0.5)), k1 = k1, b = b)
}

bm25_score <- function(index, query, i) {
  d <- index$docs[[i]]; len <- index$lengths[i]; s <- 0
  for (w in tokens(query)) {
    if (w %in% names(d)) {
      tf <- as.numeric(d[[w]])
      s <- s + index$idf[[w]] * tf * (index$k1 + 1) /
        (tf + index$k1 * (1 - index$b + index$b * len / index$avg))
    }
  }
  s
}

bm25_search <- function(index, query, k = 3) {
  scores <- vapply(seq_along(index$docs), function(i) bm25_score(index, query, i), 0)
  ord <- order(-scores)[1:k]
  lapply(ord, function(i) list(chunk = index$chunks[[i]], score = round(scores[i], 3)))
}

cosine_sim <- function(u, v) sum(u * v) / (sqrt(sum(u^2)) * sqrt(sum(v^2)))

reciprocal_rank_fusion <- function(rankings, k = 60) {
  scores <- numeric(0)
  for (ranking in rankings) for (r in seq_along(ranking)) {
    id <- ranking[r]
    scores[id] <- (if (is.na(scores[id])) 0 else scores[id]) + 1 / (k + r)
  }
  names(sort(scores, decreasing = TRUE))
}

check_citations <- function(answer, retrieved) {
  source("aie_r/factcheck.R", local = TRUE)
  ids <- vapply(retrieved, `[[`, "", "id")
  cited <- regmatches(answer, gregexpr("\\[([A-Z][A-Za-z-]*#[0-9.]+)\\]", answer))[[1]]
  cited <- gsub("\\[|\\]", "", cited)
  problems <- character(0)
  if (!length(cited)) problems <- c(problems, "no citation")
  for (cid in cited) if (!cid %in% ids) problems <- c(problems, sprintf("cites %s, which was not provided", cid))
  cited_text <- paste(vapply(retrieved[ids %in% cited], `[[`, "", "text"), collapse = " ")
  src <- extract_figures(cited_text)
  src_keys <- if (nrow(src)) paste(src$unit, round(src$value * src$scale, 2)) else character(0)
  ans <- extract_figures(gsub("\\[[A-Z][A-Za-z-]*#[0-9.]+\\]", "", answer))
  for (i in seq_len(nrow(ans))) {
    key <- paste(ans$unit[i], round(ans$value[i] * ans$scale[i], 2))
    if (!key %in% src_keys) problems <- c(problems, sprintf("figure %s not found in the cited passages", ans$raw[i]))
  }
  problems
}
