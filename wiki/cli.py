"""`wiki` command line. Parses arguments, picks the mode, prints results. Logic lives in harness.py."""
import argparse
import sys
import textwrap

from . import config
from .llm import GeminiGemmaClient, LLMError, OllamaClient

HELP = f"""\
wiki: a local academic wiki you can chat with, question, and search. Runs offline.

commands
  wiki ingest [PATH]        Parse raw files, (re)build the retrieval index, have local Gemma write or
                            update subject notes, and rebuild vault/index.md. PATH defaults to vault/raw.
                            A PATH outside vault/raw is first copied into vault/raw/added/ unchanged.
  wiki search "QUERY" [-k N]  Show matching ORIGINAL passages with file paths. No answer is generated.
                            Works even when Ollama is not running (keyword-only).
  wiki ask "QUESTION" [--mode local]
                            Standalone factual answer from retrieved evidence with [n] citations, or an
                            explicit insufficient-evidence reply. Never uses chat history or persona.
  wiki chat                 Talk with Quill, the study assistant. Keeps conversation context and searches
                            your notes only when a reply needs them. In chat: /notes Q, /save, /reset, /help, /exit
  wiki lint                 Check note names, headings, links and source references.
  wiki rename "OLD" "NEW"   Rename a note and update every incoming link and the subject map.
  wiki doctor               Check the local model, index and paths.
  wiki serve [--port 8765]  Optional local web page (127.0.0.1 only) over the same harness.
  wiki ask/chat --mode online  Optional: hosted Gemma (gemma-4-26b-a4b-it) on the Gemini API. Needs
                            GEMINI_API_KEY. Sends the prompt (question + retrieved passages) to Google.
                            Never used unless requested; local is the default.

configuration (environment variables)
  WIKI_MODEL={config.CHAT_MODEL}   WIKI_EMBED_MODEL={config.EMBED_MODEL}
  OLLAMA_URL={config.OLLAMA_URL}   WIKI_NUM_CTX={config.NUM_CTX}   WIKI_THINK=0

required inputs: Ollama running locally with both models pulled (`ollama pull {config.CHAT_MODEL}`,
`ollama pull {config.EMBED_MODEL}`); original files in vault/raw/; subjects.yaml mapping files to notes.
execution: local only (default and only mode). No cloud service or fallback is ever used.
"""


def wrap(text, indent="  "):
    return "\n".join(textwrap.fill(p, 100, initial_indent=indent, subsequent_indent=indent)
                     if p.strip() else "" for p in text.split("\n"))


def cmd_search(args, h):
    passages, record = h.search(args.query, k=args.k, use_embeddings=not args.keyword)
    print(f"search | {passages[0].method if passages else 'no results'} | no answer generated\n")
    for p in passages:
        print(f"[{p.rank}] {p.raw_path}  ({p.locator})")
        print(f"    note: {p.note_path or '-'} | bm25 {p.bm25} | cosine {p.cosine}")
        print(wrap(p.text[:700], "    > ") + ("..." if len(p.text) > 700 else "") + "\n")
    print(f"saved: {record['saved_to']}")


def cmd_ask(args, h):
    print(f"ask | model {h.client.model} | execution: {args.mode} | standalone (no chat history)\n")
    rec = h.ask(args.question)
    print(wrap(rec["answer"]) + "\n")
    if rec["sources"]:
        print("citations:")
        for s in rec["sources"]:
            print("  " + s)
    else:
        print("closest passages (not used as evidence):")
        for p in rec["retrieved"][:3]:
            print(f"  - {p['raw_path']} ({p['locator']}) cosine {p['cosine']}")
    st = rec.get("stats") or {}
    if st:
        print(f"\n{st['wall_s']}s total, first token {st['ttft_s']}s, "
              f"{st['prompt_tokens']} prompt tokens @ {st['prompt_tok_s']} tok/s, "
              f"{st['gen_tokens']} generated @ {st['gen_tok_s']} tok/s")
    print(f"status: {rec['status']} | saved: {rec['saved_to']}")


