# Every script printed in solutions/*.md under a file path must be the same code as that file.
# Run from the root of the repository:  Rscript tests/test_solutions_files.R
problems <- 0; checked <- 0
for (md in sort(Sys.glob("solutions/ch*_corrections.md"))) {
  text <- paste(readLines(md, encoding = "UTF-8", warn = FALSE), collapse = "\n")
  pat <- "(?ms)^`((?:chapters|aie|aie_r|apps|services|tests)/[^`]+\\.(?:py|R))`\n\n``` \\w+\n(.*?)\n```$"
  hits <- regmatches(text, gregexpr(pat, text, perl = TRUE))[[1]]
  for (h in hits) {
    path <- sub(pat, "\\1", h, perl = TRUE); code <- sub(pat, "\\2", h, perl = TRUE)
    lines <- readLines(path, encoding = "UTF-8", warn = FALSE)
    i <- 1
    if (!startsWith(code, "#")) {                                    # listing printed without the file's title comment
      while (i <= length(lines) && startsWith(lines[i], "#")) i <- i + 1
      while (i <= length(lines) && trimws(lines[i]) == "") i <- i + 1
    }
    checked <- checked + 1
    if (paste(lines[i:length(lines)], collapse = "\n") != code) {
      cat("DIFFERS", basename(md), path, "\n"); problems <- problems + 1
    }
  }
}
cat(checked, "scripts checked against solutions/:",
    if (problems == 0) "all identical" else paste(problems, "differ"), "\n")
stopifnot(problems == 0)
