# Turn a model's reply into an R list and check it against a small JSON schema.
library(jsonlite)

parse_json_reply <- function(text) {
  # Scan from the first "{" to its matching "}", skipping braces inside strings
  # ("note": "see {Section 4}") and escaped quotes; text after the object is ignored.
  cleaned <- trimws(gsub("```(json)?", "", text))
  start <- regexpr("{", cleaned, fixed = TRUE)
  if (start == -1) stop("no JSON object in the reply")
  chars <- strsplit(substring(cleaned, start), "")[[1]]
  depth <- 0; in_string <- FALSE; escaped <- FALSE
  for (i in seq_along(chars)) {
    ch <- chars[i]
    if (in_string) {
      if (escaped) escaped <- FALSE
      else if (ch == "\\") escaped <- TRUE
      else if (ch == '"') in_string <- FALSE
    } else if (ch == '"') in_string <- TRUE
    else if (ch == "{") depth <- depth + 1
    else if (ch == "}") {
      depth <- depth - 1
      if (depth == 0) return(fromJSON(paste(chars[1:i], collapse = ""), simplifyVector = FALSE))
    }
  }
  stop("unbalanced braces in the reply")
}

validate <- function(obj, schema) {
  errors <- character(0)
  for (f in unlist(schema$required)) if (!f %in% names(obj)) errors <- c(errors, sprintf("missing field '%s'", f))
  for (f in names(schema$properties)) {
    if (!f %in% names(obj)) next
    rule <- schema$properties[[f]]
    allowed <- unlist(rule$type)
    v <- obj[[f]]
    if (is.null(v)) {
      if (!"null" %in% allowed) errors <- c(errors, sprintf("'%s' must not be null", f))
      next
    }
    ok <- (is.character(v) && "string" %in% allowed) ||
          (is.logical(v) && "boolean" %in% allowed) ||
          (is.numeric(v) && "number" %in% allowed) ||
          (is.integer(v) && "integer" %in% allowed)
    if (!ok) {
      errors <- c(errors, sprintf("'%s' has type %s, expected %s", f, class(v)[1], paste(allowed, collapse = "/")))
      next
    }
    if (!is.null(rule$enum) && !v %in% unlist(rule$enum))
      errors <- c(errors, sprintf("'%s' = '%s' is not one of %s", f, v, paste(unlist(rule$enum), collapse = ", ")))
    if (!is.null(rule$minimum) && is.numeric(v) && v < rule$minimum)
      errors <- c(errors, sprintf("'%s' = %s is below the minimum %s", f, v, rule$minimum))
    if (!is.null(rule$pattern) && is.character(v) && !grepl(paste0("^", rule$pattern, "$"), v))
      errors <- c(errors, sprintf("'%s' = '%s' does not match %s", f, v, rule$pattern))
  }
  extra <- setdiff(names(obj), names(schema$properties))
  if (length(extra) && isFALSE(schema$additionalProperties))
    errors <- c(errors, sprintf("unexpected fields %s", paste(extra, collapse = ", ")))
  errors
}
