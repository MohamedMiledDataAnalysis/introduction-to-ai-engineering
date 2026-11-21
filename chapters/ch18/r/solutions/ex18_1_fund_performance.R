# Exercise 18.1 - Test the fund performance endpoint
# Run from the root of the repository:  Rscript chapters/ch18/r/solutions/ex18_1_fund_performance.R

# starts the service of the exercise in the background, calls the endpoint twice, stops it
library(httr2)
svc <- callr::r_bg(function() plumber::pr_run(
  plumber::pr("services/solutions/ex18_1/plumber.R"), port = 8011))
on.exit(svc$kill())
call <- function(months) {
  for (i in 1:60) {                      # wait for the service to start
    r <- tryCatch(request("http://127.0.0.1:8011/tools/fund_performance") |>
      req_url_query(fund_code = "HGEF", months = months) |>
      req_headers(`x-api-key` = "dev-key-change-me") |>
      req_error(is_error = function(resp) FALSE) |> req_perform(), error = function(e) NULL)
    if (!is.null(r)) return(r)
    Sys.sleep(0.5)
  }
  stop("the service did not start")
}
for (m in c(12, 6)) {
  r <- call(m)
  cat("months =", m, "->", resp_status(r), resp_body_string(r), "\n")
}
svc$kill()
