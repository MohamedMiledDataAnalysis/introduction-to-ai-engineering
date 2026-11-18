# The monthly Larkfield investor report: tables computed by code, a commentary drafted by the model.
month_figures <- function(cutoff) {
  tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv", stringsAsFactors = FALSE)
  cf <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_cashflows.csv")
  notes <- read.csv("data/sf/rmbs/larkfield_2025_1_notes.csv"); wf <- read.csv("data/sf/rmbs/larkfield_2025_1_waterfall.csv")
  dates <- sort(unique(tape$RREL6)); prev <- dates[which(dates == cutoff) - 1]
  m <- tape[tape$RREL6 == cutoff, ]; p <- tape[tape$RREL6 == prev, ]; c <- cf[cf$cutoff == cutoff, ]
  pool <- sum(m$RREL30); prev_pool <- sum(p$RREL30)
  arr <- m[m$RREL69 == "ARRE", ]; months <- pmin(arr$RREL68 %/% 30, 4)
  smm <- sum(c$prepayment) / (prev_pool - sum(c$sched_principal))
  w <- wf[wf$cutoff == cutoff, ]; s <- setNames(w$paid[w$waterfall == "Summary"], w$item[w$waterfall == "Summary"])
  n <- notes[notes$cutoff == cutoff, ]; rownames(n) <- n$cls
  list(cutoff = cutoff, previous = prev, pool = pool, prev_pool = prev_pool, loans = sum(m$RREL30 > 0),
       arrears_ratio = 100 * sum(arr$RREL30) / pool,
       prev_arrears_ratio = 100 * sum(p$RREL30[p$RREL69 == "ARRE"]) / prev_pool,
       buckets = data.frame(bucket = c("1 month", "2 months", "3 months", "4-5 months"),
                            loans = sapply(1:4, function(k) sum(months == k)),
                            balance = sapply(1:4, function(k) sum(arr$RREL30[months == k]))),
       cpr = 100 * (1 - (1 - smm)^12), revenue = s[["Available revenue receipts"]],
       principal = s[["Available principal receipts"]], new_defaults = s[["New defaults debited to PDL"]],
       reserve = s[["Reserve fund closing balance"]], excess_spread = s[["Excess spread released"]],
       notes = n, waterfall = w[w$waterfall != "Summary", ])
}

reconcile <- function(f) {
  rev <- f$waterfall[f$waterfall$waterfall == "Revenue", ]; prin <- f$waterfall[f$waterfall$waterfall == "Principal", ]
  pdl_cures <- sum(rev$paid[grepl("PDL", rev$item)])
  c("notes - PDL = pool" = round(sum(f$notes$closing) - sum(f$notes$pdl_balance) - f$pool, 2) == 0,
    "revenue paid = revenue available + reserve drawn" = round(sum(rev$paid) - f$revenue - sum(rev$reserve_drawn), 2) == 0,
    "principal paid = principal available + PDL cures" = round(sum(prin$paid) - f$principal - pdl_cures, 2) == 0)
}

template_commentary <- function(f) {
  change <- f$arrears_ratio - f$prev_arrears_ratio
  sprintf(paste0("In the period ending %s, principal receipts of £%.2f million were applied sequentially and repaid ",
                 "£%.2f million of Class A notes. The arrears ratio %s to %.2f%% from %.2f%%, and the annualised ",
                 "prepayment rate was %.1f%%. The reserve fund stands at its required amount of £%s."),
          f$cutoff, f$principal / 1e6, f$notes["A", "principal_paid"] / 1e6, if (change > 0) "rose" else "fell",
          f$arrears_ratio, f$prev_arrears_ratio, f$cpr, formatC(f$reserve, format = "f", digits = 2, big.mark = ","))
}
