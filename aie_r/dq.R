# Data-quality rules for a received loan tape. Each rule returns the rows that break it.
dq_rules <- list(
  negative_balance = list("Current balance (RREL30) is negative", function(t, d) t$RREL30 < 0),
  balance_above_original = list("Current balance exceeds the original balance by more than 10% on a repayment loan",
                                function(t, d) t$RREL35 == "FRXX" & t$RREL30 > 1.10 * t$RREL29),
  maturity_before_origination = list("Maturity date (RREL24) is before the origination date (RREL23)",
                                     function(t, d) as.Date(t$RREL24) <= as.Date(t$RREL23)),
  default_without_180_days = list("Status DFLT with fewer than 180 days in arrears (prospectus: six payments)",
                                  function(t, d) t$RREL69 == "DFLT" & t$RREL68 < 180),
  arrears_without_balance = list("Status ARRE with no arrears balance (RREL67)",
                                 function(t, d) t$RREL69 == "ARRE" & ifelse(is.na(t$RREL67), 0, t$RREL67) <= 0),
  ltv_implausible = list("Current LTV (RREC12) above 150%", function(t, d) t$RREC12 > 150),
  rate_out_of_range = list("Current interest rate (RREL43) outside 0% to 15%", function(t, d) t$RREL43 < 0 | t$RREL43 > 15),
  missing_region = list("Geographic region (RREL11) is missing", function(t, d) is.na(t$RREL11) | t$RREL11 == ""),
  performing_with_days_in_arrears = list("Status PERF or RNAR with days in arrears (RREL68) above 0",
                                         function(t, d) t$RREL69 %in% c("PERF", "RNAR") & t$RREL68 > 0),
  original_ltv_above_95 = list("Original LTV (RREC16) above the 95% eligibility limit", function(t, d) t$RREC16 > 95),
  wrong_cutoff_date = list("Data cut-off date (RREL6) differs from the reporting date", function(t, d) t$RREL6 != d),
  duplicate_loan = list("Loan identifier (RREL2) appears more than once",
                        function(t, d) duplicated(t$RREL2) | duplicated(t$RREL2, fromLast = TRUE))
)

run_rules <- function(tape, cutoff_date) {
  out <- list()
  for (rule in names(dq_rules)) {
    mask <- dq_rules[[rule]][[2]](tape, cutoff_date)
    mask[is.na(mask)] <- FALSE
    for (loan in unique(tape$RREL2[mask]))
      out[[length(out) + 1]] <- data.frame(loan_id = loan, rule = rule, description = dq_rules[[rule]][[1]])
  }
  if (length(out)) do.call(rbind, out) else data.frame(loan_id = character(0), rule = character(0), description = character(0))
}
