# Chapter 3 - What does a month of investor questions cost?
questions_per_month <- 500
input_tokens  <- 2500       # instructions + prospectus passages + question
output_tokens <- 300        # the answer

# Illustrative prices in USD per million tokens. Take the current prices from your provider's price page.
prices <- list(`small paid model` = c(1.00, 5.00), `large paid model` = c(3.00, 15.00))

for (name in names(prices)) {
  p <- prices[[name]]
  per_q <- input_tokens / 1e6 * p[1] + output_tokens / 1e6 * p[2]
  cat(sprintf("%-18s per question: $%.4f   per month: $%s   per year: $%s\n", name, per_q,
              formatC(per_q * questions_per_month, format = "f", digits = 2, big.mark = ","),
              formatC(per_q * questions_per_month * 12, format = "f", digits = 2, big.mark = ",")))
}
cat("local model (Ollama) per question: $0 in fees; the cost is the hardware and its running time\n")
