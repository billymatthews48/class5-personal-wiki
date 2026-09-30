"""Check the repository the way a grader sees it: clone it fresh and resolve every link.

    python tests/clone_link_check.py
Clones the local repository's committed state into a temporary folder (so git-ignored files are
absent, exactly as on GitHub), then checks that
  * every [[wikilink]] in the cloned vault (notes, index, Source Catalog, stub pages) resolves, and
  * every relative Markdown link in README.md and the evidence write-ups resolves.
Writes evidence/clone-link-check.md. Run it after committing.
"""
import re
import subprocess
import sys
import tempfile
import urllib.parse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKILINK = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\\?\|[^\]]*)?\]\]")
MDLINK = re.compile(r"\]\(([^)#][^)]*)\)")


def main():
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "clone"
        subprocess.run(["git", "clone", "-q", str(ROOT), str(clone)], check=True)
        vault = clone / "vault"
        md_files = sorted(vault.rglob("*.md"))
        by_stem = {}
        for p in md_files:
            by_stem.setdefault(p.stem, []).append(p)
        total, broken = 0, []
        for p in md_files:
            for target in WIKILINK.findall(p.read_text(encoding="utf-8")):
                target = target.strip()
                total += 1
                ok = ((vault / target).exists() or (vault / (target + ".md")).exists()
                      or ("/" not in target and target in by_stem))
                if not ok:
                    broken.append(f"{p.relative_to(clone).as_posix()}: [[{target}]]")
        md_total, md_broken = 0, []
        docs = [clone / "README.md", *sorted((clone / "evidence").rglob("*.md")), *sorted((clone / "docs").rglob("*.md"))]
        for p in docs:
            for link in MDLINK.findall(p.read_text(encoding="utf-8")):
                if link.startswith(("http://", "https://", "mailto:")):
                    continue
                md_total += 1
                if not (p.parent / urllib.parse.unquote(link)).exists():
                    md_broken.append(f"{p.relative_to(clone).as_posix()}: ({link})")
        raw_files = sum(1 for f in (vault / "raw").rglob("*") if f.is_file())
        stubs = sum(1 for f in (vault / "withheld").glob("*.md")) if (vault / "withheld").exists() else 0
        notes = sum(1 for f in (vault / "wiki").rglob("*.md"))

    lines = ["# Link check on a fresh clone", "",
             f"Run {datetime.now():%Y-%m-%d %H:%M} against commit `{commit}`, cloned into a temporary folder so that "
             "git-ignored files are absent, as they are on GitHub.", "",
             "| Check | Result |", "|---|---|",
             f"| Wiki notes in the clone | {notes} |",
             f"| Original files in `vault/raw/` in the clone | {raw_files} |",
             f"| Stub pages for originals kept local | {stubs} |",
             f"| Wikilinks checked in the vault (notes, index, Source Catalog, stubs) | {total} |",
             f"| Broken wikilinks | **{len(broken)}** |",
             f"| Relative links checked in README.md, evidence/ and docs/ | {md_total} |",
             f"| Broken relative links | **{len(md_broken)}** |", ""]
    if broken or md_broken:
        lines += ["## Broken", ""] + [f"- {b}" for b in broken + md_broken] + [""]
    out = ROOT / "evidence" / "clone-link-check.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 1 if broken or md_broken else 0


if __name__ == "__main__":
    sys.exit(main())
