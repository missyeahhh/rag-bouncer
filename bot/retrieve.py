"""BM25 keyword search. No embeddings, no model download, same result every run."""
import math
import re
from collections import Counter

K1, B = 1.5, 0.75


STOP = set("a an and are as at be by can do does for from how i in is it my of on or the to what when which why with you your".split())


def _stem(word):
    """Crude suffix stripping, enough for "databases" to match "database"."""
    for suffix in ("ing", "ed", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _tokens(text):
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


class Index:
    def __init__(self, chunks):
        self.chunks = chunks
        self.docs = [Counter(_tokens(c["text"])) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / len(self.lengths)
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query):
        q = _tokens(query)
        out = []
        for d, length in zip(self.docs, self.lengths):
            s = 0.0
            for t in q:
                if t in d:
                    tf = d[t]
                    s += self.idf[t] * tf * (K1 + 1) / (tf + K1 * (1 - B + B * length / self.avg))
            out.append(s)
        return out

    def top(self, query, k=4):
        ranked = sorted(range(len(self.chunks)), key=self.scores(query).__getitem__, reverse=True)
        return [self.chunks[i] for i in ranked[:k]]

    def bottom(self, query, k=4):
        """The least relevant chunks. Only used to sabotage the bot in the gate's red test."""
        ranked = sorted(range(len(self.chunks)), key=self.scores(query).__getitem__)
        return [self.chunks[i] for i in ranked[:k]]
