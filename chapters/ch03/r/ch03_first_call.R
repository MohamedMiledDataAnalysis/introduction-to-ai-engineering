# Chapter 3 - Ask a question about Larkfield, giving the model the relevant section
source("aie_r/llm.R")

text     <- paste(readLines("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
                            encoding = "UTF-8"), collapse = "\n")
sections <- strsplit(text, "\n## ", fixed = TRUE)[[1]]
section  <- sections[startsWith(sections, "2. The notes")]

reply <- chat(
  system = paste("You answer questions about a securitisation using only the text provided.",
                 "If the text does not contain the answer, say so."),
  messages = list(list(role = "user",
    content = paste0("TEXT:\n", section,
                     "\n\nQUESTION: What is the margin on the Class B notes?")))
)
cat("Answer:       ", trimws(reply$text), "\n")
cat("Model:        ", reply$provider, reply$model, "\n")
cat("Input tokens: ", reply$input_tokens, "\n")
cat("Output tokens:", reply$output_tokens, "\n")
cat("Seconds:      ", reply$seconds, "\n")
