# Chapter 9 - Watch the agent work, recover from an unsupported figure, and stop a loop
source("aie_r/agent.R")
source("tools/mock.R")
system_prompt <- paste(
  "You are an assistant for Larkfield Mortgage Funding 2025-1. Use the",
  "tools for every figure and search the prospectus for rules and",
  "definitions. Cite passage identifiers such as [LMF#3]. Never compute",
  "or estimate a figure yourself.")
tool_names <- c("pool_summary", "note_balance", "waterfall_summary",
                "search_prospectus")
show <- function(r) {
  for (t in r$trace) cat(sprintf("  %-18s %-60s %s\n", t$name,
    substr(toJSON(t$arguments, auto_unbox = TRUE), 1, 60),
    substr(t$result, 1, 60)))
  cat(sprintf("  status=%s steps=%d unsupported=[%s]\n  answer: %s\n\n",
              r$status, r$steps, paste(r$unsupported, collapse = ", "),
              r$answer))
}
question <- paste("How much excess spread was released in September 2026,",
                  "and to whom does it go?")
if (nzchar(Sys.getenv("USE_MOCK_SCRIPTS"))) {   # scripted model, for the scenarios
  for (script in c("tools/scripts/ch09_correction.json",
                   "tools/scripts/ch09_loop.json")) {
    mock <- start_mock(script)                   # the mock on a free port
    cat("Scenario", basename(script), "\n")
    show(run_agent(question, system_prompt, tool_names))
    stop_mock(mock)
  }
} else {
  show(run_agent(question, system_prompt, tool_names))
}
