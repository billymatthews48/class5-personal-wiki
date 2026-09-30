"""Wiki pages for humans: subject notes, index.md, Source Catalog.md, lint and rename.

Note identity lives in properties (subject_key), never in the filename, so a note can be renamed
freely and re-ingestion finds it again instead of creating a duplicate.
"""
import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path, PurePosixPath

import yaml

from . import config, subjects as subjects_mod
from .harness import load_prompt

MANIFEST = config.STATE / "manifest.json"
LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")
BAD_TITLE = [
    (re.compile(r"[0-9a-f]{8,}", re.I), "looks like a hash or id"),
    (re.compile(r"\b(19|20)\d{2}[-_/.]?\d{2}"), "contains a date"),
    (re.compile(r"\b(export|task|chunk|untitled|copy of|conversation)\b", re.I), "machine/export word"),
    (re.compile(r"[\\/:*?\"<>|#^\[\]]"), "character Obsidian/Windows can't use"),
    (re.compile(r"[.!?]$"), "ends like a sentence"),
    (re.compile(r"_|--"), "slug-style separators"),
]


def validate_title(title):
    problems = [why for rx, why in BAD_TITLE if rx.search(title)]
    words = len(title.split())
    if not 1 <= words <= 6:
        problems.append(f"{words} words (want 2-6)")
    return problems


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"subjects": {}}


def save_manifest(m):
    MANIFEST.write_text(json.dumps(m, indent=2), encoding="utf-8")


def all_notes():
    return sorted(config.WIKI.rglob("*.md")) if config.WIKI.exists() else []


def read_note(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4)
        meta = yaml.safe_load(text[4:end]) or {}
        body = text[end + 5:]
    return meta, body


def find_note(subject_key):
    for p in all_notes():
        if read_note(p)[0].get("subject_key") == subject_key:
            return p
    return None


def section(body, heading):
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return m.group(1).strip() if m else ""


GENERIC_FOLDERS = {"lectures", "supervisions", "exam", "exams", "assessment", "assesment", "revision",
                   "lent", "michaelmas", "supervisions & assessment", "first week", "week 2", "paper 1",
                   "essay 1", "essay 2", "electives"}
ORIGIN_NAMES = {"mba": "MBA", "cambridge": "Cambridge", "added": "Added"}


def source_label(raw_path):
    """Readable link label: nearest meaningful folder + file name.
    'raw/cambridge/First week/MS6 Marketing/Lectures/Week 2 - CLV.docx' -> 'MS6 Marketing / Week 2 - CLV'"""
    p = PurePosixPath(raw_path)
    folders = [f for f in p.parts[1:-1] if f.lower() not in GENERIC_FOLDERS]
    near = folders[-1] if folders else ""
    near = ORIGIN_NAMES.get(near, near)
    stem = p.stem.strip()
    return f"{near} / {stem}" if near else stem


# ---------------- withheld originals ----------------
# Some originals stay on the owner's machine (third-party material, other people's words) and are
# git-ignored. Notes link to a committed stub page for each one instead of to the missing file,
# so every source link resolves in a clone of the repository.

WITHHELD_FILE = config.ROOT / "withheld.yaml"
WITHHELD_DIR = config.VAULT / "withheld"


def load_withheld():
    if not WITHHELD_FILE.exists():
        return {}
    data = yaml.safe_load(WITHHELD_FILE.read_text(encoding="utf-8")) or {}
    return {w["path"]: w for w in data.get("withheld", [])}


def stub_target(raw_path):
    """Vault-relative link target (no .md) of the stub page for a withheld original.
    Dots are removed from the name so Obsidian does not mistake part of it for a file extension."""
    p = PurePosixPath(raw_path)
    name = f"{p.stem.replace('.', '').strip()} ({p.suffix.lstrip('.').lower()})"
    return f"withheld/{name}"


