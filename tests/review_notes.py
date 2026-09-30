"""Review aid: check every generated key idea against the original file it cites.

    python tests/review_notes.py
For each "Key ideas" bullet it takes the distinctive terms (quoted phrases, capitalised names,
numbers, longer words) and measures how many occur in (a) the cited raw file and (b) any raw file
of that subject. Low coverage flags a claim for a human to open and check; it does not prove a
claim wrong, and high coverage does not prove it right. Writes evidence/review/term_coverage.md.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.common import EVIDENCE, write        # noqa: E402
from wiki import index_store, notes             # noqa: E402

COMMON = set("""about above across after against along among around because before behind between beyond
during through under until within without which while where whose their there these those being
should would could other another rather first second often such into than then them they this that
with from have been were will also more most some many much very both each only over when what
including involves involve focus focuses requires require based using used uses key core billy""".split())


def terms(idea):
    quoted = re.findall(r"['‘’\"“”]([^'‘’\"“”]{3,40})['‘’\"“”]", idea)
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-]{5,}|\d[\d.,%]*", idea) if w.lower() not in COMMON]
    return quoted, words


def coverage(words, text):
    if not words:
        return 1.0, []
    low = text.lower()
    missing = [w for w in words if w.lower().rstrip("s") not in low]
    return 1 - len(missing) / len(words), missing


def main():
    chunks = index_store.load_chunks()
    by_file, by_subject = {}, {}
    for c in chunks:
        by_file[c["raw_path"]] = by_file.get(c["raw_path"], "") + "\n" + c["text"]
        by_subject[c["subject"]] = by_subject.get(c["subject"], "") + "\n" + c["text"]
    out = ["# Key-idea term coverage against cited originals", "",
           "Coverage = share of an idea's distinctive terms found in the cited file / in any file of the subject. "
           "Rows under 60% in the cited file, or with a missing quoted phrase, were opened and checked by hand.", "",
           "| Note | Idea (start) | Cited file | In cited | In subject | Missing terms |", "|---|---|---|---|---|---|"]
    flagged = 0
    stub_to_raw = {notes.stub_target(path): path for path in notes.load_withheld()}
    for p in notes.all_notes():
        meta, body = notes.read_note(p)
        for line in notes.section(body, "Key ideas").splitlines():
            m = re.search(r"\(\[\[((?:raw|withheld)/[^|\]]+)\|([^\]]*)\]\]\)", line)
            idea = re.sub(r"\(\[\[(?:raw|withheld)/.*$", "", line).lstrip("- ").strip()
            quoted, words = terms(idea)
            subj_text = by_subject.get(meta.get("subject_key"), "")
            # a link to a withheld-source stub page stands for the original it describes
            cited = stub_to_raw.get(m.group(1), m.group(1)) if m else None
            cited_text = by_file.get(cited, "") if m else ""
            c_cov, c_missing = coverage(words, cited_text) if m else (0.0, words)
            s_cov, _ = coverage(words, subj_text)
            q_missing = [q for q in quoted if q.lower() not in (cited_text or subj_text).lower()]
            flag = (c_cov < 0.6) or bool(q_missing) or not m
            flagged += flag
            out.append(f"| {p.stem} | {'**CHECK** ' if flag else ''}{idea[:70]} | {m.group(2) if m else '(no source link)'} | "
                       f"{c_cov:.0%} | {s_cov:.0%} | {', '.join((['\"' + q + '\"' for q in q_missing] + c_missing)[:6])} |")
    out.insert(3, f"{flagged} ideas flagged for manual checking.")
    write(EVIDENCE / "review" / "term_coverage.md", "\n".join(out) + "\n")
    print("\n".join(l for l in out if "CHECK" in l or l.startswith(str(flagged))))


if __name__ == "__main__":
    main()
