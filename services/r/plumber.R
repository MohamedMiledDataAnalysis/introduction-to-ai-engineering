# The AI engineering service in R: the agents and their tools behind an HTTP API.
# Run from the repository root:  Rscript -e 'plumber::pr_run(plumber::pr("services/r/plumber.R"), port = 8001)'
root <- normalizePath(Sys.getenv("AIE_ROOT", "../.."))   # plumber runs this file from services/r
setwd(root)
source("aie_r/agent.R")
api_key <- Sys.getenv("AIE_API_KEY", "")
if (api_key == "") {
  if (Sys.getenv("AIE_ENV", "dev") != "dev") stop("set AIE_API_KEY before starting the service")  # on a server
  api_key <- "dev-key-change-me"                                                                  # on your laptop
}
sf_tools <- c("pool_summary", "note_balance", "waterfall_summary", "search_prospectus")
am_tools <- c("fund_performance", "top_holdings")
systems <- list(
  sf = paste("You are an assistant for Larkfield Mortgage Funding 2025-1. Use the tools for every figure and search the",
             "prospectus for rules. Cite passage identifiers such as [LMF#3]. Never compute or estimate a figure."),
  am = paste("You are an assistant for Harbourline funds. Use the tools for every figure. Never compute or estimate a",
             "figure, never forecast and never recommend an investment."))

log_event <- function(...) {
  dir.create("logs", showWarnings = FALSE)
  cat(toJSON(c(list(...), ts = format(Sys.time(), "%Y-%m-%dT%H:%M:%S")), auto_unbox = TRUE), "\n",
      file = "logs/requests.jsonl", append = TRUE, sep = "")
}

#* @filter api_key
function(req, res) {
  if (req$PATH_INFO != "/health" && !identical(req$HTTP_X_API_KEY, api_key)) {
    res$status <- 401
    res$body <- jsonlite::toJSON(list(detail = "invalid API key"), auto_unbox = TRUE)
    return(res)
  }
  plumber::forward()
}

#* @get /health
#* @serializer unboxedJSON
function() list(status = "ok")

#* @post /<domain>/ask
#* @serializer unboxedJSON
function(domain, req, res) {
  owd <- setwd(root); on.exit(setwd(owd))          # each request runs from the repository root
  body <- jsonlite::fromJSON(req$postBody)
  if (!domain %in% c("sf", "am")) { res$status <- 404; return(list(detail = "domain must be 'sf' or 'am'")) }
  if (is.null(body$question) || nchar(body$question) < 3) { res$status <- 422; return(list(detail = "question too short")) }
  if (nchar(body$question) > 2000) { res$status <- 422; return(list(detail = "question too long (2,000 characters at most)")) }
  start <- Sys.time(); id <- paste(sample(c(letters, 0:9), 16, TRUE), collapse = "")
  tools <- if (domain == "sf") sf_tools else am_tools
  result <- tryCatch(run_agent(body$question, systems[[domain]], tools), error = function(e) e)
  secs <- round(as.numeric(difftime(Sys.time(), start, units = "secs")), 3)
  if (inherits(result, "llm_error")) {                      # the model server is down: temporary, say so
    log_event(request_id = id, domain = domain, question = body$question, status = "error",
              error = substr(conditionMessage(result), 1, 300), seconds = secs)
    res$status <- 503
    return(list(detail = "the assistant is unavailable; please try again later"))
  }
  if (inherits(result, "error")) {                          # a bug in our code: not temporary
    log_event(request_id = id, domain = domain, question = body$question, status = "bug",
              error = substr(conditionMessage(result), 1, 300), seconds = secs)
    res$status <- 500
    return(list(detail = "internal error; it has been logged"))
  }
  tools_used <- vapply(result$trace, `[[`, "", "name")
  log_event(request_id = id, domain = domain, question = body$question, status = result$status, steps = result$steps,
            tokens = result$tokens, tools = tools_used, answer = result$answer, seconds = secs)
  list(request_id = id, answer = result$answer, status = result$status, unsupported = I(result$unsupported),
       tools_used = I(tools_used))
}

#* @get /tools/pool_summary
#* @serializer unboxedJSON
function(cutoff_date, res) {
  owd <- setwd(root); on.exit(setwd(owd))
  out <- fromJSON(run_tool(list(name = "pool_summary", arguments = list(cutoff_date = cutoff_date))), simplifyVector = FALSE)
  if (!is.null(out$error)) { res$status <- 400; return(list(detail = out$error)) }
  out
}
