# Exercise 11.2 - A read-only connection
# Run from the root of the repository:  Rscript chapters/ch11/r/solutions/ex11_2_read_only.R

library(DBI); library(RSQLite)
con <- dbConnect(SQLite(), "data/am/harbourline.sqlite", flags = SQLITE_RO)
tryCatch(dbExecute(con, "DELETE FROM issuer_esg"),
         error = function(e) cat("refused:", conditionMessage(e), "\n"))
dbDisconnect(con)
