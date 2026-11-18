# Check every figure written in a text against a table of facts computed by code.
scale_of <- c("1" = 1, k = 1e3, thousand = 1e3, m = 1e6, mn = 1e6, million = 1e6, bn = 1e9, billion = 1e9)
figure_re <- paste0("([\u00a3\u20ac$])?\\s?(\\d{1,3}(?:,\\d{3})+(?:\\.\\d+)?|\\d+(?:\\.\\d+)?)",
                    "\\s?(?:(%|per cent|bps?\\b|basis points)|(million|billion|thousand|bn|mn|m|k)\\b)?")

extract_figures <- function(text) {
  m <- gregexpr(figure_re, text, perl = TRUE, ignore.case = TRUE)[[1]]
  empty <- data.frame(raw = character(0), value = numeric(0), decimals = integer(0), unit = character(0), scale = numeric(0))
  if (m[1] == -1) return(empty)
  starts <- attr(m, "capture.start"); lens <- attr(m, "capture.length")
  out <- list()
  for (i in seq_along(m)) {
    cap <- function(j) substr(text, starts[i, j], starts[i, j] + lens[i, j] - 1)
    cur <- cap(1); num <- cap(2); pct <- tolower(cap(3)); sc <- tolower(cap(4))
    before <- substr(text, max(1, m[i] - 12), m[i] - 1)
    after  <- substr(text, m[i] + attr(m, "match.length")[i], m[i] + attr(m, "match.length")[i])
    if (grepl("^(19|20)\\d{2}$", num) && cur == "" && pct == "") next
    if (grepl("(Class|item|section|LMF25-|\\()\\s?$", before, ignore.case = TRUE, perl = TRUE)) next
    if (grepl("\\d[-/]$", before) || after %in% c("-", "/")) next
    month <- "(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\\b"
    rest <- substr(text, m[i] + attr(m, "match.length")[i], m[i] + attr(m, "match.length")[i] + 12)
    if (cur == "" && pct == "" && (grepl(paste0("^\\s?", month), rest, ignore.case = TRUE, perl = TRUE) ||
                                   grepl(paste0(month, "\\s?$"), before, ignore.case = TRUE, perl = TRUE))) next
    unit <- if (pct %in% c("%", "per cent")) "percent" else if (pct != "") "bp" else if (cur != "") "money" else "number"
    if (unit == "number" && grepl("^[0-9]", after)) next
    scale <- if (unit %in% c("money", "number")) scale_of[[if (sc == "") "1" else sc]] else 1
    decimals <- if (grepl("\\.", num)) nchar(sub(".*\\.", "", num)) else 0
    out[[length(out) + 1]] <- data.frame(raw = trimws(substr(text, m[i], m[i] + attr(m, "match.length")[i] - 1)), value = as.numeric(gsub(",", "", num)),
                                         decimals = decimals, unit = unit, scale = scale)
  }
  if (length(out) == 0) return(empty)
  do.call(rbind, out)
}

figure_matches <- function(fig, fact_value, fact_unit) {
  if (fact_unit == "percent" && fig$unit == "bp") candidate <- abs(fact_value) * 100
  else if (fact_unit != fig$unit) return(FALSE)
  else candidate <- abs(fact_value) / fig$scale
  round(candidate, fig$decimals) == round(fig$value, fig$decimals)
}

check_text <- function(text, facts) {
  figs <- extract_figures(text)
  lapply(seq_len(nrow(figs)), function(i) {
    f <- figs[i, ]
    hits <- names(facts)[vapply(facts, function(x) figure_matches(f, x$value, x$unit), TRUE)]
    list(figure = f, hits = hits)
  })
}

forbidden_patterns <- c("\\bguarantee[ds]?\\b", "\\brisk[- ]free\\b", "\\bwill (outperform|rise|increase)\\b",
                        "\\bcertain(ly)? to\\b", "\\bno risk\\b", "\\byou should (buy|sell|invest)\\b")
forbidden_phrases <- function(text) {
  unlist(lapply(forbidden_patterns, function(p)
    regmatches(text, gregexpr(p, text, ignore.case = TRUE, perl = TRUE))[[1]]))
}
