"""`wiki ingest`: raw files -> retrieval index -> Gemma-written subject notes -> index.md.

Re-ingestion is idempotent. A subject note is regenerated only when the sha256 set of its raw
files changes; it is found by its subject_key property (not its filename), rewritten in place,
keeps its current name, and keeps anything under "## My Notes".
"""
import json
import shutil
import time
from pathlib import Path

from . import config, index_store, notes, subjects as subjects_mod
from .ingest import supported
from .llm import OllamaClient


def copy_into_raw(path, progress):
    """A source outside vault/raw is copied in unchanged (sha256-verified), never moved or edited."""
    src = Path(path).resolve()
    if src.is_relative_to(config.RAW.resolve()):
        return src
    dest = config.RAW / "added" / src.name
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        assert index_store.sha256_file(src) == index_store.sha256_file(dest)
    progress(f"copied {src} -> {dest.relative_to(config.VAULT)} (original untouched)")
    return dest


def ingest(path=None, client=None, force=False, progress=print):
    client = client or OllamaClient()
    t0 = time.perf_counter()
    target = copy_into_raw(path, progress) if path else config.RAW.resolve()
    if not target.exists():
        raise FileNotFoundError(f"{path} does not exist.")
    subs = subjects_mod.load()
    titles = {s.key: s.title for s in subs}

    chunks, report = index_store.build_chunks(progress)
    index_store.embed_chunks(client, chunks, titles, progress)

    in_scope = {r["raw_path"] for r in report
                if (config.VAULT / r["raw_path"]).resolve().is_relative_to(target)}
    unmapped = sorted(r["raw_path"] for r in report if r["subject"] is None and r["raw_path"] in in_scope)
    for u in unmapped:
        progress(f"note: {u} matches no subject in subjects.yaml; it is searchable but not in a note")

    chunks_by_file = {}
    for c in chunks:
        chunks_by_file.setdefault(c["raw_path"], []).append(c)
    manifest = notes.load_manifest()
    summary = {"written": [], "unchanged": [], "notes_stats": []}

    for s in subs:
        files = sorted(r["raw_path"] for r in report if r["subject"] == s.key)
        if not files or not in_scope.intersection(files):
            continue
        hashes = {r["raw_path"]: r["sha256"] for r in report if r["subject"] == s.key}
        existing = notes.find_note(s.key)
        prev = manifest["subjects"].get(s.key, {})
        if existing and prev.get("source_hashes") == hashes and not force:
            summary["unchanged"].append(existing.stem)
            continue
        my_notes, reviewed = "", False
        if existing:
            meta, body = notes.read_note(existing)
            my_notes = notes.section(body, "My Notes")
        dest = existing or (config.VAULT / s.note_path)   # keep whatever name the note has now
        progress(f"writing note '{dest.stem}' from {len(files)} files ...")
        excerpts = notes.pick_excerpts(files, chunks_by_file)
        others = [t for k, t in titles.items() if k != s.key]
        data, stats = notes.generate_note(client, s, excerpts, others)
        gen_dir = config.STATE / "generated"            # keep Gemma's raw JSON for review/re-render
        gen_dir.mkdir(parents=True, exist_ok=True)
        (gen_dir / f"{s.key}.json").write_text(json.dumps({"excerpts": excerpts, "data": data, "stats": stats},
                                                          indent=2, ensure_ascii=False), encoding="utf-8")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(notes.render_note(s, data, excerpts, files, others, my_notes, reviewed), encoding="utf-8")
        manifest["subjects"][s.key] = {"note_path": dest.relative_to(config.VAULT).as_posix(),
                                       "wiki_id": f"subj-{s.key}", "source_hashes": hashes}
        notes.save_manifest(manifest)
        summary["written"].append(dest.stem)
        summary["notes_stats"].append({"note": dest.stem, **{k: v for k, v in stats.items() if k != "tool_calls"}})
        progress(f"  done in {stats['wall_s']}s ({stats['prompt_tokens']} prompt tok, {stats['gen_tokens']} out)")

    notes.write_indexes(subs, report)
    summary.update(raw_files=len(report), passages=len(chunks), unmapped=unmapped,
                   wall_s=round(time.perf_counter() - t0, 1))
    progress(f"ingest finished in {summary['wall_s']}s: {len(summary['written'])} notes written, "
             f"{len(summary['unchanged'])} unchanged, {len(chunks)} passages indexed")
    return summary
