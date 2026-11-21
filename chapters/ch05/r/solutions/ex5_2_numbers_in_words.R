# Exercise 5.2 - Numbers written in words
# Run from the root of the repository:  Rscript chapters/ch05/r/solutions/ex5_2_numbers_in_words.R

source("aie_r/evals.R")

number_words <- c(one = 1, two = 2, three = 3, four = 4, five = 5, six = 6,
                  seven = 7, eight = 8, nine = 9, ten = 10, eleven = 11,
                  twelve = 12)
numbers_in <- function(text) {
  for (w in names(number_words))
    text <- gsub(paste0("\\b", w, "\\b"), number_words[[w]], text,
                 ignore.case = TRUE, perl = TRUE)
  n <- regmatches(text, gregexpr("-?\\d[\\d,]*\\.?\\d*", text, perl = TRUE))[[1]]
  as.numeric(gsub(",", "", n))
}

cases <- read.csv("evals/sf_prospectus_qa.csv", colClasses = "character")
for (run in c("a", "b")) {
  cand <- read.csv(sprintf("evals/candidates/prospectus_qa_run_%s.csv", run),
                   colClasses = "character")
  res <- run_eval(cases, setNames(as.list(cand$answer), cand$id))
  cat(sprintf("Run %s: %d/%d passed; failures: %s\n", toupper(run), sum(res$passed),
              nrow(res), paste(res$id[!res$passed], collapse = ", ")))
}
