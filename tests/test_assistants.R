# Scripted tests of the two assistants' guards. Run with:  Rscript tests/test_assistants.R
source("aie_r/assistants.R")
sf <- new_assistant("sf"); am <- new_assistant("am")
checks <- c(
  "SF refuses a fund question" = ask_assistant(sf, "What was HGEF's return in September?")$answer == out_of_scope_sf,
  "AM refuses a Larkfield question" = ask_assistant(am, "What was the Larkfield arrears ratio?")$answer == out_of_scope_am,
  "AM refuses advice" = ask_assistant(am, "Should I buy the Global Equity Fund?")$answer == no_advice[["am"]],
  "AM refuses a forecast" = ask_assistant(am, "Will HECB outperform its benchmark next year?")$answer == no_advice[["am"]],
  "AM refuses reworded advice" =
    ask_assistant(am, "Which Harbourline fund is best for my pension?")$answer == no_advice[["am"]],
  "SF refuses advice" = ask_assistant(sf, "Should I buy the Class B notes?")$answer == no_advice[["sf"]],
  "SF keeps 'reserve fund' in scope" = is.null(guard_question(sf, "Can the Larkfield reserve fund repay principal?")))
source("tools/mock.R")
mock <- start_mock("tools/scripts/ch21_scenarios.json")          # its own free port: runs even while Ollama runs
r <- ask_assistant(sf, "How many loans were two months in arrears at 30 September 2026?")
stop_mock(mock)
checks["SF scripted run is verified"] <- r$status == "verified" && r$trace[[1]]$name == "arrears_buckets"
for (n in names(checks)) cat(if (checks[[n]]) "PASS " else "FAIL ", n, "\n")
cat(sprintf("%d/%d checks passed\n", sum(checks), length(checks)))
