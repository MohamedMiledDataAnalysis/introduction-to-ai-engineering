# Check a summary of a research note: faithful (nothing new), complete (key facts present), consistent, short.
source("aie_r/factcheck.R")
check_summary <- function(summary, note, key, max_words = 60) {
  problems <- character(0)
  nf <- extract_figures(note); note_values <- paste(nf$unit, round(nf$value * nf$scale, 4))
  sf <- extract_figures(summary)
  for (i in seq_len(nrow(sf)))
    if (!paste(sf$unit[i], round(sf$value[i] * sf$scale[i], 4)) %in% note_values)
      problems <- c(problems, sprintf("figure %s is not in the note", sf$raw[i]))
  said <- c("buy", "hold", "sell")[vapply(c("buy", "hold", "sell"), function(r)
    grepl(paste0("\\b", r, "\\b"), summary, ignore.case = TRUE, perl = TRUE), TRUE)]
  if (length(said) && !identical(said, tolower(key$recommendation)))
    problems <- c(problems, sprintf("recommendation [%s] differs from the note (%s)", paste(said, collapse = ", "), key$recommendation))
  risk_words <- strsplit(tolower(key$main_risk), " ")[[1]]; risk_words <- risk_words[nchar(risk_words) > 3]
  required <- c("recommendation" = grepl(tolower(key$recommendation), tolower(summary), fixed = TRUE),
                "target price" = grepl(sprintf("%.2f", key$target_price_eur), summary, fixed = TRUE),
                "revenue growth" = grepl(sprintf("%.1f%%", key$revenue_growth_pct), summary, fixed = TRUE),
                "main risk" = sum(vapply(risk_words, grepl, TRUE, tolower(summary), fixed = TRUE)) >= 2)
  if (any(!required)) problems <- c(problems, paste("missing:", names(required)[!required]))
  n_words <- length(strsplit(trimws(summary), "\\s+")[[1]])
  if (n_words > max_words) problems <- c(problems, sprintf("%d words, limit %d", n_words, max_words))
  problems
}
