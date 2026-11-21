# Install the R packages of the book that are not installed yet, then check that each one loads.
# Run once, from the root of the repository:  Rscript scripts/install_r_packages.R
packages <- c("httr2", "jsonlite", "digest", "DBI", "RSQLite", "callr",   # Chapters 3 to 11
              "pdftools",                                                # Chapter 16
              "plumber",                                                 # Chapter 18
              "shiny", "bslib", "DT",                                    # Chapters 23 and 24
              "sys")                                                     # the test model from R scripts
installed <- vapply(packages, requireNamespace, TRUE, quietly = TRUE)
if (any(!installed)) {
  cat("Installing:", paste(packages[!installed], collapse = ", "), "\n")
  install.packages(packages[!installed], repos = "https://cloud.r-project.org")
}
ok <- vapply(packages, requireNamespace, TRUE, quietly = TRUE)
for (p in packages)
  cat(sprintf("  %-9s %s\n", p, if (ok[[p]]) as.character(packageVersion(p)) else "NOT INSTALLED"))
if (!all(ok)) stop("some packages could not be installed: see the messages above", call. = FALSE)
cat("All", length(packages), "packages are installed.\n")
