"""Measure memory and response time on this machine with the real wiki.

    python tests/bench.py --model gemma4:e4b-it-q4_K_M [--label offline]

For the chosen chat model it measures:
  1. cold RAG answer (model unloaded first): load time, time to first token, total, tokens/s
  2. warm RAG answer (same question again)
  3. ingest of one small source (parse + embed + one Gemma-written note), via a scratch copy
  4. keyword search latency (no model)
Memory: peak resident memory of all Ollama processes and of this Python process (sampled every
0.25 s), `ollama ps` reported size, and system available RAM before/after.
Writes evidence/<label>/bench-<model>.json and .md. Nothing here is estimated.
"""
import argparse
import json
import sys
import threading
import time
from pathlib import Path

import psutil
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.common import EVIDENCE, dump, environment, write   # noqa: E402
from wiki import config                                         # noqa: E402
from wiki.harness import Harness                                # noqa: E402
from wiki.llm import OllamaClient                               # noqa: E402


class MemSampler:
    def __init__(self):
        self.peak_ollama = self.peak_py = 0
        self.min_avail = psutil.virtual_memory().available
        self._stop = threading.Event()

    def _ollama_rss(self):
        # The weights live in Ollama's runner process (llama-server.exe), not in ollama.exe itself.
        total = 0
        for p in psutil.process_iter(["name"]):
            try:
                if (p.info["name"] or "").lower().startswith(("ollama", "llama-server")):
                    total += p.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return total

    def run(self):
        me = psutil.Process()
        while not self._stop.is_set():
            self.peak_ollama = max(self.peak_ollama, self._ollama_rss())
            self.peak_py = max(self.peak_py, me.memory_info().rss)
            self.min_avail = min(self.min_avail, psutil.virtual_memory().available)
            time.sleep(0.25)

    def __enter__(self):
        self.t = threading.Thread(target=self.run, daemon=True)
        self.t.start()
        return self

    def __exit__(self, *a):
        self._stop.set()
        self.t.join()

    def result(self):
        gb = lambda b: round(b / 2**30, 2)
        return {"peak_ollama_rss_gb": gb(self.peak_ollama), "peak_python_rss_gb": gb(self.peak_py),
                "min_system_available_gb": gb(self.min_avail)}


def unload(model):
    requests.post(f"{config.OLLAMA_URL}/api/generate", json={"model": model, "keep_alive": 0}, timeout=60)


def ollama_ps():
    return [{"name": m["name"], "size_gb": round(m.get("size", 0) / 2**30, 2),
             "size_vram_gb": round(m.get("size_vram", 0) / 2**30, 2)}
            for m in requests.get(f"{config.OLLAMA_URL}/api/ps", timeout=10).json().get("models", [])]


def timed(label, fn):
    with MemSampler() as m:
        t = time.perf_counter()
        out = fn()
        wall = round(time.perf_counter() - t, 2)
    return {"step": label, "wall_s": wall, **m.result(), "ollama_ps": ollama_ps()}, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=config.CHAT_MODEL)
    ap.add_argument("--label", default="online-dev")
    args = ap.parse_args()
    config.CHAT_MODEL = args.model
    client = OllamaClient(model=args.model)
    h = Harness(client)
    q = yaml.safe_load((Path(__file__).parent / "questions.yaml").read_text(encoding="utf-8"))["ask"][0]
    env = environment()
    rows = []

    unload(args.model)
    time.sleep(2)
    row, rec = timed("RAG answer, cold (model load included)", lambda: h.ask(q["question"]))
    rows.append({**row, **{k: rec["stats"][k] for k in ("load_s", "ttft_s", "prompt_tokens", "prompt_tok_s",
                                                       "gen_tokens", "gen_tok_s")}, "status": rec["status"]})
    row, rec = timed("RAG answer, warm", lambda: h.ask(q["question"]))
    rows.append({**row, **{k: rec["stats"][k] for k in ("load_s", "ttft_s", "prompt_tokens", "prompt_tok_s",
                                                       "gen_tokens", "gen_tok_s")}, "status": rec["status"]})
    row, _ = timed("keyword search (no model)", lambda: h.search("lean operations waste", use_embeddings=False))
    rows.append(row)
    row, _ = timed("hybrid search (embeddinggemma)", lambda: h.search("lean operations waste"))
    rows.append(row)

    # Ingest benchmark: note writing for one small subject (sources unchanged -> forced rewrite
    # into a scratch copy of the vault is avoided; we time generate_note directly instead).
    from wiki import index_store, notes, subjects
    subj = next(s for s in subjects.load() if s.key == "personal-development")
    chunks = index_store.load_chunks()
    by_file = {}
    for c in chunks:
        by_file.setdefault(c["raw_path"], []).append(c)
    files = sorted({c["raw_path"] for c in chunks if c["subject"] == subj.key})
    others = [s.title for s in subjects.load() if s.key != subj.key]
    ex = notes.pick_excerpts(files, by_file)
    row, (data, st) = timed(f"ingest: Gemma writes one note ({subj.title})",
                            lambda: notes.generate_note(client, subj, ex, others))
    rows.append({**row, **{k: st[k] for k in ("ttft_s", "prompt_tokens", "prompt_tok_s", "gen_tokens", "gen_tok_s")}})
    row, _ = timed("ingest: parse + index all raw files (cached parse)", lambda: index_store.build_chunks(lambda m: None))
    rows.append(row)

    name = args.model.replace(":", "_")
    dump(EVIDENCE / args.label / f"bench-{name}.json", {"env": env, "rows": rows})
    md = [f"# Benchmark: {args.model} ({args.label})", "", "```", *[f"{k}: {v}" for k, v in env.items()], "```", "",
          "| Step | Wall s | Load s | First token s | Prompt tok (tok/s) | Gen tok (tok/s) | Peak Ollama RSS GB | Min free RAM GB | ollama ps |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        ps = "; ".join(f"{m['name']} {m['size_gb']} GB" for m in r["ollama_ps"])
        md.append(f"| {r['step']} | {r['wall_s']} | {r.get('load_s', '')} | {r.get('ttft_s', '')} | "
                  f"{r.get('prompt_tokens', '')} ({r.get('prompt_tok_s', '')}) | {r.get('gen_tokens', '')} ({r.get('gen_tok_s', '')}) | "
                  f"{r['peak_ollama_rss_gb']} | {r['min_system_available_gb']} | {ps} |")
    write(EVIDENCE / args.label / f"bench-{name}.md", "\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
