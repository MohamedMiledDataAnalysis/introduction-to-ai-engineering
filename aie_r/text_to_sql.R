# Ask the Harbourline database a question in English: the model writes SQL, code guards and runs it.
source("aie_r/llm.R"); source("aie_r/prompts.R"); source("aie_r/validate.R"); source("aie_r/sqlguard.R")
source("aie_r/factcheck.R")
sql_schema <- list(type = "object", properties = list(sql = list(type = "string")), required = list("sql"))

ask_database <- function(question, retries = 1) {
  p <- load_prompt("text_to_sql_v1"); schema_text <- load_prompt("am_schema")$text
  messages <- list(list(role = "user", content = render(p$text, schema = schema_text, question = question)))
  for (attempt in 0:retries) {
    reply <- chat(messages, format = sql_schema)
    sql <- tryCatch(parse_json_reply(reply$text)$sql, error = function(e) NULL)
    if (is.null(sql)) return(list(question = question, error = "no SQL in the reply", prompt = p$hash))
    result <- run_sql(sql)
    if (is.null(result$error)) break
    messages <- c(messages, list(list(role = "assistant", content = reply$text),
      list(role = "user", content = paste0("That query failed: ", result$error, ". Write a corrected query."))))
  }
  list(question = question, sql = sql, result = result, prompt = p$hash)
}
