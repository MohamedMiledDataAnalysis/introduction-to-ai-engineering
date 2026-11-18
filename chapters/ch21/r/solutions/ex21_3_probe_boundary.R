# Exercise 21.3 - Probe the boundary of the SF scope guard, and show the test protecting it
# Run from the root of the repository:  Rscript chapters/ch21/r/solutions/ex21_3_probe_boundary.R
suppressPackageStartupMessages(source("aie_r/assistants.R"))
sf <- new_assistant("sf")
probes <- c("Compare the HGEF factsheet with the HECB KID.",
            "Which fund does the Larkfield reserve fund protect?",
            "What is the bond fund duration?",
            "Which notes does the reserve fund protect?",
            "What is the duration of the euro credit product?")
show <- function(title) {
  cat(title, "\n")
  for (q in probes)
    cat(sprintf("  %s  %s\n", if (identical(guard_question(sf, q), out_of_scope_sf)) "refused " else "accepted", q))
}
show("Guard as shipped:")

# Change 1: add 'fund' on its own to the asset management words
shipped_words <- am_words; shipped_guard <- guard_question
am_words <- sub("equity fund|bond fund", "equity fund|bond fund|fund", am_words, fixed = TRUE)
show("Change 1, 'fund' added to am_words:")

# Change 2: on top of change 1, simplify the rule to 'refuse any question with an AM word'
guard_question <- function(a, question) {
  if (a$domain == "sf" && grepl(am_words, question, ignore.case = TRUE, perl = TRUE)) return(out_of_scope_sf)
  shipped_guard(a, question)
}
show("Change 2, and the rule simplified:")
ok <- is.null(guard_question(sf, "Which fund does the Larkfield reserve fund protect?"))
cat("Test 'SF accepts fund in a Larkfield question':", if (ok) "PASS" else "FAIL", "\n")
am_words <- shipped_words; guard_question <- shipped_guard
