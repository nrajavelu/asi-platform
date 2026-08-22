"""Real BM25 retrieval layer -- no API key required.

Standing in for the vector DB (Qdrant) in this scaffold: same contract
(query in, ranked chunks + scores out, real wall-clock timing), swappable
for dense retrieval later without touching the analysis layer.
"""
import time
from rank_bm25 import BM25Okapi


class Retriever:
    def __init__(self, chunks: list[str]):
        self.chunks = chunks
        tokenized = [c.lower().split() for c in chunks]
        t0 = time.perf_counter()
        self.bm25 = BM25Okapi(tokenized)
        self.index_seconds = time.perf_counter() - t0

    def query(self, q: str, k: int = 4):
        t0 = time.perf_counter()
        scores = self.bm25.get_scores(q.lower().split())
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        elapsed = time.perf_counter() - t0
        return [(self.chunks[i], float(scores[i])) for i in ranked], elapsed