def source_link(raw_path, withheld=None, table=False):
    """Wikilink to an original, or to its stub page if the original is withheld from the repo."""
    withheld = load_withheld() if withheld is None else withheld
    bar = "\\|" if table else "|"
    if raw_path in withheld:
        return f"[[{stub_target(raw_path)}{bar}{source_label(raw_path)} (kept local)]]"
    return f"[[{raw_path}{bar}{source_label(raw_path)}]]"


def write_withheld_stubs(report, titles):
    """(Re)write one stub page per withheld original and point existing note links at the stubs."""
    withheld = load_withheld()
    by_path = {r["raw_path"]: r for r in report}
    WITHHELD_DIR.mkdir(parents=True, exist_ok=True)
    wanted = set()
    for path, w in withheld.items():
        r = by_path.get(path, {})
        note = titles.get(r.get("subject"))
        stub = config.VAULT / (stub_target(path) + ".md")
        wanted.add(stub.name)
        lines = ["---", "type: withheld source", f"original_path: \"{path}\"",
                 f"sha256: {r.get('sha256', 'unknown')}", "---",
                 f"# {stub.stem}", "",
                 "**This original file is kept on my machine and is not published in this repository.**", "",
                 f"- **What it is:** {w['what']}",
                 f"- **Why it is not here:** {w['reason']}",
                 f"- **Original path:** `{path}`",
                 f"- **Fingerprint (sha256):** `{r.get('sha256', 'unknown')}`",
                 f"- **Passages indexed locally:** {r.get('passages', 'unknown')}",
                 f"- **Used by note:** {'[[' + note + ']]' if note else '(none)'}", "",
                 "On my machine the file is still indexed, so `wiki search` and `wiki ask` can find and cite its "
                 "passages. In a clone of this repository those passages are not available.", ""]
        stub.write_text("\n".join(lines), encoding="utf-8")
    for old in WITHHELD_DIR.glob("*.md"):
        if old.name not in wanted:
            old.unlink()
    # Point links in existing notes at the stubs (idempotent; new notes already use source_link).
    for p in all_notes():
        t = p.read_text(encoding="utf-8")
        t2 = t
        for path in withheld:
            t2 = re.sub(rf"\[\[{re.escape(path)}\|[^\]]*\]\]", lambda m, p=path: source_link(p, withheld), t2)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
    return len(withheld)


# ---------------- generation ----------------

NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_ideas": {"type": "array", "items": {"type": "object", "properties": {
            "idea": {"type": "string"}, "source": {"type": "string"}}, "required": ["idea", "source"]}},
        "related": {"type": "array", "items": {"type": "object", "properties": {
            "note": {"type": "string"}, "reason": {"type": "string"}}, "required": ["note", "reason"]}},
    },
    "required": ["summary", "key_ideas", "related"],
}


