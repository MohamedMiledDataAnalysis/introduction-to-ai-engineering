# Chapter 2 - A tiny next-word model built from the Larkfield prospectus
import math
import re
from collections import Counter, defaultdict

text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
            encoding="utf-8").read().lower()
words = re.findall(r"[a-z]+", text)
print("Words in the prospectus excerpt:", len(words))

# Count which word follows which (bigram counts)
follow = defaultdict(Counter)
for w1, w2 in zip(words, words[1:]):
    follow[w1][w2] += 1

context = "class"
counts = follow[context]
total = sum(counts.values())
print(f"\nWords that follow '{context}' ({total} occurrences):")
for word, c in counts.most_common(4):
    print(f"  {word:<10} {c:>3}   p = {c / total:.3f}")

# Temperature: divide the log-probabilities by T, then renormalise
def with_temperature(probs, t):
    logits = {w: math.log(p) / t for w, p in probs.items()}   # log-probability divided by T
    m = max(logits.values())
    expd = {w: math.exp(v - m) for w, v in logits.items()}   # back to the original scale
    s = sum(expd.values())
    return {w: v / s for w, v in expd.items()}                # rescale so the total is 1

probs = {w: c / total for w, c in counts.items()}
top = [w for w, _ in counts.most_common(4)]
print("\nProbability of the four most likely words at three temperatures:")
print(f"  {'word':<10}" + "".join(f"T={t:<8}" for t in (0.5, 1.0, 2.0)))
tables = {t: with_temperature(probs, t) for t in (0.5, 1.0, 2.0)}
for w in top:
    print(f"  {w:<10}" + "".join(f"{tables[t][w]:<10.3f}"
                                 for t in (0.5, 1.0, 2.0)))
