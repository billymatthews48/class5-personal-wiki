"""The harness: everything between the CLI and the model.

  search  -> retrieval tool only. No model call.
  ask     -> RAG workflow: retrieve -> evidence prompt (wiki-instructions.md) -> Gemma -> citation
             check. Stateless: a fresh message list per question, never chat history.
  chat    -> persona.md + rolling conversation history. Gemma decides whether to call the
             search_notes tool; the harness runs the tool and checks citations in the reply.

Every run is saved as JSON + Markdown under .wiki/runs/<mode>/.
"""
import json
import re
from dataclasses import asdict
from datetime import datetime

from . import config
from .llm import OllamaClient
from .retrieval import Retriever

INSUFFICIENT = "INSUFFICIENT_EVIDENCE"
CITE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def load_prompt(name):
    return (config.PROMPTS / name).read_text(encoding="utf-8")


def cited_numbers(text):
    return {int(n) for group in CITE.findall(text) for n in re.split(r"\s*,\s*", group)}


def format_evidence(passages, budget=config.ASK_EVIDENCE_CHARS):
    """Number passages [1..n] with their source labels, within a character budget."""
    blocks, used, kept = [], 0, []
    for p in passages:
        text = p.text if used + len(p.text) <= budget else p.text[: max(0, budget - used)]
        if len(text) < 200 and kept:
            break
        n = len(kept) + 1
        blocks.append(f"[{n}] source: {p.raw_path} ({p.locator})\n{text}")
        kept.append(p)
        used += len(text)
    return "\n\n".join(blocks), kept


def source_lines(passages, numbers=None):
    lines = []
    for n, p in enumerate(passages, 1):
        if numbers is None or n in numbers:
            note = f" | note: [[{p.note_title}]]" if p.note_title else ""
            lines.append(f"[{n}] {p.raw_path} ({p.locator}){note}")
    return lines


def save_run(mode, record, markdown):
    folder = config.RUNS / mode
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
    (folder / f"{stamp}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str),
                                          encoding="utf-8")
    (folder / f"{stamp}.md").write_text(markdown, encoding="utf-8")
    return folder / f"{stamp}.md"


def run_header(mode, client=None):
    online = getattr(client, "api_key", None) is not None
    return {"mode": mode, "execution": "online" if online else "local",
            "model": getattr(client, "model", config.CHAT_MODEL),
            "embed_model": config.EMBED_MODEL,
            "runtime": "Gemini API (hosted Gemma)" if online else f"Ollama at {config.OLLAMA_URL}",
            "time": datetime.now().isoformat(timespec="seconds")}


