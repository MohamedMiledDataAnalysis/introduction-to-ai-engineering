"""Split documents into chunks and retrieve the chunks most relevant to a question (BM25)."""
import math
import re
from collections import Counter

STOP = {"the", "of", "to", "and", "a", "in", "on", "is", "by", "for", "each", "or", "be", "are", "it",
        "its", "at", "as", "an", "any", "all", "this", "that", "with", "can", "how", "what", "which",
        "does", "do", "who", "when", "after", "much", "many"}


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def chunk_markdown(text, doc_id, max_words=180):
    """One chunk per '## ' section; long sections are split at blank lines into pieces of at most max_words."""
    chunks = []
    for part in re.split(r"\n## ", "\n" + text)[1:]:
        title, _, body = part.partition("\n")
        pieces, current = [], []
        for para in re.split(r"\n\s*\n", body.strip()):
            if current and len(" ".join(current + [para]).split()) > max_words:
                pieces.append("\n\n".join(current))
                current = []
            current.append(para)
        if current:
            pieces.append("\n\n".join(current))
        for i, piece in enumerate(pieces, 1):
            cid = f"{doc_id}#{title.split('.')[0].strip()}" + (f".{i}" if len(pieces) > 1 else "")
            chunks.append({"id": cid, "title": title.strip(), "text": f"{title.strip()}\n{piece}"})
    return chunks


class BM25:
    """Okapi BM25 ranking: rewards rare words that appear in a chunk, discounts long chunks."""

    def __init__(self, chunks, k1=1.5, b=0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.docs = [Counter(tokens(c["text"])) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / len(self.docs)
        n = len(self.docs)
        df = Counter(w for d in self.docs for w in d)
        self.idf = {w: math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5)) for w in df}

    def score(self, query, i):
        d, length, s = self.docs[i], self.lengths[i], 0.0
        for w in tokens(query):
            if w in d:
                tf = d[w]
                s += self.idf[w] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * length / self.avg))
        return s

    def search(self, query, k=3):
        ranked = sorted(range(len(self.docs)), key=lambda i: self.score(query, i), reverse=True)
        return [(self.chunks[i], round(self.score(query, i), 3)) for i in ranked[:k]]


def cosine(u, v):
    dot = sum(a * b for a, b in zip(u, v))
    nu = math.sqrt(sum(a * a for a in u))
    nv = math.sqrt(sum(b * b for b in v))
    return dot / (nu * nv) if nu and nv else 0.0


def reciprocal_rank_fusion(rankings, k=60):
    """Combine several ranked lists of chunk ids: each list gives 1/(k + rank) to its items."""
    scores = Counter()
    for ranking in rankings:
        for rank, cid in enumerate(ranking, 1):
            scores[cid] += 1 / (k + rank)
    return [cid for cid, _ in scores.most_common()]


CITATION = re.compile(r"\[([A-Z][A-Za-z\-]*#[\d.]+)\]")


def check_citations(answer, retrieved):
    """retrieved: list of chunks given to the model. Returns a list of problems (empty = grounded)."""
    from aie.factcheck import extract_figures
    by_id = {c["id"]: c for c in retrieved}
    cited = CITATION.findall(answer)
    problems = []
    if not cited:
        problems.append("no citation")
    for cid in cited:
        if cid not in by_id:
            problems.append(f"cites {cid}, which was not provided")
    cited_text = " ".join(by_id[c]["text"] for c in cited if c in by_id)
    source_values = {(f.unit, round(f.value * f.scale, 2)) for f in extract_figures(cited_text)}
    for f in extract_figures(CITATION.sub("", answer)):
        if (f.unit, round(f.value * f.scale, 2)) not in source_values:
            problems.append(f"figure {f.raw} not found in the cited passages")
    return problems
