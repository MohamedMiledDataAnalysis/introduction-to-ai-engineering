# Chapter 5 - Run the evaluation against the live assistant and save the answers
source("aie_r/llm.R"); source("aie_r/evals.R")
prospectus <- paste(readLines("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md", encoding = "UTF-8"),
                    collapse = "\n")
system_prompt <- paste("You answer questions about the Larkfield Mortgage Funding 2025-1 prospectus using only",
                       "the text provided. Quote figures exactly as written. If the text does not contain the",
                       "answer, say: 'The document does not state this.'")
cases <- read.csv("evals/sf_prospectus_qa.csv", colClasses = "character")
answers <- list()
for (i in seq_len(nrow(cases))) {
  reply <- chat(system = system_prompt, messages = list(list(role = "user",
    content = paste0("TEXT:\n", prospectus, "\n\nQUESTION: ", cases$question[i]))))
  answers[[cases$id[i]]] <- trimws(reply$text)
}
stamp <- format(Sys.time(), "%Y%m%d_%H%M")
write.csv(data.frame(id = names(answers), answer = unlist(answers)),
          sprintf("evals/candidates/prospectus_qa_live_%s.csv", stamp), row.names = FALSE)
res <- run_eval(cases, answers)
ci <- wilson_interval(sum(res$passed), nrow(res))
cat(sprintf("Live run: %d/%d passed; 95%% interval %.0f%% to %.0f%%\n",
            sum(res$passed), nrow(res), 100 * ci[1], 100 * ci[2]))
print(res[!res$passed, c("id", "reason")], row.names = FALSE)
