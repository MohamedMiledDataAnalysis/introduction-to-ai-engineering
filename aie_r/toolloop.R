# Answer a question with tools: the model asks for tool calls, code runs them, the model answers.
source("aie_r/llm.R"); source("aie_r/tools.R")
toolloop_system <- paste("You answer questions about Larkfield Mortgage Funding 2025-1 and Harbourline funds.",
                         "Get every figure from a tool; never compute or estimate a figure yourself.",
                         "Quote figures as the tools return them, rounded only as the question asks.",
                         "If no tool can answer, say so.")

ask_with_tools <- function(question, tool_names = NULL, max_rounds = 3, system = toolloop_system, trace = NULL) {
  messages <- list(list(role = "user", content = question))
  tools <- tool_specs(tool_names)
  for (round in seq_len(max_rounds)) {
    reply <- chat(messages, system = system, tools = tools)
    if (length(reply$tool_calls) == 0) return(list(answer = reply$text, trace = trace))
    messages[[length(messages) + 1]] <- list(role = "assistant", content = reply$text,
      tool_calls = lapply(reply$tool_calls, function(c) list(`function` = c)))
    for (call in reply$tool_calls) {
      result <- run_tool(call, allowed = tool_names)
      trace[[length(trace) + 1]] <- list(name = call$name, arguments = call$arguments, result = as.character(result))
      messages[[length(messages) + 1]] <- list(role = "tool", content = as.character(result), tool_name = call$name)
    }
  }
  list(answer = "I could not complete the answer within the allowed number of steps.", trace = trace)
}