class Harness:
    def __init__(self, client=None):
        self.client = client or OllamaClient()
        self._retriever = None

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = Retriever(self.client)
        return self._retriever

    # ---------------- search: the retrieval tool, exposed directly ----------------
    def search(self, query, k=5, use_embeddings=True):
        passages = self.retriever.search(query, k=k, use_embeddings=use_embeddings)
        record = {**run_header("search", self.client), "query": query, "k": k,
                  "passages": [asdict(p) for p in passages]}
        md = [f"# search: {query}", f"method: {passages[0].method if passages else 'n/a'}", ""]
        for p in passages:
            md += [f"## {p.rank}. {p.raw_path} ({p.locator})",
                   f"note: {p.note_path} | bm25 {p.bm25} | cosine {p.cosine} | rrf {p.score}", "",
                   p.text, ""]
        record["saved_to"] = str(save_run("search", record, "\n".join(md)))
        return passages, record

    # ---------------- ask: standalone RAG with citation checks ----------------
    def ask(self, question, k=config.ASK_TOP_K, on_token=None):
        header = run_header("ask", self.client)
        candidates = self.retriever.search(question, k=k)
        best_cos = max((p.cosine or 0) for p in candidates) if candidates else 0
        record = {**header, "question": question,
                  "retrieved": [asdict(p) for p in candidates], "best_cosine": best_cos}

        if not candidates or (candidates[0].cosine is not None and best_cos < config.ASK_MIN_COSINE):
            record.update(status="insufficient_evidence", gate="retrieval",
                          answer=f"Insufficient evidence: nothing in the wiki is close enough to this "
                                 f"question (best similarity {best_cos:.2f} < {config.ASK_MIN_COSINE}).",
                          citations=[], model_called=False)
            return self._finish_ask(record, [])

        evidence, used = format_evidence(candidates)
        messages = [  # fresh list every time: no chat history, no persona
            {"role": "system", "content": load_prompt("wiki-instructions.md")},
            {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{evidence}"},
        ]
        text, stats = self.client.chat(messages, temperature=0.1, on_token=on_token, max_tokens=400)
        text = text.strip()
        record.update(model_called=True, stats=stats, raw_answer=text, prompt_chars=sum(len(m["content"]) for m in messages),
                      evidence_passages=len(used))

        if text.startswith(INSUFFICIENT) or INSUFFICIENT in text[:80]:
            record.update(status="insufficient_evidence", gate="model",
                          answer="Insufficient evidence: " + text.split(":", 1)[-1].strip(), citations=[])
            return self._finish_ask(record, used)

        numbers = cited_numbers(text)
        valid = {n for n in numbers if 1 <= n <= len(used)}
        invalid = sorted(numbers - valid)
        if not valid:
            record.update(status="insufficient_evidence", gate="citation_check",
                          answer="Insufficient evidence: the model's answer cited no retrieved passage, "
                                 "so it was not shown as grounded.", citations=[])
            return self._finish_ask(record, used)
        for n in invalid:
            text = text.replace(f"[{n}]", "")
        record.update(status="answered", answer=text, citations=sorted(valid),
                      invalid_citations=invalid, gate=None)
        return self._finish_ask(record, used)

    def _finish_ask(self, record, used):
        cites = set(record.get("citations") or [])
        record["sources"] = source_lines(used, cites) if cites else []
        md = [f"# ask: {record['question']}",
              f"model: {record['model']} | execution: {record['execution']} | status: {record['status']}", "",
              "## Answer", record["answer"], ""]
        if record["sources"]:
            md += ["## Citations"] + [f"- {s}" for s in record["sources"]] + [""]
        md += ["## Retrieved passages"]
        for p in record["retrieved"]:
            md += [f"- {p['raw_path']} ({p['locator']}), cosine {p['cosine']}, bm25 {p['bm25']}",
                   "  > " + p["text"][:400].replace("\n", " ")]
        record["saved_to"] = str(save_run("ask", record, "\n".join(md)))
        return record

    def chat_session(self):
        return ChatSession(self)


SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_notes",
        "description": "Search Billy's academic wiki (courses, essays, projects) for original passages. "
                       "Use only when the reply needs facts from his notes.",
        "parameters": {"type": "object", "required": ["query"],
                       "properties": {"query": {"type": "string",
                                                "description": "keywords describing what to find"}}},
    },
}


MEMORY_FILE = config.VAULT / "memory" / "Chat Memory.md"
DRAFTS_DIR = config.VAULT / "drafts"


def read_memory():
    if not MEMORY_FILE.exists():
        return []
    return [l for l in MEMORY_FILE.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]


