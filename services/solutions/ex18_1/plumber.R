# Exercise 18.1 - The R service with a fund performance endpoint
# Run from the root of the repository:  Rscript -e 'plumber::pr_run(plumber::pr("services/solutions/ex18_1/plumber.R"), port = 8001)'

`%||%` <- function(a, b) if (is.null(a)) b else a
root <- normalizePath(Sys.getenv("AIE_ROOT", "../../.."))  # plumber runs from services/solutions/ex18_1
setwd(root)
source("aie_r/assistants.R")
api_key <- Sys.getenv("AIE_API_KEY", "")
if (api_key == "") {
  if (Sys.getenv("AIE_ENV", "dev") != "dev")         # on a server
    stop("set AIE_API_KEY before starting the service")
  api_key <- "dev-key-change-me"                     # on your laptop only
}
assistants <- list(sf = new_assistant("sf"), am = new_assistant("am"))  # guards
same_key <- function(a, b) {    # compare hashes: the time does not depend on the guess
  h <- function(x) digest::digest(enc2utf8(x), "sha256", serialize = FALSE)
  identical(h(a), h(b))
}

log_event <- function(...) {
  dir.create("logs", showWarnings = FALSE)
  cat(toJSON(c(list(...), ts = format(Sys.time(), "%Y-%m-%dT%H:%M:%S")), auto_unbox = TRUE),
      "\n", file = "logs/requests.jsonl", append = TRUE, sep = "")
}

#* @filter api_key
function(req, res) {
  if (req$PATH_INFO != "/health" && !same_key(req$HTTP_X_API_KEY %||% "", api_key)) {
    res$status <- 401
    res$setHeader("Content-Type", "application/json")
    res$body <- jsonlite::toJSON(list(detail = "invalid API key"),
                                 auto_unbox = TRUE)
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
  owd <- setwd(root); on.exit(setwd(owd))   # run from the repository root
  if (!domain %in% c("sf", "am")) {
    res$status <- 404; return(list(detail = "domain must be 'sf' or 'am'"))
  }
  body <- tryCatch(jsonlite::fromJSON(req$postBody), error = function(e) NULL)
  q <- if (is.list(body)) body$question
  if (!is.character(q) || length(q) != 1 || nchar(q) < 3 || nchar(q) > 2000) {
    res$status <- 422   # the same rule as Python's pydantic class
    return(list(detail = "question must be one text of 3 to 2,000 characters"))
  }
  start <- Sys.time(); id <- paste(sample(c(letters, 0:9), 16, TRUE), collapse = "")
  result <- tryCatch(ask_assistant(assistants[[domain]], q),   # guards, then the agent
                     error = function(e) e)
  secs <- round(as.numeric(difftime(Sys.time(), start, units = "secs")), 3)
  if (inherits(result, "llm_error")) {      # the model server is down
    log_event(request_id = id, domain = domain, question = q, status = "error",
              error = substr(conditionMessage(result), 1, 300), seconds = secs)
    res$status <- 503
    return(list(detail = "the assistant is unavailable; please try again later"))
  }
  if (inherits(result, "error")) {          # a bug in our code
    log_event(request_id = id, domain = domain, question = q, status = "bug",
              error = substr(conditionMessage(result), 1, 300), seconds = secs)
    res$status <- 500
    return(list(detail = "internal error; it has been logged"))
  }
  tools_used <- vapply(result$trace, `[[`, "", "name")
  log_event(request_id = id, domain = domain, question = q, status = result$status,
            steps = result$steps, tokens = result$tokens, tools = tools_used,
            answer = result$answer, seconds = secs)
  list(request_id = id, answer = result$answer, status = result$status,
       unsupported = I(result$unsupported), tools_used = I(tools_used))
}

#* @get /tools/pool_summary
#* @serializer unboxedJSON
function(res, cutoff_date = "") {
  owd <- setwd(root); on.exit(setwd(owd))
  if (!nzchar(cutoff_date)) {
    res$status <- 400; return(list(detail = "missing argument: cutoff_date"))
  }
  out <- fromJSON(run_tool(list(name = "pool_summary",
                                arguments = list(cutoff_date = cutoff_date))),
                  simplifyVector = FALSE)
  if (!is.null(out$error)) { res$status <- 400; return(list(detail = out$error)) }
  out
}

#* @get /tools/fund_performance
#* @serializer unboxedJSON
function(fund_code, months, res) {
  owd <- setwd(root); on.exit(setwd(owd))
  out <- fromJSON(run_tool(list(name = "fund_performance",
    arguments = list(fund_code = fund_code, months = as.integer(months)))),
    simplifyVector = FALSE)
  if (!is.null(out$error)) { res$status <- 400; return(list(detail = out$error)) }
  out
}
