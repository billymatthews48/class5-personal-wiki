"""Copy the chosen academic originals into vault/raw/ byte-for-byte.

Originals on OneDrive/GitHub are only read. Each copy is verified by sha256; identical files
found at several paths are copied once and the extra paths are logged. Writes
.wiki/raw_catalog.json, which ingest later turns into vault/Source Catalog.md.
Run once while online (OneDrive placeholders download on read; git clone needs network).
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "vault" / "raw"
ONEDRIVE = Path.home() / "OneDrive" / "Documents"

KEEP = {".docx", ".pdf", ".pptx", ".pptm", ".md", ".txt"}
SKIP_NAMES = {  # non-academic files found inside the academic folders
    "Billy Matthews - Application for award.docx",
    "Billy Matthews - cover letter.docx",
    "HCC Billy Matthews.pptm",
}
GITHUB_REPOS = ["billymatthews48/Assignment-1", "billymatthews48/class4-custom-llm"]
GITHUB_DOCS = {"README.md", "ASSIGNMENT.md", "EXPERIMENT_LOG.md", "STUDENT_README.md",
               "COURSE_README.md", "eval_comparison.md"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def copy_tree(src_root, dest_root, catalog, seen, origin):
    for src in sorted(p for p in src_root.rglob("*") if p.is_file()):
        if src.suffix.lower() not in KEEP or src.name in SKIP_NAMES or src.name.startswith("~$"):
            continue
        digest = sha256(src)
        rel_src = src.relative_to(src_root)
        if digest in seen:
            catalog[seen[digest]]["duplicates"].append(f"{origin}/{rel_src.as_posix()}")
            continue
        dest = dest_root / rel_src
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or sha256(dest) != digest:
            shutil.copy2(src, dest)
        assert sha256(dest) == digest, f"copy mismatch: {src}"
        key = dest.relative_to(RAW.parent).as_posix()   # e.g. raw/mba/Marketing/Hwk 3.docx
        seen[digest] = key
        catalog[key] = {"sha256": digest, "origin": f"{origin}/{rel_src.as_posix()}",
                        "bytes": dest.stat().st_size, "duplicates": []}


def main():
    catalog, seen = {}, {}
    copy_tree(ONEDRIVE / "MBA academics", RAW / "mba", catalog, seen, "OneDrive/MBA academics")
    copy_tree(ONEDRIVE / "Cambridge academics" / "Year 3", RAW / "cambridge", catalog, seen,
              "OneDrive/Cambridge academics/Year 3")
    with tempfile.TemporaryDirectory() as tmp:
        for repo in GITHUB_REPOS:
            name = repo.split("/")[1]
            clone = Path(tmp) / name
            subprocess.run(["git", "clone", "--depth", "1", f"https://github.com/{repo}.git",
                            str(clone)], check=True, capture_output=True)
            commit = subprocess.run(["git", "-C", str(clone), "rev-parse", "HEAD"],
                                    capture_output=True, text=True).stdout.strip()
            docs = Path(tmp) / f"{name}-docs"
            for p in clone.rglob("*.md"):
                if p.name in GITHUB_DOCS and ".git" not in p.parts:
                    target = docs / p.relative_to(clone)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, target)
            if docs.exists():
                copy_tree(docs, RAW / "github" / name, catalog, seen,
                          f"github.com/{repo}@{commit[:7]}")
    out = ROOT / ".wiki" / "raw_catalog.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    dups = sum(len(v["duplicates"]) for v in catalog.values())
    print(f"copied {len(catalog)} unique files into {RAW} ({dups} duplicate paths skipped)")


if __name__ == "__main__":
    sys.exit(main())
