# Exercise 3.4 - Ask one section of the prospectus
# Run from the root of the repository:  Rscript chapters/ch03/r/solutions/ex3_4_ask_section.R

source("aie_r/llm.R")
prospectus <- paste(readLines(
  "data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
  encoding = "UTF-8"), collapse = "\n")
parts <- strsplit(prospectus, "\n## ", fixed = TRUE)[[1]][-1]
sections <- setNames(parts, sub("\n.*", "", parts))

ask_section <- function(section_title, question) {
  if (!section_title %in% names(sections))
    stop("no section titled '", section_title, "'")
  reply <- chat(
    system = paste("Answer only from the text provided. If the text does",
                   "not contain the answer, say so."),
    messages = list(list(role = "user", content = paste0(
      "TEXT:\n", sections[[section_title]], "\n\nQUESTION: ", question))))
  trimws(reply$text)
}
cat(ask_section("3. Reserve fund",
                "What is the Reserve Fund Required Amount?"), "\n")
