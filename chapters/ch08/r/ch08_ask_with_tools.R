# Chapter 8 - Ask a question; the model calls tools for the figures
source("aie_r/toolloop.R")
out <- ask_with_tools(paste("What was the Class A note balance after the September 2026 payment,",
                            "and the arrears ratio of the pool at that date?"), trace = list())
for (t in out$trace) cat(sprintf("tool  %s(%s)\n      -> %s...\n", t$name,
                                 toJSON(t$arguments, auto_unbox = TRUE), substr(t$result, 1, 110)))
cat("\nanswer:", out$answer, "\n")
