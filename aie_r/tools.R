# Tools: R functions a model may ask to run, described by JSON schemas.
library(jsonlite)
source("aie_r/validate.R")

.cache <- new.env()
.load <- function(name, path) {
  if (is.null(.cache[[name]])) .cache[[name]] <- read.csv(path, stringsAsFactors = FALSE)
  .cache[[name]]
}
.check_date <- function(date, available) {
  if (!date %in% available)
    stop(sprintf("no data for %s; available month-ends run from %s to %s", date, min(available), max(available)))
}

pool_summary <- function(cutoff_date) {
  t <- .load("tape", "data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
  .check_date(cutoff_date, t$RREL6)
  m <- t[t$RREL6 == cutoff_date, ]
  pool <- sum(m$RREL30); arrears <- sum(m$RREL30[m$RREL69 == "ARRE"])
  list(cutoff_date = cutoff_date, pool_balance_gbp = round(pool, 2), loans_outstanding = sum(m$RREL30 > 0),
       arrears_balance_gbp = round(arrears, 2), arrears_ratio_pct = round(100 * arrears / pool, 4),
       defaulted_loans_to_date = sum(m$RREL69 == "DFLT"))
}

note_balance <- function(note_class, cutoff_date) {
  n <- .load("notes", "data/sf/rmbs/larkfield_2025_1_notes.csv")
  .check_date(cutoff_date, n$cutoff)
  r <- n[n$cutoff == cutoff_date & n$cls == note_class, ]
  if (nrow(r) == 0) stop("unknown class ", note_class, "; classes are A, B, C, D")
  list(class = note_class, cutoff_date = cutoff_date, opening_gbp = round(r$opening, 2),
       principal_paid_gbp = round(r$principal_paid, 2), interest_paid_gbp = round(r$interest_paid, 2),
       closing_gbp = round(r$closing, 2), coupon_pct = r$coupon_pct)
}

waterfall_summary <- function(cutoff_date) {
  w <- .load("wf", "data/sf/rmbs/larkfield_2025_1_waterfall.csv")
  .check_date(cutoff_date, w$cutoff)
  m <- w[w$cutoff == cutoff_date & w$waterfall == "Summary", ]
  names_map <- c("Available revenue receipts" = "revenue_receipts_gbp",
                 "Available principal receipts" = "principal_receipts_gbp",
                 "New defaults debited to PDL" = "new_defaults_gbp",
                 "Reserve fund closing balance" = "reserve_fund_balance_gbp",
                 "Excess spread released" = "excess_spread_gbp")
  c(list(cutoff_date = cutoff_date), setNames(as.list(round(m$paid, 2)), unname(names_map[m$item])))
}

fund_performance <- function(fund_code, months) {
  nav <- .load("nav", "data/am/fund_nav_monthly.csv"); bm <- .load("bm", "data/am/benchmark_returns_monthly.csv")
  f <- nav[nav$fund_code == fund_code, ]
  if (nrow(f) == 0) stop("unknown fund ", fund_code, "; funds are HGEF, HECB, HBMA")
  if (!months %in% c(1, 3, 12, 36)) stop("months must be 1, 3, 12 or 36")
  fr <- prod(1 + tail(f$net_return, months)) - 1
  br <- prod(1 + tail(bm[[fund_code]], months)) - 1
  list(fund_code = fund_code, period_months = months, period_end = tail(f$month_end, 1),
       fund_return_pct = round(100 * fr, 4), benchmark_return_pct = round(100 * br, 4),
       relative_return_pct = round(100 * (fr - br), 4))
}

top_holdings <- function(fund_code, n = 10) {
  h <- .load("hold", "data/am/fund_holdings_monthly.csv")
  last <- max(h$month_end)
  m <- h[h$fund_code == fund_code & h$month_end == last & h$isin != "CASH-EUR", ]
  if (nrow(m) == 0) stop("unknown fund ", fund_code, "; funds are HGEF, HECB, HBMA")
  m <- head(m[order(-m$weight), ], n)
  list(fund_code = fund_code, as_of = last,
       holdings = lapply(seq_len(nrow(m)), function(i)
         list(name = m$name[i], sector = m$sector[i], weight_pct = round(100 * m$weight[i], 2))))
}

date_rule <- list(type = "string", pattern = "20[0-9]{2}-[0-9]{2}-[0-9]{2}")
registry <- list(
  pool_summary = list(fn = pool_summary, description = "Pool balance, loans outstanding, arrears balance and ratio of the Larkfield 2025-1 mortgage pool at a month-end cut-off date.",
    parameters = list(type = "object", properties = list(cutoff_date = date_rule), required = list("cutoff_date"), additionalProperties = FALSE)),
  note_balance = list(fn = note_balance, description = "Opening and closing balance, principal and interest paid, and coupon of one class of Larkfield 2025-1 notes at a month-end.",
    parameters = list(type = "object", properties = list(note_class = list(type = "string", enum = list("A", "B", "C", "D")), cutoff_date = date_rule),
                      required = list("note_class", "cutoff_date"), additionalProperties = FALSE)),
  waterfall_summary = list(fn = waterfall_summary, description = "Revenue and principal receipts, new defaults, reserve fund balance and excess spread of Larkfield 2025-1 for one collection period, named by its end date.",
    parameters = list(type = "object", properties = list(cutoff_date = date_rule), required = list("cutoff_date"), additionalProperties = FALSE)),
  fund_performance = list(fn = fund_performance, description = "Net return of a Harbourline fund and of its benchmark over the last 1, 3, 12 or 36 months to the latest month-end.",
    parameters = list(type = "object", properties = list(fund_code = list(type = "string", enum = list("HGEF", "HECB", "HBMA")),
                      months = list(type = "integer", enum = list(1L, 3L, 12L, 36L))), required = list("fund_code", "months"), additionalProperties = FALSE)),
  top_holdings = list(fn = top_holdings, description = "The largest holdings of a Harbourline fund at the latest month-end.",
    parameters = list(type = "object", properties = list(fund_code = list(type = "string", enum = list("HGEF", "HECB", "HBMA")),
                      n = list(type = "integer", minimum = 1)), required = list("fund_code"), additionalProperties = FALSE))
)

tool_specs <- function(names = NULL) {
  if (is.null(names)) names <- names(registry)
  lapply(names, function(n) list(type = "function", `function` = list(
    name = n, description = registry[[n]]$description, parameters = registry[[n]]$parameters)))
}

run_tool <- function(call, allowed = NULL) {
  name <- call$name; args <- call$arguments
  if (is.null(args)) args <- list()
  if (is.character(args)) args <- fromJSON(args, simplifyVector = FALSE)
  if (is.null(name) || !name %in% names(registry) || (!is.null(allowed) && !name %in% allowed))
    return(toJSON(list(error = paste("unknown tool", name)), auto_unbox = TRUE))
  problems <- validate(args, registry[[name]]$parameters)
  if (length(problems)) return(toJSON(list(error = paste("invalid arguments:", paste(problems, collapse = "; "))), auto_unbox = TRUE))
  tryCatch(toJSON(do.call(registry[[name]]$fn, args), auto_unbox = TRUE, digits = NA),
           error = function(e) toJSON(list(error = conditionMessage(e)), auto_unbox = TRUE))
}

search_prospectus <- function(query, k = 3) {
  if (is.null(.cache$pidx)) {
    source("aie_r/retrieval.R", local = TRUE)
    text <- paste(readLines("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md", encoding = "UTF-8"), collapse = "\n")
    .cache$pidx <- bm25_index(chunk_markdown(text, "LMF"))
    .cache$search <- bm25_search
  }
  res <- .cache$search(.cache$pidx, query, k)
  list(query = query, passages = lapply(res, function(r) list(id = r$chunk$id, text = r$chunk$text)))
}
registry$search_prospectus <- list(fn = search_prospectus,
  description = paste("Search the Larkfield 2025-1 prospectus excerpt and return the most relevant passages with",
                      "their identifiers (for example LMF#3). Use it for definitions, rules, fees, triggers and",
                      "the priority of payments. Cite the identifiers in your answer."),
  parameters = list(type = "object", properties = list(query = list(type = "string"), k = list(type = "integer", minimum = 1)),
                    required = list("query"), additionalProperties = FALSE))

# ---------------- added for the final project ----------------
arrears_buckets <- function(cutoff_date) {
  t <- .load("tape", "data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
  .check_date(cutoff_date, t$RREL6)
  m <- t[t$RREL6 == cutoff_date & t$RREL69 == "ARRE", ]
  months <- pmin(m$RREL68 %/% 30, 4)
  labels <- c("1 month", "2 months", "3 months", "4-5 months")
  list(cutoff_date = cutoff_date, buckets = lapply(1:4, function(k)
    list(bucket = labels[k], loans = sum(months == k), balance_gbp = round(sum(m$RREL30[months == k]), 2))))
}

.fund_docs <- function() {
  if (is.null(.cache$fund_docs)) {
    source("aie_r/retrieval.R", local = TRUE)
    chunks <- list()
    add <- function(text, code, kind) {
      for (c in chunk_markdown(text, paste0(code, "-", kind))) {
        c$fund <- code; c$id <- paste0(code, "-", kind, "#", length(chunks) + 1)
        chunks[[length(chunks) + 1]] <<- c
      }
    }
    for (code in c("HGEF", "HECB", "HBMA")) {
      lc <- tolower(code)
      add(paste(readLines(sprintf("data/am/documents/%s_kid.md", lc), encoding = "UTF-8"), collapse = "\n"), code, "KID")
      add(paste(readLines(sprintf("data/am/documents/%s_factsheet_2026_09.md", lc), encoding = "UTF-8"), collapse = "\n"), code, "factsheet")
    }
    add(paste(readLines("data/am/documents/hgef_sfdr_periodic_2026.md", encoding = "UTF-8"), collapse = "\n"), "HGEF", "SFDR")
    # key facts before the first '## ' section: one chunk per factsheet and for the SFDR disclosure
    heads <- list(c("HGEF", "factsheet", "data/am/documents/hgef_factsheet_2026_09.md"),
                  c("HECB", "factsheet", "data/am/documents/hecb_factsheet_2026_09.md"),
                  c("HBMA", "factsheet", "data/am/documents/hbma_factsheet_2026_09.md"),
                  c("HGEF", "SFDR", "data/am/documents/hgef_sfdr_periodic_2026.md"))
    for (h in heads) {
      lines <- readLines(h[3], encoding = "UTF-8")
      first <- which(startsWith(lines, "## "))[1]
      lines <- lines[seq_len(first - 1)]
      lines <- lines[nzchar(trimws(lines)) & !startsWith(lines, ">")]
      text <- paste(c("Key facts", trimws(sub("^#+ ", "", lines[1])), lines[-1]), collapse = "\n")
      chunks[[length(chunks) + 1]] <- list(id = paste0(h[1], "-", h[2], "#", length(chunks) + 1),
                                           title = "Key facts", text = text, fund = h[1])
    }
    .cache$fund_docs <- chunks; .cache$bm25_index <- bm25_index; .cache$bm25_search <- bm25_search
  }
  .cache$fund_docs
}

search_fund_documents <- function(query, fund_code, k = 3) {
  chunks <- Filter(function(c) c$fund == fund_code, .fund_docs())     # filter by fund first (Chapter 7)
  if (!length(chunks)) stop("unknown fund ", fund_code, "; funds are HGEF, HECB, HBMA")
  res <- .cache$bm25_search(.cache$bm25_index(chunks), query, k)
  list(fund_code = fund_code, passages = lapply(res, function(r) list(id = r$chunk$id, text = r$chunk$text)))
}

fund_characteristics <- function(fund_code) {
  h <- .load("hold", "data/am/fund_holdings_monthly.csv"); last <- max(h$month_end)
  m <- h[h$fund_code == fund_code & h$month_end == last, ]
  if (nrow(m) == 0) stop("unknown fund ", fund_code, "; funds are HGEF, HECB, HBMA")
  sec <- .load("sec", "data/am/security_master.csv"); esg <- .load("esg", "data/am/issuer_esg.csv")
  x <- merge(m[m$isin != "CASH-EUR", ], sec[, c("isin", "issuer", "modified_duration", "rating")], by = "isin", all.x = TRUE)
  x$issuer_key <- ifelse(is.na(x$issuer) | x$issuer == "", x$name, x$issuer)
  x <- merge(x, esg[, c("issuer", "esg_score", "carbon_intensity_tco2e_per_eur_m")], by.x = "issuer_key", by.y = "issuer", all.x = TRUE)
  w <- x$weight / sum(x$weight)
  sect <- sort(tapply(m$weight, m$sector, sum), decreasing = TRUE)[1:3]
  out <- list(fund_code = fund_code, as_of = last, holdings = nrow(x),
              cash_weight_pct = round(100 * sum(m$weight[m$isin == "CASH-EUR"]), 2),
              weighted_esg_score = round(sum(w * x$esg_score), 1),
              weighted_carbon_intensity = round(sum(w * x$carbon_intensity_tco2e_per_eur_m), 1),
              top_sectors = lapply(names(sect), function(s) list(sector = s, weight_pct = round(100 * sect[[s]], 2))))
  b <- x[!is.na(x$modified_duration), ]
  if (nrow(b)) {
    bw <- b$weight / sum(b$weight)
    out$bond_modified_duration_years <- round(sum(bw * b$modified_duration), 2)
    out$bbb_share_of_bonds_pct <- round(100 * sum(bw[startsWith(b$rating, "BBB")]), 2)
  }
  out
}

registry$arrears_buckets <- list(fn = arrears_buckets,
  description = paste("Number of loans and current balance of the Larkfield 2025-1 loans in arrears at a month-end, by",
                      "months in arrears: 1, 2, 3, and 4 to 5. Defaulted loans (6 months or more) are not included."),
  parameters = list(type = "object", properties = list(cutoff_date = date_rule), required = list("cutoff_date"),
                    additionalProperties = FALSE))
fund_enum <- list(type = "string", enum = list("HGEF", "HECB", "HBMA"))
registry$search_fund_documents <- list(fn = search_fund_documents,
  description = paste("Search the Key Information Document, the September 2026 factsheet and, for HGEF, the SFDR periodic",
                      "disclosure of ONE Harbourline fund. Returns passages with identifiers to cite."),
  parameters = list(type = "object", properties = list(query = list(type = "string"), fund_code = fund_enum,
                    k = list(type = "integer", minimum = 1)), required = list("query", "fund_code"), additionalProperties = FALSE))
registry$fund_characteristics <- list(fn = fund_characteristics,
  description = paste("Portfolio characteristics of a Harbourline fund at the latest month-end: holdings, cash weight,",
                      "weighted ESG score and carbon intensity, top three sectors, bond duration and BBB share."),
  parameters = list(type = "object", properties = list(fund_code = fund_enum), required = list("fund_code"),
                    additionalProperties = FALSE))
