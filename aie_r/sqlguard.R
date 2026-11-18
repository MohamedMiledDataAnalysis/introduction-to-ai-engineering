# Run model-written SQL safely: one read-only SELECT on allowed tables, with a row limit.
library(DBI); library(RSQLite)
forbidden_sql <- "\\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace\\s+into|vacuum|reindex)\\b"
clause_end <- "(?i)\\b(where|group|order|having|limit|union|except|intersect|on|using)\\b|\\)"

tables_in <- function(sql) {
  # every table named after FROM or JOIN, including comma-separated lists: FROM funds f, holdings h
  found <- character(0)
  starts <- gregexpr("(?i)\\b(from|join)\\s+", sql, perl = TRUE)[[1]]
  if (starts[1] == -1) return(found)
  for (i in seq_along(starts)) {
    kw <- tolower(substr(sql, starts[i], starts[i] + 3))
    rest <- substring(sql, starts[i] + attr(starts, "match.length")[i])
    e <- regexpr(clause_end, rest, perl = TRUE)
    clause <- if (e > 0) substr(rest, 1, e - 1) else rest
    parts <- strsplit(clause, ",", fixed = TRUE)[[1]]
    if (kw == "join") parts <- parts[1]
    for (p in parts) {
      if (startsWith(trimws(p), "(")) next
      m <- regmatches(p, regexpr("(?i)^\\s*[a-z_][a-z0-9_]*", p, perl = TRUE))
      if (length(m)) found <- c(found, trimws(m))
    }
  }
  found
}
default_tables <- c("funds", "securities", "holdings", "nav", "benchmark_returns", "issuer_esg", "transactions")

check_sql <- function(sql, allowed_tables = default_tables) {
  s <- trimws(sub(";\\s*$", "", trimws(sql)))
  problems <- character(0)
  if (grepl(";", s, fixed = TRUE)) problems <- c(problems, "more than one statement")
  if (!grepl("^\\s*(select|with)\\b", s, ignore.case = TRUE, perl = TRUE)) problems <- c(problems, "not a SELECT query")
  m <- regmatches(s, regexpr(forbidden_sql, s, ignore.case = TRUE, perl = TRUE))
  if (length(m)) problems <- c(problems, paste("forbidden keyword:", m))
  ctes <- regmatches(s, gregexpr("(?i)(\\bwith|,)\\s*[a-z_][a-z0-9_]*\\s+as\\s*\\(", s, perl = TRUE))[[1]]
  ctes <- tolower(sub("(?i)^(with|,)\\s*([a-z_][a-z0-9_]*).*$", "\\2", ctes, perl = TRUE))   # WITH t AS (...)
  tabs <- tolower(tables_in(s))
  for (t in setdiff(tabs, c(allowed_tables, ctes))) problems <- c(problems, paste("table not allowed:", t))
  list(problems = problems, sql = s)
}

run_sql <- function(sql, db = "data/am/harbourline.sqlite", allowed_tables = default_tables, max_rows = 200) {
  chk <- check_sql(sql, allowed_tables)
  if (length(chk$problems)) return(list(error = paste(chk$problems, collapse = "; ")))
  con <- dbConnect(SQLite(), db, flags = SQLITE_RO)             # the database cannot be changed
  on.exit(dbDisconnect(con))
  res <- tryCatch(dbGetQuery(con, sprintf("SELECT * FROM (%s) LIMIT %d", chk$sql, max_rows + 1)),
                  error = function(e) list(error = paste("SQL error:", conditionMessage(e))))
  if (!is.data.frame(res)) return(res)
  list(columns = names(res), rows = head(res, max_rows), truncated = nrow(res) > max_rows)
}

same_result <- function(a, b, ordered = FALSE, digits = 6) {
  if (!is.null(a$error) || !is.null(b$error)) return(FALSE)
  norm <- function(df) {
    df <- as.data.frame(lapply(df, function(x) if (is.numeric(x)) round(x, digits) else x))
    names(df) <- paste0("c", seq_along(df))
    rows <- apply(df, 1, function(r) paste(trimws(r), collapse = "|"))
    if (ordered) rows else sort(rows)
  }
  ra <- norm(a$rows); rb <- norm(b$rows)
  length(ra) == length(rb) && all(ra == rb)
}
