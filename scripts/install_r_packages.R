# Install the R packages of the book that are missing or older than the version the book was tested with,
# then check that each one loads. Run from the root of the repository:  Rscript scripts/install_r_packages.R
minimum <- c(httr2 = "1.0.0", jsonlite = "1.8.8", digest = "0.6.34",      # Chapters 3 to 11
             DBI = "1.2.2", RSQLite = "2.3.4", callr = "3.7.5",
             pdftools = "3.4.0",                                         # Chapter 16
             plumber = "1.2.1",                                          # Chapter 18
             shiny = "1.8.0", bslib = "0.6.1", DT = "0.31",              # Chapters 23 and 24
             sys = "3.4.2")                                              # the test model from R scripts
too_old <- function(p) !requireNamespace(p, quietly = TRUE) || packageVersion(p) < minimum[[p]]
todo <- names(minimum)[vapply(names(minimum), too_old, TRUE)]
if (length(todo)) {
  cat("Installing or updating:", paste(todo, collapse = ", "), "\n")
  install.packages(todo, repos = "https://cloud.r-project.org")
}
ok <- !vapply(names(minimum), too_old, TRUE)
for (p in names(minimum))
  cat(sprintf("  %-9s minimum %-7s installed %s\n", p, minimum[[p]],
              if (requireNamespace(p, quietly = TRUE)) as.character(packageVersion(p)) else "none"))
if (!all(ok)) stop("not installed or too old: ", paste(names(minimum)[!ok], collapse = ", "),
                   ". Read the messages above; on Linux, pdftools needs: sudo apt install libpoppler-cpp-dev",
                   call. = FALSE)
cat("All", length(minimum), "packages are installed, at the minimum version or later.\n")
