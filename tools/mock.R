# Start the mock model on a free port for a test, and point aie_r/llm.R at it.
#   source("tools/mock.R")
#   mock <- start_mock("tools/scripts/ch21_scenarios.json")
#   ...   # every chat() call reaches the mock, even while Ollama runs
#   stop_mock(mock)
python_cmd <- function() {
  for (p in c("python3", "python", "py")) if (nzchar(Sys.which(p))) return(p)   # Windows has python or py
  stop("Python not found: install it as in Chapter 0")
}

start_mock <- function(script = NULL, fail_first = 0) {
  port_file <- tempfile(fileext = ".port")
  env <- c(MOCK_PORT = "0", MOCK_PORT_FILE = port_file, MOCK_FAIL_FIRST = as.character(fail_first))
  if (!is.null(script)) env <- c(env, MOCK_SCRIPT = script)
  old <- Sys.getenv(names(env), unset = NA); do.call(Sys.setenv, as.list(env))
  pid <- sys::exec_background(python_cmd(), "tools/mock_ollama.py", std_out = FALSE, std_err = FALSE)
  for (n in names(old)) if (is.na(old[[n]])) Sys.unsetenv(n) else do.call(Sys.setenv, setNames(list(old[[n]]), n))
  deadline <- Sys.time() + 15; port <- NA
  while (Sys.time() < deadline) {              # wait until the mock has written its port and accepts calls
    if (is.na(port) && file.exists(port_file) && length(l <- readLines(port_file, warn = FALSE)) && nzchar(l[1]))
      port <- as.integer(l[1])
    if (!is.na(port)) {
      con <- tryCatch(suppressWarnings(socketConnection("127.0.0.1", port, open = "r+b", timeout = 1)),
                      error = function(e) NULL)
      if (!is.null(con)) { close(con); break }
    }
    Sys.sleep(0.05)
  }
  if (is.na(port)) { tools::pskill(pid); stop("the mock did not start within 15 seconds") }
  mock <- list(pid = pid, old_url = get0("ollama_url", envir = globalenv(), ifnotfound = NULL))
  assign("ollama_url", sprintf("http://localhost:%d", port), envir = globalenv())
  mock
}

stop_mock <- function(mock) {
  tools::pskill(mock$pid)
  if (!is.null(mock$old_url)) assign("ollama_url", mock$old_url, envir = globalenv())
  invisible(NULL)
}
