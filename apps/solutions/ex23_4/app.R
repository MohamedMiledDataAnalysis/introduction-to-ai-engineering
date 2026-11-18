# Exercise 23.4 - the SF application with a review queue for answers that need review
# Run from the repository root:  Rscript -e 'shiny::runApp("apps/solutions/ex23_4", port = 8114)'
library(shiny); library(bslib); library(DT)
root <- normalizePath(Sys.getenv("AIE_ROOT", "../../.."))   # runApp starts in apps/solutions/ex23_4; work from the repository root
setwd(root)
source("aie_r/assistants.R"); source("aie_r/investor_report.R"); source("aie_r/dq.R"); source("aie_r/dq_email.R")

service_url <- Sys.getenv("AIE_SERVICE_URL", "")          # empty: the R agent runs inside the app
service_key <- Sys.getenv("AIE_API_KEY", "dev-key-change-me")
assistant <- new_assistant("sf")
tape  <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv", stringsAsFactors = FALSE)
dates <- sort(unique(tape$RREL6))[-1]                       # collection period ends (no report at closing)
gbp <- function(x, d = 2) paste0("£", formatC(x, format = "f", digits = d, big.mark = ","))

ask_agent <- function(question, history) {
  if (service_url == "") return(ask_assistant(assistant, question, history))
  resp <- tryCatch(httr2::request(paste0(service_url, "/sf/ask")) |>
                     httr2::req_headers(`x-api-key` = service_key) |>
                     httr2::req_body_json(list(question = question)) |>
                     httr2::req_timeout(300) |> httr2::req_error(is_error = function(r) FALSE) |>
                     httr2::req_perform(), error = function(e) NULL)
  if (is.null(resp) || httr2::resp_status(resp) != 200)
    return(list(answer = "The assistant is unavailable; the figures on the dashboard remain available.",
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
  title = "Larkfield 2025-1", fillable = FALSE, theme = bs_theme(version = 5, primary = "#1F2A44", secondary = "#C9A227"),
  nav_panel("Dashboard",
    layout_sidebar(
      sidebar = sidebar(selectInput("date", "Collection period ending", rev(dates)), width = 230),
      layout_columns(
        value_box("Pool balance", textOutput("kpi_pool")), value_box("Arrears ratio", textOutput("kpi_arrears")),
        value_box("CPR (annualised)", textOutput("kpi_cpr")), value_box("Class A balance", textOutput("kpi_classa"))),
      card(card_header("Arrears ratio and CPR since closing"), plotOutput("trend", height = 260)),
      card(card_header("Reconciliations"), tableOutput("recon")),
      card(card_header("Notes"), tableOutput("notes")))),
  nav_panel("Data quality",
    card(card_header("Received tape for 30 September 2026: rule breaches"), DTOutput("dq")),
    card(card_header("Query to the servicer"),
         actionButton("draft", "Draft with the model"), br(), br(),
         verbatimTextOutput("email"), textOutput("email_check"))),
  nav_panel("Assistant",
    layout_sidebar(
      sidebar = sidebar(width = 300,
        textAreaInput("question", "Question", rows = 4, placeholder = "e.g. Can the reserve fund repay principal?"),
        actionButton("ask", "Ask", class = "btn-primary"),
        helpText(if (service_url == "") "Mode: R agent inside the app" else paste("Mode: service at", service_url))),
      uiOutput("conversation"))),
  nav_panel("Investor report",
    layout_sidebar(sidebar = sidebar(selectInput("rdate", "Collection period ending", rev(dates)),
                                     downloadButton("download", "Download report (.md)"), width = 260),
                   card(card_header("Commentary (template; checked)"), textOutput("commentary")),
                   card(card_header("Arrears"), tableOutput("buckets"))))
)

server <- function(input, output, session) {
  setwd(root)                     # runApp() sets the working directory to the app folder; the aie_r code reads from the root
  figures <- reactive(month_figures(input$date))
  output$kpi_pool    <- renderText(gbp(figures()$pool / 1e6, 2) |> paste0("m"))
  output$kpi_arrears <- renderText(sprintf("%.2f%%", figures()$arrears_ratio))
  output$kpi_cpr     <- renderText(sprintf("%.1f%%", figures()$cpr))
  output$kpi_classa  <- renderText(gbp(figures()$notes["A", "closing"] / 1e6, 2) |> paste0("m"))
  series <- reactive({
    s <- lapply(dates, function(d) { f <- month_figures(d); c(f$arrears_ratio, f$cpr) })
    data.frame(date = as.Date(dates), arrears = sapply(s, `[`, 1), cpr = sapply(s, `[`, 2))
  }) |> bindCache("series")
  output$trend <- renderPlot({
    s <- series(); par(mar = c(3, 4, 1, 4))
    plot(s$date, s$arrears, type = "l", lwd = 3, col = "#1F2A44", ylab = "Arrears ratio (%)", xlab = "", ylim = c(0, 2))
    par(new = TRUE)
    plot(s$date, s$cpr, type = "l", lwd = 2, col = "#C9A227", axes = FALSE, xlab = "", ylab = "", ylim = c(0, 20))
    axis(4); mtext("CPR (%)", side = 4, line = 2.5)
    legend("bottomright", c("Arrears ratio (left)", "CPR (right)"), col = c("#1F2A44", "#C9A227"), lwd = c(3, 2), bty = "n", horiz = TRUE)
  })
  output$recon <- renderTable({
    r <- reconcile(figures()); data.frame(Check = names(r), Result = ifelse(r, "PASS", "FAIL"))
  })
  output$notes <- renderTable({
    n <- figures()$notes
    data.frame(Class = n$cls, Opening = gbp(n$opening), `Principal paid` = gbp(n$principal_paid),
               Closing = gbp(n$closing), Coupon = sprintf("%.2f%%", n$coupon_pct), check.names = FALSE)
  })

  received <- read.csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv", stringsAsFactors = FALSE)
  flags <- run_rules(received, "2026-09-30")
  output$dq <- renderDT(datatable(flags, rownames = FALSE, options = list(pageLength = 12, dom = "tp")))
  email <- reactiveVal(template_email(flags, "30 September 2026", "7 October 2026"))
  observeEvent(input$draft, {
    d <- tryCatch(draft_email(flags, "30 September 2026", "7 October 2026")$email, error = function(e) NULL)
    if (!is.null(d) && length(check_email(d, flags)) == 0) email(d)
    else showNotification("The draft was unavailable or failed its check; the template is shown.", type = "warning")
  })
  output$email <- renderText(email())
  output$email_check <- renderText({
    p <- check_email(email(), flags)
    if (length(p)) paste("Check:", paste(p, collapse = "; ")) else "Check: every flagged loan listed exactly once."
  })

  history <- reactiveVal(list()); log <- reactiveVal(list())
  observeEvent(input$ask, {
    req(nchar(input$question) >= 3)
    r <- withProgress(message = "The assistant is working", ask_agent(input$question, history()))
    history(c(history(), list(list(role = "user", content = input$question),
                              list(role = "assistant", content = r$answer))))
    log(c(list(list(q = input$question, r = r)), log()))
    if (identical(r$status, "needs_review")) {
      dir.create("logs", showWarnings = FALSE)
      row <- data.frame(time = format(Sys.time(), "%Y-%m-%dT%H:%M:%S"), question = input$question,
                        answer = r$answer, unsupported = paste(r$unsupported, collapse = "; "))
      f <- "logs/review_queue.csv"
      write.table(row, f, sep = ",", row.names = FALSE, col.names = !file.exists(f), append = file.exists(f))
    }
    updateTextAreaInput(session, "question", value = "")
  })
  output$conversation <- renderUI({
    lapply(log(), function(x) card(
      card_header(x$q),
      p(x$r$answer), div(status_badge(x$r$status),
        if (length(x$r$unsupported)) span(class = "text-danger", paste(" Unsupported:", paste(x$r$unsupported, collapse = ", ")))),
      if (length(x$r$trace)) tags$details(tags$summary("Trace"),
        tags$ul(lapply(x$r$trace, function(t) tags$li(code(t$name), " ", substr(t$result, 1, 160)))))))
  })

  rfig <- reactive(month_figures(input$rdate))
  output$commentary <- renderText(template_commentary(rfig()))
  output$buckets <- renderTable(transform(rfig()$buckets, balance = gbp(balance)))
  output$download <- downloadHandler(
    filename = function() sprintf("larkfield_investor_report_%s.md", gsub("-", "_", substr(input$rdate, 1, 7))),
    content = function(file) {
      f <- rfig(); n <- f$notes
      writeLines(c("# Larkfield Mortgage Funding 2025-1 PLC — Investor report", "",
                   paste("Collection period ending", f$cutoff, "(paid on the 20th of the following month)"), "", "## Commentary", "", template_commentary(f), "",
                   "## Notes", "", "| Class | Opening | Principal paid | Closing |", "|---|---:|---:|---:|",
                   sprintf("| %s | %s | %s | %s |", n$cls, gbp(n$opening), gbp(n$principal_paid), gbp(n$closing))), file)
    })
}

shinyApp(ui, server)
