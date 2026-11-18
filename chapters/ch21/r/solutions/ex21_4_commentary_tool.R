# Exercise 21.4 - The investor report workflow of Chapter 14 as a tool of the SF agent
# Run from the root of the repository, with the mock model on the script of this exercise:
#   MOCK_SCRIPT=tools/scripts/ex21_4_commentary.json python tools/mock_ollama.py &
#   Rscript chapters/ch21/r/solutions/ex21_4_commentary_tool.R
suppressPackageStartupMessages({source("aie_r/assistants.R"); source("aie_r/investor_report.R")})

dates <- sort(unique(read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")$RREL6))[-1]   # no report at closing

commentary_figures <- function(f) {
  # the figures the commentary may quote, named with the unit suffixes the verifier reads
  list(principal_receipts_gbp = f$principal, class_a_principal_paid_gbp = f$notes["A", "principal_paid"],
       arrears_ratio_pct = round(f$arrears_ratio, 4), previous_arrears_ratio_pct = round(f$prev_arrears_ratio, 4),
       cpr_pct = round(f$cpr, 4), reserve_fund_gbp = f$reserve, pool_balance_gbp = f$pool)
}

draft_investor_commentary <- function(cutoff_date) {
  if (!cutoff_date %in% dates)
    stop(sprintf("no investor report for %s; reports run from %s to %s", cutoff_date, dates[1], dates[length(dates)]))
  f <- month_figures(cutoff_date)
  checks <- reconcile(f)
  if (!all(checks)) stop("reconciliation failed: ", paste(names(checks)[!checks], collapse = "; "))
  text <- template_commentary(f)
  figs <- commentary_figures(f)
  facts <- lapply(names(figs), function(n)
    list(value = figs[[n]], unit = if (endsWith(n, "_gbp")) "money" else "percent"))
  names(facts) <- names(figs)
  unsupported <- vapply(Filter(function(r) !length(r$hits), check_text(text, facts)), function(r) r$figure$raw, "")
  list(cutoff_date = cutoff_date, commentary = text, unsupported_figures = I(unsupported),
       approval_required = TRUE, figures = figs)
}

registry$draft_investor_commentary <- list(fn = draft_investor_commentary,
  description = paste("Draft the commentary of the Larkfield 2025-1 investor report for one collection period,",
                      "after the reconciliations pass. The draft must be approved by an analyst before publication."),
  parameters = list(type = "object", properties = list(cutoff_date = date_rule),
                    required = list("cutoff_date"), additionalProperties = FALSE))

ask_sf <- function(a, question) {
  # the SF assistant's answer, with the status forced to needs_review when the commentary tool ran
  r <- ask_assistant(a, question)
  if (any(vapply(r$trace, function(s) identical(s$name, "draft_investor_commentary"), TRUE))) {
    r$status <- "needs_review"; r$unsupported <- c(r$unsupported, "investor commentary: approval required")
  }
  r
}

# 1. The tool on its own, through run_tool() as the agent calls it
for (d in c("2026-09-30", "2026-10-31", "2025-06-30")) {
  out <- fromJSON(run_tool(list(name = "draft_investor_commentary", arguments = list(cutoff_date = d))))
  cat(d, "->", if (!is.null(out$error)) out$error else
        paste0(substr(out$commentary, 1, 70), "... | unsupported: [", paste(out$unsupported_figures, collapse = ", "), "]"), "\n")
}

# 2. The reconciliation gate: break one note balance on the way in
shipped <- month_figures
month_figures <- function(cutoff) { f <- shipped(cutoff); f$notes["A", "closing"] <- f$notes["A", "closing"] + 100; f }
cat("broken notes ->", fromJSON(run_tool(list(name = "draft_investor_commentary",
                                              arguments = list(cutoff_date = "2026-09-30"))))$error, "\n")
month_figures <- shipped

# 3. The agent with the new tool, on the scripted model
sf <- new_assistant("sf"); sf$tools <- c(sf$tools, "draft_investor_commentary")
r <- ask_sf(sf, "Draft the commentary for the September 2026 investor report.")
cat("agent tools used:", vapply(r$trace, `[[`, "", "name"), "\n")
cat("status:", r$status, "| flags:", paste(r$unsupported, collapse = "; "), "\n")
