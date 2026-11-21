# The Larkfield prospectus assistant: retrieve, answer with citations, check grounding.
source("aie_r/llm.R"); source("aie_r/prompts.R"); source("aie_r/retrieval.R")
refusal_text <- "The passages provided do not state this."
qa_keywords <- c("LMF#2" = "Keywords: margin, coupon, spread, interest rate")

build_index <- function(path = "data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md") {
  chunks <- chunk_markdown(paste(readLines(path, encoding = "UTF-8"), collapse = "\n"), "LMF")
  for (i in seq_along(chunks)) if (chunks[[i]]$id %in% names(qa_keywords))
    chunks[[i]]$text <- paste0(chunks[[i]]$text, "\n", qa_keywords[[chunks[[i]]$id]])
  bm25_index(chunks)
}

answer_llm <- function(question, index, k = 3) {
  retrieved <- lapply(bm25_search(index, question, k), `[[`, "chunk")
  p <- load_prompt("answer_with_citations_v1")
  passages <- paste(vapply(retrieved, function(c)
    paste0("[", c$id, "]\n", c$text), ""), collapse = "\n\n")
  text <- trimws(chat(list(list(role = "user", content = render(
    p$text, passages = passages, question = question))))$text)
  problems <- if (startsWith(text, refusal_text)) character(0)
              else check_citations(text, retrieved)
  list(answer = text, retrieved = vapply(retrieved, `[[`, "", "id"),
       problems = problems, prompt = p$hash)
}

answer_extractive <- function(question, index, min_score = 4) {
  top <- bm25_search(index, question, 1)[[1]]
  if (top$score < min_score) return(list(answer = refusal_text, retrieved = top$chunk$id, problems = character(0)))
  q <- unique(tokens(question))
  pieces <- trimws(unlist(strsplit(top$chunk$text, "(?<=[.;])\\s+|\n", perl = TRUE)))
  pieces <- pieces[pieces != ""]
  overlap <- vapply(pieces, function(p) length(intersect(q, unique(tokens(p)))), 0)
  list(answer = paste0(pieces[which.max(overlap)], " [", top$chunk$id, "]"), retrieved = top$chunk$id,
       problems = character(0))
}
