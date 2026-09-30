"""THE RETRIEVAL TOOL. Finds original passages; never generates text.

search() ranks raw passages with BM25 keyword scoring (always available, pure Python) and,
when the local embedding model is reachable, cosine similarity from embeddinggemma. The two
rankings are merged with reciprocal rank fusion. Each result carries its raw file path,
locator, and the wiki note it belongs to, so callers can cite or open the exact source.
"""
import re
from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi

from . import index_store, subjects as subjects_mod
from .llm import LLMError

STOP = set("""a an and are as at be by for from has have i in is it its my of on or that the this
to was were what which who with how did do does me we our you your about into than then""".split())
RRF_K = 60


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+(?:[.,][0-9]+)*", text.lower()) if t not in STOP]


@dataclass
class Passage:
    rank: int
    text: str
    raw_path: str
    locator: str
    note_title: str | None
    note_path: str | None
    bm25: float
    cosine: float | None
    score: float
    method: str


class Retriever:
    def __init__(self, client=None):
        self.client = client
        self.chunks = index_store.load_chunks()
        if not self.chunks:
            raise LookupError("The index is empty. Run `wiki ingest` first.")
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in self.chunks])
        self.vectors = index_store.load_vectors(len(self.chunks))
        self.subjects = {s.key: s for s in subjects_mod.load()}

    def search(self, query, k=5, use_embeddings=True):
        bm = self.bm25.get_scores(tokenize(query))
        order_bm = np.argsort(-bm)[:200]
        cos, method = None, "keyword (BM25)"
        if use_embeddings and self.vectors is not None and self.client is not None:
            try:
                qv = np.asarray(self.client.embed([index_store.query_prompt(query)])[0], np.float32)
                qv /= np.linalg.norm(qv) + 1e-9
                cos = self.vectors @ qv
                method = "hybrid (BM25 + embeddinggemma)"
            except LLMError:
                cos = None   # Ollama down: keyword search still works
        fused = {}
        for r, i in enumerate(order_bm):
            if bm[i] > 0:
                fused[i] = fused.get(i, 0) + 1 / (RRF_K + r)
        if cos is not None:
            for r, i in enumerate(np.argsort(-cos)[:200]):
                fused[i] = fused.get(i, 0) + 1 / (RRF_K + r)
        results, seen = [], set()
        for i in sorted(fused, key=fused.get, reverse=True):
            c = self.chunks[i]
            sig = re.sub(r"\W+", "", c["text"].lower())[:160]   # same text in .docx and .pdf copies
            if sig in seen:
                continue
            seen.add(sig)
            subj = self.subjects.get(c["subject"])
            results.append(Passage(
                rank=len(results) + 1, text=c["text"], raw_path=c["raw_path"], locator=c["locator"],
                note_title=subj.title if subj else None, note_path=subj.note_path if subj else None,
                bm25=round(float(bm[i]), 2), cosine=None if cos is None else round(float(cos[i]), 3),
                score=round(fused[i], 4), method=method))
            if len(results) == k:
                break
        return results
