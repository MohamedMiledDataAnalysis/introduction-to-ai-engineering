# Exercise 15.2 - A positional check for the moderate scenario
# Run from the root of the repository:  Rscript chapters/ch15/r/solutions/ex15_2_positional_check.R

moderate_rhp_in_document <- function(document) {
  line <- grep("^\\| Moderate \\|", strsplit(document, "\n")[[1]], value = TRUE)
  if (!length(line)) return(NULL)
  cells <- regmatches(line, gregexpr("EUR [0-9,]+", line))[[1]]
  as.numeric(gsub("EUR |,", "", tail(cells, 1)))
}

for (code in c("hgef", "hecb", "hbma")) {
  document <- paste(readLines(sprintf("data/am/documents/%s_kid.md", code), encoding = "UTF-8"),
                    collapse = "\n")
  cat(toupper(code), moderate_rhp_in_document(document), "\n")
}
