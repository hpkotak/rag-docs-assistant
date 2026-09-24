"""Retrieval: keyword search (BM25), embedding search, and a hybrid of the two.

Embeddings come from a small local model (BAAI/bge-small-en-v1.5, 67 MB, runs on CPU), downloaded
once into .cache/. No API key or vector database is needed at this size.
"""
import math
import re
from collections import Counter
from functools import lru_cache

import numpy as np

from assistant.corpus import ROOT, Chunk

EMBED_MODEL = "BAAI/bge-small-en-v1.5"


STOPWORDS = set("""a an and are as at be but by can do does for from how i if in is it its me my of on or our
so that the their them there they this to up we what when where which who will with you your""".split())


def tokenize(text: str) -> list[str]:
    # Keeps things like "e3001", "tfx_live_" and "payment.failed" as single tokens.
    return [t for t in re.findall(r"[a-z0-9]+(?:[._][a-z0-9]+)*_?", text.lower()) if t not in STOPWORDS]


class BM25:
    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75):
        self.docs = [Counter(tokenize(t)) for t in texts]
        self.lens = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lens) / len(self.lens)
        df = Counter(tok for d in self.docs for tok in d)
        n = len(self.docs)
        self.idf = {tok: math.log(1 + (n - f + 0.5) / (f + 0.5)) for tok, f in df.items()}
        self.k1, self.b = k1, b

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for d, ln in zip(self.docs, self.lens):
            s = 0.0
            for tok in q:
                if tok in d:
                    tf = d[tok]
                    s += self.idf[tok] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * ln / self.avg))
            out.append(s)
        return out


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding
    return TextEmbedding(EMBED_MODEL, cache_dir=str(ROOT / ".cache" / "models"))


class Dense:
    def __init__(self, texts: list[str]):
        self.vecs = np.array(list(_model().passage_embed(texts)))
        self.vecs /= np.linalg.norm(self.vecs, axis=1, keepdims=True)

    def scores(self, query: str) -> list[float]:
        q = np.array(next(iter(_model().query_embed(query))))
        return list(self.vecs @ (q / np.linalg.norm(q)))


def _ranking(scores: list[float]) -> list[int]:
    return sorted(range(len(scores)), key=lambda i: -scores[i])


class Index:
    """mode: "dense" (embeddings only), "bm25" (keywords only) or "hybrid" (both, merged by rank)."""

    def __init__(self, chunks: list[Chunk], mode: str = "hybrid"):
        self.chunks, self.mode = chunks, mode
        texts = [c.text for c in chunks]
        self.bm25 = BM25(texts) if mode in ("bm25", "hybrid") else None
        self.dense = Dense(texts) if mode in ("dense", "hybrid") else None

    def search(self, query: str, k: int) -> list[Chunk]:
        if self.mode == "bm25":
            order = _ranking(self.bm25.scores(query))
        elif self.mode == "dense":
            order = _ranking(self.dense.scores(query))
        else:
            # Reciprocal rank fusion: a chunk ranked high by either method comes out near the top.
            fused = Counter()
            for ranks in (_ranking(self.bm25.scores(query)), _ranking(self.dense.scores(query))):
                for pos, i in enumerate(ranks):
                    fused[i] += 1 / (60 + pos)
            order = [i for i, _ in fused.most_common()]
        return [self.chunks[i] for i in order[:k]]
