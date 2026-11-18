# Prompt templates stored as versioned text files in prompts/.
library(digest, quietly = TRUE, warn.conflicts = FALSE)

load_prompt <- function(name, dir = "prompts") {
  text <- paste(readLines(file.path(dir, paste0(name, ".txt")), encoding = "UTF-8"), collapse = "\n")
  list(text = text, hash = substr(digest(text, algo = "sha256", serialize = FALSE), 1, 10))
}

render <- function(template, ...) {
  values <- list(...)
  needed <- unique(regmatches(template, gregexpr("\\{([a-z_][a-z0-9_]*)\\}", template))[[1]])
  needed <- gsub("[{}]", "", needed)
  missing <- setdiff(needed, names(values))
  if (length(missing)) stop("missing values for placeholders: ", paste(missing, collapse = ", "))
  for (k in names(values)) template <- gsub(paste0("{", k, "}"), as.character(values[[k]]), template, fixed = TRUE)
  template
}
