"""Retrieval-only evaluation: did the expected source appear, and at what rank? No model call.

    python tests/retrieval_check.py            # hybrid if embeddings exist, plus keyword-only
Writes evidence/retrieval/retrieval_check.md
"""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.common import EVIDENCE, CountingClient, environment, write   # noqa: E402
from wiki.retrieval import Retriever                                     # noqa: E402


def main():
    qs = yaml.safe_load((Path(__file__).parent / "questions.yaml").read_text(encoding="utf-8"))["ask"]
    client = CountingClient()
    r = Retriever(client)
    env = environment()
    lines = ["# Retrieval check (no generation)", "",
             f"time {env['time']} | internet: {env['internet']} | embed model {env['embed_model']}", "",
             "| Test | Method | Expected source rank(s) in top 5 |", "|---|---|---|"]
    detail = []
    for q in qs:
        for use_emb in (False, True):
            res = r.search(q["question"], k=5, use_embeddings=use_emb)
            method = res[0].method if res else "none"
            ranks = [p.rank for p in res if p.raw_path in q["expected_sources"]]
            want = "n/a (unsupported question)" if not q["expected_sources"] else (ranks or "MISSING")
            lines.append(f"| {q['id']} | {method} | {want} |")
            detail += [f"### {q['id']} - {method}", f"Q: {q['question']}", ""]
            detail += [f"{p.rank}. `{p.raw_path}` ({p.locator}) bm25 {p.bm25} cosine {p.cosine}" for p in res]
            detail.append("")
    assert client.chat_calls == 0, "retrieval must not call the language model"
    write(EVIDENCE / "retrieval" / "retrieval_check.md", "\n".join(lines + ["", "## Detail", ""] + detail))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
