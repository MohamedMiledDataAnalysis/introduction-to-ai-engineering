# Chapter 3 - Does the model give the same answer twice?
source("aie_r/llm.R")
prompt <- "In one short sentence, why do UK mortgage borrowers often redeem when their fixed rate ends?"

for (temperature in c(0, 1)) {
  answers <- vapply(1:5, function(i) {
    seed <- if (temperature == 0) 42 else sample.int(1e6, 1)
    trimws(chat(list(list(role = "user", content = prompt)),
                temperature = temperature, seed = seed)$text)
  }, "")
  cat(sprintf("Temperature %g: %d distinct answers out of 5\n", temperature, length(unique(answers))))
}