class ChatSession:
    """Conversation context lives here and only here; ask() never sees it."""

    def __init__(self, harness):
        self.h = harness
        self.history = []        # user/assistant turns only (tool output is not kept long-term)
        self.log = []
        self.system = load_prompt("persona.md") + self._memory_block()

    # ---- explicit memory and drafts (optional feature) ----
    # Both live in the vault for browsing but OUTSIDE raw/, so the retrieval index (raw only) and
    # therefore ask mode never treat them as evidence.
    def _memory_block(self):
        items = read_memory()
        if not items:
            return ""
        return ("\n\n## Things Billy explicitly asked you to remember (user-stated, NOT verified notes; "
                "never cite them as sources)\n" + "\n".join(items))

    def remember(self, text):
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not MEMORY_FILE.exists():
            MEMORY_FILE.write_text("# Chat Memory\n\nSaved only by an explicit /remember in chat. "
                                   "User-stated, not verified; excluded from search and ask.\n\n", encoding="utf-8")
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"- {datetime.now():%Y-%m-%d}: {text.strip()}\n")
        self.system = load_prompt("persona.md") + self._memory_block()
        return MEMORY_FILE

    def save_draft(self, name=None):
        reply = next((m["content"] for m in reversed(self.history) if m["role"] == "assistant"), None)
        if not reply:
            raise LookupError("Nothing to save yet: ask Quill for a draft first.")
        request = next((m["content"] for m in reversed(self.history) if m["role"] == "user"), "")
        title = name or " ".join(re.findall(r"[A-Za-z]+", request)[:5]).title() or "Draft"
        path = DRAFTS_DIR / f"{title}.md"
        n = 2
        while path.exists():
            path = DRAFTS_DIR / f"{title} {n}.md"
            n += 1
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\ntype: generated draft\nmodel: {getattr(self.h.client, 'model', '')}\n"
                        f"created: {datetime.now():%Y-%m-%d}\n---\n# {path.stem}\n\n"
                        f"> Generated by Quill in chat from: {request}\n\n{reply}\n", encoding="utf-8")
        return path

    def reset(self):
        self.history, self.log = [], []

    def _trimmed(self):
        kept, used = [], 0
        for m in reversed(self.history):
            used += len(m["content"])
            if used > config.CHAT_HISTORY_CHARS and kept:
                break
            kept.append(m)
        return list(reversed(kept))

    def turn(self, user_text, force_query=None, on_token=None):
        messages = [{"role": "system", "content": self.system}, *self._trimmed(),
                    {"role": "user", "content": user_text}]
        passages, query, stats_all = [], None, []

        if force_query:                       # /notes <query>: user explicitly asked for retrieval
            query = force_query
        else:                                 # let Gemma decide via native tool calling
            text, stats = self.h.client.chat(messages, temperature=0.7, tools=[SEARCH_TOOL],
                                             on_token=on_token)
            stats_all.append(stats)
            calls = [c for c in stats["tool_calls"] if c.get("function", {}).get("name") == "search_notes"]
            if calls:
                query = calls[0]["function"].get("arguments", {}).get("query") or user_text
            else:
                return self._record(user_text, text.strip(), None, [], stats_all)

        passages = self.h.retriever.search(query, k=4)
        evidence, used = format_evidence(passages, budget=config.ASK_EVIDENCE_CHARS)
        messages.append({"role": "assistant", "content": "",
                         "tool_calls": [{"function": {"name": "search_notes", "arguments": {"query": query}}}]})
        messages.append({"role": "tool", "tool_name": "search_notes",
                         "content": f"Results for '{query}' (cite as [n]):\n\n{evidence}"})
        text, stats = self.h.client.chat(messages, temperature=0.7, on_token=on_token)
        stats_all.append(stats)
        return self._record(user_text, text.strip(), query, used, stats_all)

    def _record(self, user_text, reply, query, used, stats_all):
        numbers = cited_numbers(reply) if used else set()
        valid = {n for n in numbers if 1 <= n <= len(used)}
        sources = source_lines(used, valid) if valid else []
        self.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": reply}]
        entry = {**run_header("chat", self.h.client), "user": user_text, "reply": reply, "retrieved": query is not None,
                 "search_query": query, "citations": sorted(valid),
                 "invalid_citations": sorted(numbers - valid), "sources": sources,
                 "passages": [asdict(p) for p in used], "stats": stats_all}
        self.log.append(entry)
        return entry

    def save(self):
        hdr = run_header("chat", self.h.client)
        md = ["# chat transcript", f"model: {hdr['model']} | execution: {hdr['execution']}", ""]
        for e in self.log:
            md += [f"**You:** {e['user']}", "",
                   f"*(notes searched: {e['search_query']!r})*" if e["retrieved"] else "*(no notes search)*", "",
                   f"**Quill:** {e['reply']}", ""]
            md += [f"- {s}" for s in e["sources"]] + [""]
        return save_run("chat", {"turns": self.log}, "\n".join(md))
