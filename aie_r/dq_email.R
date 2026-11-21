# Draft the data query to the servicer with a model, then check it against the list of issues.
source("aie_r/llm.R"); source("aie_r/prompts.R")
issues_text <- function(found) paste(sprintf("- %s: %s", found$loan_id, found$description), collapse = "\n")

draft_email <- function(found, cutoff_date, deadline) {
  p <- load_prompt("servicer_query_email_v1")
  prompt <- render(p$text, cutoff_date = cutoff_date, deadline = deadline, issues = issues_text(found))
  list(email = trimws(chat(list(list(role = "user", content = prompt)), temperature = 0.2)$text), prompt = p$hash)
}

check_email <- function(email, found) {
  written <- regmatches(email, gregexpr("LMF25-[0-9]{5}", email))[[1]]
  expected <- unique(found$loan_id)
  c(sprintf("loan %s is not in the issue list",
            sort(setdiff(unique(written), expected))),
    sprintf("loan %s is missing from the email",
            sort(setdiff(expected, written))),
    sprintf("loan %s is mentioned %d times",
            names(which(table(written) > 1)),
            as.integer(table(written)[table(written) > 1])))
}

template_email <- function(found, cutoff_date, deadline) {
  paste0("Dear colleagues,\n\nOur checks of the loan-level tape for ", cutoff_date, " found the following issues. ",
         "Please confirm or correct each one and send a corrected tape by ", deadline, ".\n\n", issues_text(found),
         "\n\nKind regards,\nLarkfield 2025-1 Cash Management")
}
