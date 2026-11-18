# Chapter 8 - Run tool calls of the kind a model emits, including bad ones
source("aie_r/tools.R")
cat("Tools offered to the model:", paste(vapply(tool_specs(),
    function(t) t$`function`$name, ""), collapse = ", "), "\n")
calls <- list(
  list(name = "pool_summary", arguments = list(cutoff_date = "2026-09-30")),
  list(name = "note_balance",
       arguments = list(note_class = "A", cutoff_date = "2026-09-30")),
  list(name = "fund_performance",
       arguments = list(fund_code = "HGEF", months = 12L)),
  list(name = "note_balance",
       arguments = list(note_class = "E", cutoff_date = "2026-09-30")),
  list(name = "pool_summary", arguments = list(cutoff_date = "2026-10-31")),
  list(name = "delete_loans", arguments = list())
)
for (c in calls) cat(sprintf("\n%s(%s)\n  -> %s\n", c$name,
  toJSON(c$arguments, auto_unbox = TRUE), run_tool(c)))
