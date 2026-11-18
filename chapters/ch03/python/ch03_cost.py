# Chapter 3 - What does a month of investor questions cost?
QUESTIONS_PER_MONTH = 500
INPUT_TOKENS = 2_500        # instructions + prospectus passages + question
OUTPUT_TOKENS = 300         # the answer

# Illustrative prices in USD per million tokens. Take the current prices from your provider's price page.
PRICES = {"small paid model": (1.00, 5.00), "large paid model": (3.00, 15.00)}

for name, (p_in, p_out) in PRICES.items():
    per_q = INPUT_TOKENS / 1e6 * p_in + OUTPUT_TOKENS / 1e6 * p_out
    print(f"{name:<18} per question: ${per_q:.4f}   per month: ${per_q * QUESTIONS_PER_MONTH:,.2f}"
          f"   per year: ${per_q * QUESTIONS_PER_MONTH * 12:,.2f}")
print("local model (Ollama) per question: $0 in fees; the cost is the hardware and its running time")
