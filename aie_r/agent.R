# A small, inspectable agent: the model decides which tools to call, under limits,
# with every step recorded and the final answer verified before it is returned.
source("aie_r/llm.R"); source("aie_r/tools.R"); source("aie_r/factcheck.R")

facts_from_results <- function(results) {
  facts <- list()
  walk <- function(obj, path) {
    if (is.list(obj)) {
      nms <- names(obj)
      for (i in seq_along(obj)) walk(obj[[i]], if (!is.null(nms) && nms[i] != "") paste0(path, ".", nms[i]) else paste0(path, "[", i, "]"))
    } else if (is.numeric(obj) && length(obj) == 1) {
      unit <- if (endsWith(path, "_pct")) "percent" else if (endsWith(path, "_gbp") || endsWith(path, "_eur")) "money" else "number"
      facts[[path]] <<- list(value = obj, unit = unit)
      if (unit == "money") facts[[paste0(path, "#plain")]] <<- list(value = obj, unit = "number")
    }
  }
  calls <- list()
  for (r in results) {                                 # a second call of the same tool gets its own names
    calls[[r$name]] <- (if (is.null(calls[[r$name]])) 0 else calls[[r$name]]) + 1
    walk(fromJSON(r$result, simplifyVector = FALSE),
         if (calls[[r$name]] == 1) r$name else paste0(r$name, "#", calls[[r$name]]))
  }
  facts
}

passage_facts <- function(results) {
  facts <- list()
  for (r in results) {
    for (p in fromJSON(r$result, simplifyVector = FALSE)$passages) {
      figs <- extract_figures(p$text)
      for (i in seq_len(nrow(figs))) facts[[paste0(p$id, "#", i)]] <- list(value = figs$value[i] * figs$scale[i], unit = figs$unit[i])
    }
  }
  facts
}

verify_answer <- function(answer, results) {
  facts <- c(facts_from_results(results), passage_facts(results))
  clean <- gsub("\\[[A-Z][A-Za-z-]*#[0-9.]+\\]", "", answer)
  unsupported <- character(0)
  for (r in check_text(clean, facts)) if (!length(r$hits)) unsupported <- c(unsupported, r$figure$raw)
  unsupported
}

run_agent <- function(question, system, tool_names, max_steps = 6, max_tokens = 20000, verify = TRUE, history = list()) {
  messages <- c(history, list(list(role = "user", content = question)))
  trace <- list(); results <- list(); seen <- character(0); tokens <- 0; verified_once <- FALSE
  tools <- tool_specs(tool_names)
  end <- function(answer, step, status, problems = character(0))
    list(answer = answer, status = status, steps = step, tokens = tokens, trace = trace, unsupported = problems)
  for (step in seq_len(max_steps)) {
    reply <- chat(messages, system = system, tools = tools)
    tokens <- tokens + reply$input_tokens + reply$output_tokens
    if (tokens > max_tokens) return(end("stopped: token budget exceeded", step, "stopped"))
    if (length(reply$tool_calls) == 0) {
      answer <- trimws(reply$text)
      problems <- if (verify) verify_answer(answer, results) else character(0)
      if (length(problems) && !verified_once) {
        verified_once <- TRUE
        trace[[length(trace) + 1]] <- list(name = "verification", arguments = NULL, result = paste(problems, collapse = "; "))
        messages <- c(messages, list(list(role = "assistant", content = answer),
          list(role = "user", content = paste0("These figures are not supported by the tool results: ",
            paste(problems, collapse = "; "), ". Correct the answer using only figures from the tools."))))
        next
      }
      return(end(answer, step, if (length(problems)) "needs_review" else "verified", problems))
    }
    messages[[length(messages) + 1]] <- list(role = "assistant", content = reply$text,
      tool_calls = lapply(reply$tool_calls, function(c) list(`function` = c)))
    for (call in reply$tool_calls) {
      key <- paste(call$name, toJSON(call$arguments, auto_unbox = TRUE))
      if (key %in% seen) {
        result <- toJSON(list(error = "you already made this exact call; use its result above"), auto_unbox = TRUE)
      } else {
        seen <- c(seen, key)
        result <- run_tool(call, allowed = tool_names)
        if (!grepl('^\\{"error"', result)) results[[length(results) + 1]] <- list(name = call$name, result = as.character(result))
      }
      trace[[length(trace) + 1]] <- list(name = call$name, arguments = call$arguments, result = as.character(result))
      messages[[length(messages) + 1]] <- list(role = "tool", content = as.character(result), tool_name = call$name)
    }
  }
  end("stopped: step limit reached", max_steps, "stopped")
}
