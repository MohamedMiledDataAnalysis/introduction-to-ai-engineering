# One function to talk to a language model, whichever provider runs it.
#
#   source("aie_r/llm.R")
#   reply <- chat(list(list(role = "user", content = "Hello")))
#   cat(reply$text)
#
# Providers: "ollama" (local, default) and "anthropic" (paid API; needs ANTHROPIC_API_KEY).
library(httr2)

aie_provider <- Sys.getenv("AIE_PROVIDER", "ollama")
aie_model    <- Sys.getenv("AIE_MODEL", "qwen3.5:4b")
ollama_url   <- Sys.getenv("OLLAMA_URL", "http://localhost:11434")

llm_error <- function(...) {
  # a classed error, so that callers can tell "the model is unavailable" from a bug in their own code
  stop(structure(class = c("llm_error", "error", "condition"), list(message = paste0(...), call = NULL)))
}

llm_post <- function(url, payload, headers = list(), timeout = 300, retries = 2) {
  req <- request(url) |>
    req_body_json(payload, auto_unbox = TRUE, null = "null") |>
    req_timeout(timeout) |>
    req_error(is_error = function(resp) FALSE) |>
    req_retry(max_tries = retries + 1,
              is_transient = function(resp) resp_status(resp) %in% c(429, 500, 502, 503, 529),
              backoff = function(i) min(2^(i - 1), 8))
  if (length(headers)) req <- req_headers(req, !!!headers)
  resp <- tryCatch(req_perform(req), error = function(e) llm_error("cannot reach ", url, ": ", conditionMessage(e)))
  if (resp_status(resp) != 200) {
    llm_error(sprintf("HTTP %d: %s", resp_status(resp), substr(resp_body_string(resp), 1, 200)))
  }
  resp_body_json(resp, simplifyVector = FALSE)
}

chat <- function(messages, model = aie_model, provider = aie_provider, system = NULL,
                 temperature = 0, seed = 42, max_tokens = 1024, format = NULL, tools = NULL,
                 timeout = 300, retries = 2, think = FALSE, num_ctx = 16384) {
  start <- Sys.time()
  if (provider == "ollama") {
    msgs <- if (is.null(system)) messages else c(list(list(role = "system", content = system)), messages)
    payload <- list(model = model, messages = msgs, stream = FALSE,
                    think = think,                     # FALSE: answer directly, no hidden reasoning first
                    options = list(temperature = temperature, seed = seed, num_predict = max_tokens,
                                   num_ctx = num_ctx)) # context window; Ollama's own default can be 4,096
    if (!is.null(format)) payload$format <- format
    if (!is.null(tools)) payload$tools <- tools
    out <- llm_post(paste0(ollama_url, "/api/chat"), payload, timeout = timeout, retries = retries)
    msg <- out$message
    calls <- lapply(msg$tool_calls, function(tc) tc$`function`)
    result <- list(text = if (is.null(msg$content)) "" else msg$content,
                   tool_calls = calls,
                   input_tokens = if (is.null(out$prompt_eval_count)) 0 else out$prompt_eval_count,
                   output_tokens = if (is.null(out$eval_count)) 0 else out$eval_count)
    if (result$input_tokens >= 0.9 * num_ctx)
      warning(sprintf("prompt uses %d of %d context tokens: Ollama drops the oldest text beyond the window",
                      result$input_tokens, num_ctx))
  } else if (provider == "anthropic") {
    if (!is.null(tools) || !is.null(format))
      stop("tools and format are implemented for Ollama only in this wrapper")
    key <- Sys.getenv("ANTHROPIC_API_KEY")
    if (key == "") stop("set the ANTHROPIC_API_KEY environment variable")
    payload <- list(model = model, max_tokens = max_tokens, messages = messages,
                    temperature = temperature)
    if (!is.null(system)) payload$system <- system
    out <- llm_post("https://api.anthropic.com/v1/messages", payload,
                    headers = list(`x-api-key` = key, `anthropic-version` = "2023-06-01"),
                    timeout = timeout, retries = retries)
    texts <- vapply(out$content, function(b) if (identical(b$type, "text")) b$text else "", "")
    result <- list(text = paste(texts, collapse = ""), tool_calls = list(),
                   input_tokens = out$usage$input_tokens, output_tokens = out$usage$output_tokens)
  } else {
    stop("unknown provider: ", provider)
  }
  result$provider <- provider
  result$model <- model
  result$seconds <- round(as.numeric(difftime(Sys.time(), start, units = "secs")), 3)
  result
}

embed <- function(texts, model = "nomic-embed-text") {
  out <- llm_post(paste0(ollama_url, "/api/embed"), list(model = model, input = as.list(texts)))
  lapply(out$embeddings, unlist)
}
