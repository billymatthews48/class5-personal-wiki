"""The local retrieval index, stored in .wiki/ (outside the vault).

  parsed/<sha256>.json   cached passages per raw file, so unchanged files are never re-parsed
  chunks.jsonl           one line per passage: raw path, locator, text, subject key
  vectors.npy            embeddinggemma vectors aligned with chunks.jsonl (optional)
  embed_cache.sqlite     text-hash -> vector, so re-indexing only embeds new passages
"""
import hashlib
import json
import sqlite3

import numpy as np

from . import config, subjects as subjects_mod
from .ingest import Segment, read, supported

CHUNKS = config.STATE / "chunks.jsonl"
VECTORS = config.STATE / "vectors.npy"
PARSED = config.STATE / "parsed"
EMBED_CACHE = config.STATE / "embed_cache.sqlite"
PARSER_VERSION = 3  # bump when ingest/ changes how passages are cut, to invalidate parsed/


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_cached(path):
    """Passages for one raw file, re-parsed only when its bytes change."""
    digest = sha256_file(path)
    cache = PARSED / f"{digest}.v{PARSER_VERSION}.json"
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        return digest, [Segment(**s) for s in data]
    doc = read(path)
    segs = doc.segments if doc else []
    PARSED.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps([s.__dict__ for s in segs]), encoding="utf-8")
    return digest, segs


def build_chunks(progress=print):
    """Rebuild chunks.jsonl from every raw file. Returns (chunks, per-file report)."""
    subs = subjects_mod.load()
    chunks, report = [], []
    for path in sorted(p for p in config.RAW.rglob("*") if p.is_file() and supported(p)):
        rel = path.relative_to(config.VAULT).as_posix()
        digest, segs = parse_cached(path)
        subj = subjects_mod.subject_for(rel, subs)
        report.append({"raw_path": rel, "sha256": digest, "passages": len(segs),
                       "subject": subj.key if subj else None})
        for i, s in enumerate(segs):
            chunks.append({
                "id": hashlib.sha1(f"{rel}|{i}".encode()).hexdigest()[:12],
                "raw_path": rel, "locator": s.locator, "text": s.text,
                "subject": subj.key if subj else None,
            })
    config.STATE.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    progress(f"indexed {len(chunks)} passages from {len(report)} raw files")
    return chunks, report


def load_chunks():
    if not CHUNKS.exists():
        return []
    with open(CHUNKS, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# ---------- embeddings (embeddinggemma via local Ollama) ----------

def doc_prompt(chunk, title):
    return f"title: {title or 'none'} | text: {chunk['text']}"


def query_prompt(q):
    return f"task: search result | query: {q}"


def embed_chunks(client, chunks, titles, progress=print):
    """Embed every chunk, reusing cached vectors; writes vectors.npy aligned with chunks."""
    db = sqlite3.connect(EMBED_CACHE)
    db.execute("CREATE TABLE IF NOT EXISTS emb (h TEXT PRIMARY KEY, v BLOB)")
    prompts = [doc_prompt(c, titles.get(c["subject"])) for c in chunks]
    hashes = [hashlib.sha1(p.encode()).hexdigest() for p in prompts]
    have = {}
    for i in range(0, len(hashes), 500):
        batch = hashes[i:i + 500]
        q = f"SELECT h, v FROM emb WHERE h IN ({','.join('?' * len(batch))})"
        have.update({h: v for h, v in db.execute(q, batch)})
    todo = [i for i, h in enumerate(hashes) if h not in have]
    progress(f"embedding {len(todo)} new passages ({len(chunks) - len(todo)} cached)")
    step = 64
    for n in range(0, len(todo), step):
        idx = todo[n:n + step]
        vecs = client.embed([prompts[i] for i in idx])
        for i, v in zip(idx, vecs):
            blob = np.asarray(v, dtype=np.float32).tobytes()
            have[hashes[i]] = blob
            db.execute("INSERT OR REPLACE INTO emb VALUES (?, ?)", (hashes[i], blob))
        db.commit()
        if (n // step) % 10 == 0:
            progress(f"  embedded {min(n + step, len(todo))}/{len(todo)}")
    db.close()
    mat = np.stack([np.frombuffer(have[h], dtype=np.float32) for h in hashes]) if hashes else np.zeros((0, 768), np.float32)
    mat /= np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9
    np.save(VECTORS, mat)
    return mat


def load_vectors(n_chunks):
    if not VECTORS.exists():
        return None
    mat = np.load(VECTORS)
    return mat if mat.shape[0] == n_chunks else None   # stale index -> keyword only