def cmd_chat(args, h):
    s = h.chat_session()
    print(f"Quill (chat) | model {h.client.model} | execution: {args.mode}. /help for commands, /exit to quit.\n")
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("/exit", "/quit"):
            break
        if line == "/help":
            print("  /notes QUERY   search your notes for this turn\n"
                  "  /remember TEXT save a fact to Chat Memory (user-stated; never used as evidence)\n"
                  "  /draft [NAME]  save Quill's last reply to vault/drafts/ (kept apart from evidence)\n"
                  "  /save          save transcript\n  /reset         clear conversation\n  /exit          quit")
            continue
        if line.startswith("/remember"):
            text = line[len("/remember"):].strip()
            print(f"  saved to {s.remember(text).relative_to(config.VAULT)}" if text else "  usage: /remember TEXT")
            continue
        if line.startswith("/draft"):
            try:
                print(f"  draft saved: {s.save_draft(line[len('/draft'):].strip() or None).relative_to(config.VAULT)}")
            except LookupError as err:
                print(f"  {err}")
            continue
        if line == "/reset":
            s.reset()
            print("  (conversation cleared)")
            continue
        if line == "/save":
            print(f"  saved: {s.save()}")
            continue
        force = None
        if line.startswith("/notes"):
            force = line[len("/notes"):].strip() or None
            if not force:
                print("  usage: /notes QUERY")
                continue
        print("quill> ", end="", flush=True)
        try:
            e = s.turn(line, force_query=force, on_token=lambda t: print(t, end="", flush=True))
        except LLMError as err:
            print(f"\n  error: {err}")
            continue
        print()
        if e["retrieved"]:
            print(f"  (searched notes for: {e['search_query']!r})")
            for src in e["sources"]:
                print("  " + src)
        print()
    if s.log:
        print(f"transcript saved: {s.save()}")


def cmd_ingest(args, h):
    from .pipeline import ingest
    ingest(args.path, client=h.client, force=args.force)


def cmd_lint(args, h):
    from .notes import lint
    problems = lint()
    print("\n".join(problems) if problems else "lint: no problems found")
    return 1 if problems else 0


def cmd_rename(args, h):
    from .notes import rename
    dest, changed = rename(args.old, args.new)
    print(f"renamed -> {dest.relative_to(config.VAULT)}; links updated in: {', '.join(changed) or 'none'}")
    print("run `wiki ingest` to refresh embeddings, then rerun the question tests.")


def cmd_doctor(args, h):
    from . import index_store
    ok = True
    print(f"vault:  {config.VAULT}  (raw files: {sum(1 for p in config.RAW.rglob('*') if p.is_file())})")
    print(f"state:  {config.STATE}")
    try:
        models = h.client.installed_models()
        for m in (config.CHAT_MODEL, config.EMBED_MODEL):
            present = any(x == m or x.split(":")[0] == m for x in models)
            ok &= present
            print(f"model:  {m}: {'installed' if present else 'MISSING (ollama pull ' + m + ')'}")
        print(f"ollama: reachable at {config.OLLAMA_URL}")
    except LLMError as e:
        ok = False
        print(f"ollama: {e}")
    n = len(index_store.load_chunks())
    vec = index_store.load_vectors(n)
    print(f"index:  {n} passages, embeddings {'ok' if vec is not None else 'missing/stale (keyword only)'}")
    print("online: not configured (local-only build)")
    return 0 if ok and n else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="wiki", description=HELP,
                                     formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True)
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("search"); p.add_argument("query"); p.add_argument("-k", type=int, default=5)
    p.add_argument("--keyword", action="store_true", help="BM25 only, skip embeddings")
    p = sub.add_parser("ask"); p.add_argument("question")
    p.add_argument("--mode", choices=["local", "online"], default="local",
                   help="where Gemma runs: local (default, Ollama) or online (hosted Gemma, opt-in)")
    p = sub.add_parser("chat")
    p.add_argument("--mode", choices=["local", "online"], default="local")
    p = sub.add_parser("ingest"); p.add_argument("path", nargs="?")
    p.add_argument("--force", action="store_true", help="rewrite notes even if sources are unchanged")
    sub.add_parser("lint")
    p = sub.add_parser("rename"); p.add_argument("old"); p.add_argument("new")
    sub.add_parser("doctor")
    p = sub.add_parser("serve"); p.add_argument("--port", type=int, default=8765)
    sub.add_parser("help")
    args = parser.parse_args(argv)
    if args.cmd in (None, "help"):
        print(HELP)
        return 0
    from .harness import Harness
    handlers = {"search": cmd_search, "ask": cmd_ask, "chat": cmd_chat, "ingest": cmd_ingest,
                "lint": cmd_lint, "rename": cmd_rename, "doctor": cmd_doctor,
                "serve": lambda a, h: __import__("wiki.web", fromlist=["serve"]).serve(h, a.port)}
    try:
        online = getattr(args, "mode", "local") == "online"
        client = GeminiGemmaClient() if online else OllamaClient()
        return handlers[args.cmd](args, Harness(client)) or 0
    except LLMError as e:
        print(f"error: {e}", file=sys.stderr)
    except (LookupError, FileNotFoundError, FileExistsError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
