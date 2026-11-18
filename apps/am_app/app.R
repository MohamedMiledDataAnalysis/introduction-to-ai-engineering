# Harbourline funds — the asset management application (Chapter 24)
# Run from the repository root:  Rscript -e 'shiny::runApp("apps/am_app", port = 8102)'
library(shiny); library(bslib); library(DT); library(jsonlite)
root <- normalizePath(Sys.getenv("AIE_ROOT", "../.."))
setwd(root)
source("aie_r/assistants.R"); source("aie_r/commentary.R")

service_url <- Sys.getenv("AIE_SERVICE_URL", "")
service_key <- Sys.getenv("AIE_API_KEY", "dev-key-change-me")
assistant <- new_assistant("am")
funds <- read.csv("data/am/funds.csv", stringsAsFactors = FALSE)
nav   <- read.csv("data/am/fund_nav_monthly.csv", stringsAsFactors = FALSE)
bm    <- read.csv("data/am/benchmark_returns_monthly.csv", stringsAsFactors = FALSE)
hold  <- read.csv("data/am/fund_holdings_monthly.csv", stringsAsFactors = FALSE)
tool  <- function(name, ...) fromJSON(run_tool(list(name = name, arguments = list(...))))
WARNING <- "Past performance does not predict future returns."

ask_agent <- function(question, history) {
  if (service_url == "") return(ask_assistant(assistant, question, history))
  resp <- tryCatch(httr2::request(paste0(service_url, "/am/ask")) |>
                     httr2::req_headers(`x-api-key` = service_key) |>
                     httr2::req_body_json(list(question = question)) |>
                     httr2::req_timeout(300) |> httr2::req_error(is_error = function(r) FALSE) |>
                     httr2::req_perform(), error = function(e) NULL)
  if (is.null(resp) || httr2::resp_status(resp) != 200)
    return(list(answer = "The assistant is unavailable; the fund figures on the other tabs remain available.",
                status = "error", trace = list(), unsupported = character(0)))
  b <- httr2::resp_body_json(resp)
  list(answer = b$answer, status = b$status, unsupported = unlist(b$unsupported),
       trace = lapply(unlist(b$tools_used), function(t) list(name = t, arguments = NULL, result = "")))
}
status_badge <- function(status) {
  colour <- switch(status, verified = "success", declined = "dark", needs_review = "warning", "danger")
  span(class = paste0("badge text-bg-", colour), status)
}

ui <- page_navbar(
  title = "Harbourline funds", fillable = FALSE, theme = bs_theme(version = 5, primary = "#1F2A44", secondary = "#C9A227"),
  sidebar = sidebar(selectInput("fund", "Fund", setNames(funds$fund_code, paste(funds$fund_code, "-", funds$name))),
                    radioButtons("months", "Period", c("1 year" = 12, "3 years" = 36), inline = TRUE), width = 260),
  nav_panel("Performance",
    layout_columns(value_box("Fund return", textOutput("kpi_fund")), value_box("Benchmark", textOutput("kpi_bench")),
                   value_box("Relative", textOutput("kpi_rel")), value_box("Ongoing charges", textOutput("kpi_ocf"))),
    card(card_header("Growth of 100 (net of fees) against the benchmark"), plotOutput("growth", height = 260),
         card_footer(WARNING))),
  nav_panel("Portfolio",
    layout_columns(card(card_header("Top ten holdings, 30 September 2026"), tableOutput("top")),
                   card(card_header("Characteristics"), tableOutput("chars")))),
  nav_panel("Attribution",
    card(card_header("HGEF, September 2026: Brinson attribution (basis points)"), tableOutput("attr")),
    card(card_header("Draft commentary and its fact check"), textOutput("draft"), br(), tableOutput("check"))),
  nav_panel("Assistant",
    layout_columns(col_widths = c(4, 8),
      card(textAreaInput("question", "Question", rows = 4, placeholder = "e.g. What are the ongoing costs of HECB?"),
           actionButton("ask", "Ask", class = "btn-primary"),
           helpText(if (service_url == "") "Mode: R agent inside the app" else paste("Mode: service at", service_url)),
           helpText("The assistant gives information, not investment advice.")),
      uiOutput("conversation")))
)

