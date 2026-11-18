# Chapter 12 - Run the data-quality rules on the received tape and measure them against the injected errors
source("aie_r/dq.R"); library(jsonlite)
tape  <- read.csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv",
                  stringsAsFactors = FALSE)
truth <- fromJSON("data/sf/rmbs/dq/injected_errors.json")
found <- run_rules(tape, "2026-09-30")
print(table(found$rule))
key <- function(df) paste(df$loan_id, df$rule)
tp <- intersect(key(found), key(truth))
fp <- setdiff(key(found), key(truth))
fn <- setdiff(key(truth), key(found))
cat(sprintf("\ntrue positives %d, false positives %d, false negatives %d\n",
            length(tp), length(fp), length(fn)))
cat(sprintf("precision %.0f%%, recall %.0f%%\n",
            100 * length(tp) / nrow(found), 100 * length(tp) / nrow(truth)))
for (x in fp) cat("  extra flag:", x, "\n")
for (x in fn) cat("  missed:    ", x, "\n")
