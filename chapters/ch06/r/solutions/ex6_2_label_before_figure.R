# Exercise 6.2 - A figure must be named before it
# Run from the root of the repository:  Rscript chapters/ch06/r/solutions/ex6_2_label_before_figure.R

source("aie_r/factcheck.R")
cut <- "2026-09-30"
tape <- read.csv("data/sf/rmbs/larkfield_2025_1_loan_tape.csv")
wf <- read.csv("data/sf/rmbs/larkfield_2025_1_waterfall.csv")
notes <- read.csv("data/sf/rmbs/larkfield_2025_1_notes.csv")
sep <- tape[tape$RREL6 == cut, ]
w <- setNames(wf$paid[wf$cutoff == cut], wf$item[wf$cutoff == cut])
n <- notes[notes$cutoff == cut, ]; rownames(n) <- n$cls
pool <- sum(sep$RREL30)
fact <- function(value, unit, keys) list(value = value, unit = unit, keys = keys)
facts <- list(
  "revenue receipts" = fact(w[["Available revenue receipts"]], "money", "revenue"),
  "principal receipts" = fact(w[["Available principal receipts"]], "money", "principal"),
  "Class A principal paid" = fact(n["A", "principal_paid"], "money", c("class a", "repaid", "reducing")),
  "Class A closing balance" = fact(n["A", "closing"], "money", c("class a", "outstanding")),
  "pool balance" = fact(pool, "money", c("pool", "portfolio")),
  "arrears ratio" = fact(100 * sum(sep$RREL30[sep$RREL69 == "ARRE"]) / pool, "percent", "arrears"),
  "reserve fund balance" = fact(w[["Reserve fund closing balance"]], "money", "reserve"),
  "excess spread" = fact(w[["Excess spread released"]], "money", c("excess", "spread", "residual")))

check_text_labelled <- function(text, facts, window = 60) {
  figs <- extract_figures(text)
  lapply(seq_len(nrow(figs)), function(i) {
    f <- figs[i, ]
    context <- tolower(substr(text, max(1, f$start - window), f$start - 1))
    hits <- names(facts)[vapply(facts, function(x)
      figure_matches(f, x$value, x$unit) &&
        any(vapply(x$keys, grepl, TRUE, x = context, fixed = TRUE)), TRUE)]
    list(figure = f$raw, hits = hits)
  })
}

for (r in check_text_labelled("Revenue receipts were £4.88 million", facts))
  cat(r$figure, "->", if (length(r$hits)) r$hits else "no fact", "\n")
