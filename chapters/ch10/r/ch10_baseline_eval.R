# Chapter 10 - Score a no-model baseline on the prospectus evaluation set; the model must beat it
source("aie_r/prospectus_qa.R"); source("aie_r/evals.R")
index <- build_index()
cases <- read.csv("evals/sf_prospectus_qa.csv", colClasses = "character")
answers <- setNames(lapply(cases$question, function(q) answer_extractive(q, index)$answer), cases$id)
res <- run_eval(cases, answers)
ci <- wilson_interval(sum(res$passed), nrow(res))
cat(sprintf("Extractive baseline: %d/%d passed (95%% interval %.0f%%-%.0f%%)\n",
            sum(res$passed), nrow(res), 100 * ci[1], 100 * ci[2]))
for (i in which(!res$passed)) cat(sprintf("  %s  %-45s %s\n", res$id[i], res$reason[i], substr(answers[[res$id[i]]], 1, 70)))
