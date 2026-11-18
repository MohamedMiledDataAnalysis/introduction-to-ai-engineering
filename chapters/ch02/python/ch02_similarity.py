# Chapter 2 - Which section of the prospectus is closest to a question?
# Bag-of-words vectors weighted by TF-IDF, compared with cosine similarity.
import math
import re
from collections import Counter

text = open("data/sf/rmbs/larkfield_2025_1_prospectus_excerpt.md",
            encoding="utf-8").read()
sections = re.split(r"\n## ", text)[1:]      # one string per section
titles = [s.split("\n")[0] for s in sections]

STOP = {"the", "of", "to", "and", "a", "in", "on", "is", "by", "for",
        "each", "or", "be", "are", "it", "its", "at", "as", "an", "any",
        "all", "this", "that", "with", "can", "how"}

def tokens(s):
    return [w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP]

docs = [Counter(tokens(s)) for s in sections]
n = len(docs)
df = Counter(w for d in docs for w in d)     # sections containing each word
idf = {w: math.log(n / df[w]) + 1 for w in df}

def vector(counter):
    return {w: c * idf.get(w, 0.0) for w, c in counter.items()}

def cosine(u, v):
    dot = sum(u[w] * v.get(w, 0.0) for w in u)
    nu = math.sqrt(sum(x * x for x in u.values()))
    nv = math.sqrt(sum(x * x for x in v.values()))
    return dot / (nu * nv) if nu and nv else 0.0

question = "How can the reserve fund be used?"
q = vector(Counter(tokens(question)))
scores = sorted(((cosine(q, vector(d)), t) for d, t in zip(docs, titles)),
                reverse=True)
print("Question:", question)
for score, title in scores[:3]:
    print(f"  {score:.3f}  {title}")
