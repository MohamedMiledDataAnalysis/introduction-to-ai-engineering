# Extract KID data into a schema, one document per call, and check every value three ways.
source("aie_r/validate.R")
kid_schema <- fromJSON("prompts/kid_schema.json", simplifyVector = FALSE)
doc_format <- list(management_costs_pct = function(v) sprintf("%.2f%%", v), transaction_costs_pct = function(v) sprintf("%.2f%%", v),
                   summary_risk_indicator = function(v) paste(v, "on a scale"),
                   recommended_holding_period_years = function(v) paste(v, "years"),
                   moderate_scenario_rhp_eur = function(v) paste("EUR", formatC(v, format = "d", big.mark = ",")),
                   entry_costs_eur = function(v) paste("EUR", formatC(v, format = "d", big.mark = ",")),
                   isin = function(v) v)

isin_valid <- function(code) {
  chars <- strsplit(substr(code, 1, 11), "")[[1]]
  digits <- paste(vapply(chars, function(ch) as.character(strtoi(ch, 36L)), ""), collapse = "")
  d <- rev(as.integer(strsplit(digits, "")[[1]]))
  dbl <- ifelse(seq_along(d) %% 2 == 1, ifelse(2 * d > 9, 2 * d - 9, 2 * d), d)
  (10 - sum(dbl) %% 10) %% 10 == as.integer(substr(code, 12, 12))
}

check_extraction <- function(obj, document, fund_row) {
  problems <- paste("schema:", validate(obj, kid_schema))
  if (length(problems) == 1 && problems == "schema: ") problems <- character(0)
  for (field in names(doc_format)) {
    v <- obj[[field]]
    if (!is.null(v) && !grepl(doc_format[[field]](v), document, fixed = TRUE))
      problems <- c(problems, sprintf("%s = %s not found in the document as '%s'", field, v, doc_format[[field]](v)))
  }
  if (!is.null(obj$isin) && !isin_valid(obj$isin)) problems <- c(problems, "isin check digit is wrong")
  if (!identical(as.integer(obj$summary_risk_indicator), as.integer(fund_row$sri)))
    problems <- c(problems, sprintf("risk indicator %s differs from the fund master (%s)", obj$summary_risk_indicator, fund_row$sri))
  if (!is.null(obj$management_costs_pct) && round(obj$management_costs_pct / 100, 6) != round(fund_row$ocf, 6))
    problems <- c(problems, sprintf("management costs %s%% differ from the fund master's ongoing charges (%.2f%%)", obj$management_costs_pct, 100 * fund_row$ocf))
  problems
}
