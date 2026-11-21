# Exercise 3.1 - Cost of the larger scenario
# Run from the root of the repository:  python chapters/ch03/python/solutions/ex3_1_cost_scenario.py

QUESTIONS_PER_MONTH = 2_000
INPUT_TOKENS = 6_000
OUTPUT_TOKENS = 500

# Illustrative prices in USD per million tokens. Take the current prices from your provider's price page.
PRICES = {"small paid model": (1.00, 5.00), "large paid model": (3.00, 15.00)}

for name, (p_in, p_out) in PRICES.items():
    per_q = INPUT_TOKENS / 1e6 * p_in + OUTPUT_TOKENS / 1e6 * p_out
    print(f"{name:<18} per question: ${per_q:.4f}   per month: ${per_q * QUESTIONS_PER_MONTH:,.2f}"
          f"   per year: ${per_q * QUESTIONS_PER_MONTH * 12:,.2f}")
print("local model (Ollama) per question: $0 in fees; the cost is the hardware and its running time")