server <- function(input, output, session) {
  setwd(root)                     # runApp() sets the working directory to the app folder; the aie_r code reads from the root
  perf <- reactive(tool("fund_performance", fund_code = input$fund, months = as.integer(input$months)))
  output$kpi_fund  <- renderText(sprintf("%.2f%%", perf()$fund_return_pct))
  output$kpi_bench <- renderText(sprintf("%.2f%%", perf()$benchmark_return_pct))
  output$kpi_rel   <- renderText(sprintf("%+.2f%%", perf()$relative_return_pct))
  output$kpi_ocf   <- renderText(sprintf("%.2f%%", 100 * funds$ocf[funds$fund_code == input$fund]))
  output$growth <- renderPlot({
    n <- as.integer(input$months)
    f <- tail(nav[nav$fund_code == input$fund, ], n); b <- tail(bm[, c("month_end", input$fund)], n)
    d <- as.Date(f$month_end); gf <- 100 * cumprod(1 + f$net_return); gb <- 100 * cumprod(1 + b[[2]])
    par(mar = c(3, 4, 1, 1))
    plot(d, gf, type = "l", lwd = 3, col = "#1F2A44", ylim = range(c(gf, gb, 100)), xlab = "", ylab = "Growth of 100")
    lines(d, gb, lwd = 2, col = "#C9A227", lty = 2); abline(h = 100, col = "grey70")
    legend("topleft", c(input$fund, "Benchmark"), col = c("#1F2A44", "#C9A227"), lwd = c(3, 2), lty = c(1, 2), bty = "n")
  })
  output$top <- renderTable(tool("top_holdings", fund_code = input$fund, n = 10L)$holdings)
  output$chars <- renderTable({
    ch <- tool("fund_characteristics", fund_code = input$fund); ch$top_sectors <- NULL
    data.frame(Measure = gsub("_", " ", names(ch)), Value = vapply(ch, function(v) format(v), ""))
  })
  hf <- hgef_facts("2026-09-30")
  output$attr <- renderTable({
    a <- hf$attr
    data.frame(Sector = a$sector, `Fund weight` = sprintf("%.2f%%", 100 * a$portfolio_weight),
               `Benchmark weight` = sprintf("%.2f%%", 100 * a$benchmark_weight),
               Allocation = sprintf("%+.1f", 1e4 * a$allocation), Selection = sprintf("%+.1f", 1e4 * a$selection),
               Interaction = sprintf("%+.1f", 1e4 * a$interaction), Total = sprintf("%+.1f", 1e4 * a$total), check.names = FALSE)
  })
  drafts <- trimws(strsplit(paste(readLines("evals/drafts/hgef_commentary_2026_09.txt", warn = FALSE),
                                   collapse = " "), "DRAFT [0-9]+")[[1]])
  drafts <- drafts[nchar(drafts) > 0]
  draft <- drafts[2]                                   # the second draft has two errors for the checker to find
  output$draft <- renderText(draft)
  output$check <- renderTable({
    r <- check_commentary(draft, hf$facts)
    data.frame(Figure = vapply(r, `[[`, "", "raw"),
               Matched = vapply(r, function(x) paste(x$hits, collapse = "; "), ""),
               Result = vapply(r, function(x) if (is.na(x$problem)) "OK" else x$problem, ""))
  })

  history <- reactiveVal(list()); log <- reactiveVal(list())
  observeEvent(input$ask, {
    req(nchar(input$question) >= 3)
    r <- withProgress(message = "The assistant is working", ask_agent(input$question, history()))
    history(c(history(), list(list(role = "user", content = input$question),
                              list(role = "assistant", content = r$answer))))
    log(c(list(list(q = input$question, r = r)), log()))
    updateTextAreaInput(session, "question", value = "")
  })
  output$conversation <- renderUI({
    lapply(log(), function(x) card(
      card_header(x$q), p(x$r$answer),
      div(status_badge(x$r$status),
          if (length(x$r$unsupported)) span(class = "text-danger", paste(" Unsupported:", paste(x$r$unsupported, collapse = ", ")))),
      if (length(x$r$trace)) tags$details(tags$summary("Trace"),
        tags$ul(lapply(x$r$trace, function(t) tags$li(code(t$name), " ", substr(t$result, 1, 160)))))))
  })
}

shinyApp(ui, server)
