# Chapter 0 - Check that R, httr2 and Ollama work together
# Run from the root of the repository:  Rscript chapters/ch00/r/check_setup.R
library(httr2)

model      <- "qwen3.5:4b"
ollama_url <- "http://localhost:11434/api/chat"

cat("R version: ", R.version$major, ".", R.version$minor, "\n", sep = "")
cat("httr2 version:", as.character(packageVersion("httr2")), "\n")

tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
cat("Loan tape rows:", nrow(tape), "\n")

req <- request(ollama_url) |>
  req_body_json(list(
    model    = model,
    messages = list(list(role = "user",
      content = "Reply with exactly these three words: Ollama is ready")),
    stream   = FALSE,
    think    = FALSE    # answer directly; Chapter 3 explains
  )) |>
  req_timeout(300)

result <- tryCatch(
  {
    resp <- req_perform(req)
    cat("Model reply:", trimws(resp_body_json(resp)$message$content), "\n")
  },
  httr2_failure = function(e) {
    cat("Ollama is not running. Start the Ollama application,",
        "then run this script again.\n")
  },
  httr2_http = function(e) {
    cat("Ollama answered with an error:", conditionMessage(e), "\n")
    cat("Check that you downloaded the model with: ollama pull", model, "\n")
  }
)
