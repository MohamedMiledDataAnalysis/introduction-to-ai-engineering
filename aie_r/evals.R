# Score answers against an evaluation set and compare runs.
refusal_pattern <- paste0("do(es)? not (state|mention|contain|name|say|give|include|specify)|",
                          "not (stated|mentioned|given) in|not in the (document|text)|no information|covers .{3,60} only|",
                          "cannot give investment advice|no data for|data (is available|ends)")

numbers_in <- function(text) {
  n <- regmatches(text, gregexpr("-?\\d[\\d,]*\\.?\\d*", text, perl = TRUE))[[1]]
  as.numeric(gsub(",", "", n))
}

score_one <- function(case, answer) {
  answer <- gsub("\\[[A-Z][A-Za-z-]*#[0-9.]+\\]", "", answer)   # citations are not part of the answer's content
  kind <- case$answer_type
  if (kind == "number") {
    found <- numbers_in(answer)
    ok <- any(abs(found - as.numeric(case$expected)) <= as.numeric(case$tolerance))
    return(list(ok, if (ok) "number found" else
      sprintf("expected %s, found [%s]", case$expected, paste(found, collapse = ", "))))
  }
  if (kind == "text") {
    options <- tolower(trimws(strsplit(case$keywords, "|", fixed = TRUE)[[1]]))
    # whole words only: the keyword "no" must not match inside "notes" or "not"
    esc <- function(k) gsub("([][{}()+*^$|\\\\.?])", "\\\\\\1", k)
    ok <- any(vapply(options, function(k)
      grepl(paste0("(?<![a-z])", esc(k), "(?![a-z])"), tolower(answer), perl = TRUE), TRUE))
    return(list(ok, if (ok) "keyword found" else paste("none of", paste(options, collapse = ", "))))
  }
  if (kind == "ordered") {
    rest <- answer
    for (label in trimws(strsplit(case$expected, ",")[[1]])) {
      m <- regexpr(paste0("\\b(Class )?", label, "\\b"), rest, perl = TRUE)
      if (m == -1) return(list(FALSE, sprintf("'%s' missing or out of order", label)))
      rest <- substring(rest, m + attr(m, "match.length"))
    }
    return(list(TRUE, "order correct"))
  }
  if (kind == "not_in_document") {
    ok <- grepl(refusal_pattern, answer, ignore.case = TRUE)
    return(list(ok, if (ok) "declined correctly" else "answered instead of declining"))
  }
  stop("unknown answer_type ", kind)
}

run_eval <- function(cases, answers) {
  res <- lapply(seq_len(nrow(cases)), function(i) {
    case <- cases[i, ]
    ans <- if (is.null(answers[[case$id]])) "" else answers[[case$id]]
    s <- score_one(case, ans)
    data.frame(id = case$id, answer_type = case$answer_type, passed = s[[1]], reason = s[[2]])
  })
  do.call(rbind, res)
}

compare_runs <- function(before, after) {
  m <- merge(before, after, by = "id", suffixes = c("_before", "_after"))
  list(regressions = m$id[m$passed_before & !m$passed_after],
       fixes = m$id[!m$passed_before & m$passed_after])
}

wilson_interval <- function(passed, total, z = 1.96) {
  if (total == 0) return(c(0, 1))
  p <- passed / total
  denom <- 1 + z^2 / total
  centre <- (p + z^2 / (2 * total)) / denom
  half <- z * sqrt(p * (1 - p) / total + z^2 / (4 * total^2)) / denom
  c(max(0, centre - half), min(1, centre + half))
}
