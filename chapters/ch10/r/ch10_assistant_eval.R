# Chapter 10 - Evaluate the model-based assistant: answers, grounding and retrieval, side by side
source("aie_r/prospectus_qa.R"); source("aie_r/evals.R")
index <- build_index()
cases <- read.csv("evals/sf_prospectus_qa.csv", colClasses = "character")
outputs <- setNames(lapply(cases$question, function(q) answer_llm(q, index)), cases$id)
res <- run_eval(cases, lapply(outputs, `[[`, "answer"))
grounded <- sum(vapply(outputs, function(o) length(o$problems) == 0, TRUE))
ans <- cases[cases$source_section != "", ]
hits <- sum(vapply(seq_len(nrow(ans)), function(i)
  ans$source_section[i] %in% sub("\\..*", "", sub(".*#", "", outputs[[ans$id[i]]]$retrieved)), TRUE))
ci <- wilson_interval(sum(res$passed), nrow(res))
cat(sprintf("prompt %s\nanswers correct : %d/%d (%.0f%%-%.0f%%)\nanswers grounded: %d/%d\nretrieval hits  : %d/%d\n",
            outputs[[1]]$prompt, sum(res$passed), nrow(res), 100 * ci[1], 100 * ci[2], grounded, nrow(res), hits, nrow(ans)))
for (i in which(!res$passed)) cat(sprintf("  %s  %s  | problems: %s\n", res$id[i], res$reason[i],
                                          paste(outputs[[res$id[i]]]$problems, collapse = "; ")))
