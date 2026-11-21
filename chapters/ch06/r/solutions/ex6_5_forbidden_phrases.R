# Exercise 6.5 - Two forbidden phrases from compliance
# Run from the root of the repository:  Rscript chapters/ch06/r/solutions/ex6_5_forbidden_phrases.R

source("aie_r/factcheck.R")
# the two patterns added to forbidden_patterns (here in memory; in aie_r/factcheck.R in the exercise)
forbidden_patterns <- c(forbidden_patterns,
  "\\bcapital[- ]protected\\b", "\\bcan('|no)?t lose\\b",
  NULL)
for (s in c("This fund is capital protected.",
            "The fund does not offer any capital protection.",
            "Investors can't lose more than they invest.",
            "You cannot lose money.", "A capital-protected note."))
  cat(paste(forbidden_phrases(s), collapse = ", "), "<-", s, "\n")