def pick_excerpts(files, chunks_by_file, budget=config.TITLE_INPUT_CHARS * 2, max_files=12):
    """Take the opening passages of up to max_files files, own-work formats first, within budget.
    This is how much of a subject Gemma sees when writing a note (~6000 chars ~ 1500 tokens)."""
    order = sorted(files, key=lambda f: (f.endswith(".pdf"), -len(chunks_by_file.get(f, []))))[:max_files]
    per = max(300, budget // max(1, len(order)))
    excerpts = []
    for f in order:
        text = " ".join(c["text"] for c in chunks_by_file.get(f, [])[:3])[:per]
        if text.strip():
            excerpts.append((f, text))
    return excerpts


def generate_note(client, subject, excerpts, other_titles):
    listing = "\n".join(f"[S{i}] {source_label(f)}\n{t}" for i, (f, t) in enumerate(excerpts, 1))
    messages = [
        {"role": "system", "content": load_prompt("note-writer.md")},
        {"role": "user", "content": f"Subject title: {subject.title}\n\nOther notes in the wiki:\n"
                                    + "\n".join(f"- {t}" for t in other_titles)
                                    + f"\n\nExcerpts:\n{listing}"},
    ]
    text, stats = client.chat(messages, temperature=0.2, fmt=NOTE_SCHEMA, max_tokens=900)
    data = json.loads(text)
    return data, stats


def render_note(subject, data, excerpts, files, other_titles, my_notes="", reviewed=False):
    label = {f"S{i}": f for i, (f, _) in enumerate(excerpts, 1)}
    withheld = load_withheld()
    ideas = []
    for item in data.get("key_ideas", []):
        src = label.get(item.get("source", "").strip("[] "))
        ref = f" ({source_link(src, withheld)})" if src else ""
        idea = re.sub(r"\s*\[S\d+\]", "", item["idea"]).strip()   # labels belong in the link, not the text
        ideas.append(f"- {idea}{ref}")
    related = [f"- [[{r['note']}]]: {r['reason'].strip()}" for r in data.get("related", [])
               if r.get("note") in other_titles and r.get("note") != subject.title]
    sources = [f"- {source_link(f, withheld)}" for f in sorted(files)]
    meta = {"subject_key": subject.key, "wiki_id": f"subj-{subject.key}", "topic": subject.folder,
            "source_count": len(files), "generated_by": config.CHAT_MODEL,
            "generated": date.today().isoformat(), "reviewed": reviewed}
    parts = ["---", yaml.safe_dump(meta, sort_keys=False).strip(), "---", f"# {subject.title}", "",
             data.get("summary", "").strip(), "", "## Key ideas", *ideas, "",
             "## Related", *(related or ["- (none yet)"]), "",
             "## Sources", *sources, "", "## My Notes", my_notes or "", ""]
    return "\n".join(parts)


def write_indexes(subjects, report):
    """Rebuild vault/index.md (human landing page) and vault/Source Catalog.md."""
    by_folder = {}
    for s in subjects:
        path = find_note(s.key)
        if not path:
            continue
        _, body = read_note(path)
        blurb = re.split(r"(?<=[.!?])\s", body.split("\n## ")[0].split("\n", 2)[-1].strip())[0]
        by_folder.setdefault(s.folder, []).append((path.stem, blurb))
    lines = ["# Academic Wiki", "",
             "Notes on my Cambridge Management Studies degree, Berkeley MBA coursework, and GitHub projects. "
             "Each note summarises one subject, links to related subjects, and cites the original files "
             "in `raw/`. See [[Source Catalog]] for every original file.", ""]
    for folder in sorted(by_folder):
        lines += [f"## {folder}", ""]
        lines += [f"- [[{t}]]: {b}" for t, b in sorted(by_folder[folder])] + [""]
    (config.VAULT / "index.md").write_text("\n".join(lines), encoding="utf-8")

    titles = {s.key: s.title for s in subjects}
    catalog = json.loads((config.STATE / "raw_catalog.json").read_text(encoding="utf-8")) \
        if (config.STATE / "raw_catalog.json").exists() else {}
    withheld = load_withheld()
    cat = ["# Source Catalog", "",
           "Every original file in `raw/`, unchanged. `sha256` is the fingerprint of the file; "
           "`passages` is how many retrieval passages it produced (0 = scanned, no text layer).", "",
           f"{len(withheld)} originals are kept on my machine and not published (third-party material, or other "
           "people's words). They are marked \"kept local\" and link to a page that says what the file is and why "
           "it is not here.", "",
           "| Original | Origin | Passages | Note | sha256 |", "|---|---|---|---|---|"]
    for r in sorted(report, key=lambda r: r["raw_path"]):
        origin = catalog.get(r["raw_path"], {}).get("origin", "added later")
        note = f"[[{titles[r['subject']]}]]" if r["subject"] in titles else "(none)"
        name = PurePosixPath(r["raw_path"]).name
        link = (f"[[{stub_target(r['raw_path'])}\\|{name} (kept local)]]" if r["raw_path"] in withheld
                else f"[[{r['raw_path']}\\|{name}]]")
        cat.append(f"| {link} | {origin} | "
                   f"{r['passages'] or '0 (no text layer)'} | {note} | `{r['sha256'][:12]}` |")
    (config.VAULT / "Source Catalog.md").write_text("\n".join(cat) + "\n", encoding="utf-8")
    write_withheld_stubs(report, titles)


# ---------------- lint ----------------

def lint():
    problems = []
    titles = {p.stem: p for p in all_notes()}
    incoming = {t: 0 for t in titles}
    withheld = load_withheld()
    ignored = {l.strip() for l in (config.ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()} \
        if (config.ROOT / ".gitignore").exists() else set()
    problems += [f"withheld.yaml: {path} is not listed in .gitignore" for path in withheld
                 if f"vault/{path}" not in ignored]
    for p in all_notes():
        meta, body = read_note(p)
        h1 = re.search(r"^# (.+)$", body, re.M)
        if not h1 or h1.group(1).strip() != p.stem:
            problems.append(f"{p.name}: first heading does not match filename")
        problems += [f"{p.name}: title {why}" for why in validate_title(p.stem)]
        if not meta.get("subject_key"):
            problems.append(f"{p.name}: missing subject_key property")
        if not section(body, "Sources"):
            problems.append(f"{p.name}: no Sources section")
        for target, _ in LINK.findall(body):
            target = target.strip()
            if target.startswith("raw/"):
                if not (config.VAULT / target).exists():
                    problems.append(f"{p.name}: broken source link {target}")
                elif target in withheld:
                    problems.append(f"{p.name}: links straight to a withheld original ({target}); "
                                    f"run `wiki ingest` so it points at the stub page")
            elif target.startswith("withheld/"):
                if not (config.VAULT / (target + ".md")).exists():
                    problems.append(f"{p.name}: broken link to withheld-source page {target}")
            elif target in titles:
                if target != p.stem:
                    incoming[target] += 1
            elif target not in ("Source Catalog", "index"):
                problems.append(f"{p.name}: broken link [[{target}]]")
    problems += [f"{t}.md: no incoming links from other notes" for t, n in incoming.items() if n == 0]
    return problems


# ---------------- rename ----------------

def rename(old, new):
    problems = validate_title(new)
    if problems:
        raise ValueError(f"'{new}' is not a good note name: {', '.join(problems)}")
    src = next((p for p in all_notes() if p.stem == old), None)
    if not src:
        raise FileNotFoundError(f"No note named '{old}'.")
    dest = src.with_name(f"{new}.md")
    if dest.exists():
        raise FileExistsError(f"'{new}.md' already exists.")
    config.ARCHIVE.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, config.ARCHIVE / f"{datetime.now():%Y%m%d-%H%M%S} {old}.md")
    meta, _ = read_note(src)
    text = src.read_text(encoding="utf-8").replace(f"\n# {old}\n", f"\n# {new}\n", 1)
    dest.write_text(text, encoding="utf-8")
    src.unlink()
    changed = []
    for p in [*all_notes(), config.VAULT / "index.md", config.VAULT / "Source Catalog.md"]:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        t2 = re.sub(rf"\[\[{re.escape(old)}(\|[^\]]*)?\]\]", lambda m: f"[[{new}{m.group(1) or ''}]]", t)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            changed.append(p.name)
    # subjects.yaml is the naming source of truth, so re-ingestion keeps the new name.
    y = config.SUBJECTS_FILE.read_text(encoding="utf-8")
    config.SUBJECTS_FILE.write_text(re.sub(rf"(\n\s+title:\s*){re.escape(old)}\s*\n", rf"\g<1>{new}\n", y),
                                    encoding="utf-8")
    m = load_manifest()
    if meta.get("subject_key") in m["subjects"]:
        m["subjects"][meta["subject_key"]]["note_path"] = dest.relative_to(config.VAULT).as_posix()
        save_manifest(m)
    return dest, changed
