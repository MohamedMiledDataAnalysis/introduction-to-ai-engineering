# Exercise 22.3 - The past-performance warning as a check, broad and narrow
# Run from the root of the repository:  Rscript chapters/ch22/r/solutions/ex22_3_missing_warning.R
suppressPackageStartupMessages(source("aie_r/agent.R"))

missing_warning <- function(answer) {
  # the book's check: a percentage, a performance word, and no warning
  figs <- extract_figures(answer)
  any(figs$unit == "percent") &&
    grepl("\\b(return(ed)?|performance|gained|lost)\\b", answer, ignore.case = TRUE, perl = TRUE) &&
    !grepl("past performance (does not|is not a reliable)", answer, ignore.case = TRUE)
}

missing_warning_narrow <- function(answer, results) {
  # the trade-off of the book: fire only if the answer quotes a return that a fund_performance call returned
  f <- facts_from_results(results)
  returns <- f[endsWith(names(f), "return_pct")]
  quotes_a_return <- any(vapply(check_text(answer, returns), function(r) length(r$hits) > 0, TRUE))
  quotes_a_return && !grepl("past performance (does not|is not a reliable)", answer, ignore.case = TRUE)
}

apply_warning_check <- function(result, domain = "am") {
  # what ask_assistant() does after the forbidden-phrase check (the book's integration)
  if (domain == "am" && missing_warning(result$answer)) {
    result$status <- "needs_review"
    result$unsupported <- c(result$unsupported, "past performance warning missing")
  }
  result
}

# 1. The four sentences of the book
book <- c("HGEF returned 6.46% over one year to 30 September 2026.",
          "HGEF returned 6.46% over one year to 30 September 2026. Past performance does not predict future returns.",
          "HECB's ongoing costs are 0.40%.",
          "Ongoing costs of 0.40% reduce the return each year.")
cat("The four sentences of the book:\n")
for (s in book) cat(sprintf("  %-6s %s\n", if (missing_warning(s)) "True" else "False", s))

# 2. A larger set of answers, each labelled with the right decision, and the trace the agent would have
as_result <- function(code) list(name = "fund_performance",
  result = as.character(toJSON(fund_performance(code, 12), auto_unbox = TRUE, digits = NA)))
perf <- list(as_result("HGEF"), as_result("HECB"))
labelled <- data.frame(stringsAsFactors = FALSE,
  answer = c("HGEF returned 6.46% over one year, against 7.86% for its benchmark.",
             "HGEF returned 6.46% over one year. Past performance is not a reliable indicator of future results.",
             "HGEF trailed its benchmark by 1.40% over one year.",
             "HECB's ongoing costs are 0.40%.",
             "Ongoing costs of 0.40% reduce the return each year.",
             "The fund's largest holding is 4.2% of the portfolio.",
             "HGEF's performance fee is 0%; there is none.",
             "Information technology is 16.08% of HGEF, against 17.34% for the benchmark."),
  required = c(TRUE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE))
labelled$broad <- vapply(labelled$answer, missing_warning, TRUE)
labelled$narrow <- vapply(labelled$answer, missing_warning_narrow, TRUE, results = perf)
cat("\nBroad and narrow check on labelled answers:\n")
for (i in seq_len(nrow(labelled)))
  cat(sprintf("  required %-5s broad %-5s narrow %-5s %s\n", labelled$required[i], labelled$broad[i],
              labelled$narrow[i], substr(labelled$answer[i], 1, 70)))
cat(sprintf("Wrong decisions: broad %d of %d, narrow %d of %d\n", sum(labelled$broad != labelled$required),
            nrow(labelled), sum(labelled$narrow != labelled$required), nrow(labelled)))

# 3. The integration: an agent result before and after the check
r <- apply_warning_check(list(answer = book[1], status = "verified", unsupported = character(0)))
cat("\nAfter the check:", r$status, r$unsupported, "\n")
