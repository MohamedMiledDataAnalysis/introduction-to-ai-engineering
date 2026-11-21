# Exercise 9.2 - A follow-up question with history
# Run from the root of the repository:  Rscript chapters/ch09/r/solutions/ex9_2_follow_up.R

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
source("aie_r/agent.R")
first_q <- "What was the pool balance at 30 September 2026?"
first   <- run_agent(first_q, system_prompt, tool_names)
history <- list(list(role = "user", content = first_q),
                list(role = "assistant", content = first$answer))
second  <- run_agent("And at the end of August?", system_prompt,
                     tool_names, history = history)
show(second)
