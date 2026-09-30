"""Human review pass over Gemma-written notes.

Each correction below was decided by opening the cited original (see evidence/review/). The script
applies them to the notes, marks each reviewed note `reviewed: true`, and writes the review log.
Originals in raw/ are never changed; only the wiki notes are corrected.
Safe to re-run: a correction whose "old" text is no longer present is skipped.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from wiki import config, notes   # noqa: E402

R = "raw/cambridge/Electives/Strategic management/"

# (note title, kind, old text or regex, new text, reason)
EDITS = [
    ("Microeconomics", "text", "The owner's work explores", "Billy's work explores",
     "Wording: the prompt at the time produced 'the owner'."),
    ("Macroeconomics", "text", "as per the Fischer equation", "as per the Fisher equation (spelled 'Fischer' in the lecture notes)",
     "The source notes misspell Fisher; the note now says so rather than repeating it silently."),
    ("Technology Adoption Curves", "regex", r"\bThe author\b", "Billy", "Wording."),
    ("Organizational Behaviour", "text",
     "Eastern cultures tend to favor holistic perception and relationship-based categorization, contrasting with Western analytical preferences.",
     "Easterners tend to prefer holistic perception (the whole field, including background), while Westerners are more analytical and focus on the focal object.",
     "UNSUPPORTED DETAIL: 'relationship-based categorization' is not in Week 4 - Perception; the source says holistic vs analytical only."),
    ("Strategic Management", "regex",
     r"(- Strategy is defined as objectives, policies, and plans[^\n]*?)\s*\[S1, S11\]",
     rf"\1 ([[{R}Crib sheet.docx|Strategic management / Crib sheet]])",
     "MISSING SOURCE LINK: Gemma returned two labels, so no link was rendered. Definition confirmed in the Crib sheet."),
    ("Strategic Management", "regex",
     r"(- Hybrid hotel models are proposed[^\n]*?)\s*\[S2, S3, S4\]",
     rf"\1 ([[{R}Supervisions & assessment/Assessment/1114L-MSE12-INDIVIDUAL-ESSAY.docx|Strategic management / 1114L-MSE12-INDIVIDUAL-ESSAY]])",
     "MISSING SOURCE LINK: claim confirmed in the introduction of the individual essay."),
]

# Related links rewritten by hand. Generic reasons ("both involve strategy") were removed; each
# kept or added link names a shared concept that was confirmed in both subjects' originals.
RELATED = {
    "Microeconomics": [
        ("Strategic Management", "The MBA economics memo argues for escaping the Bertrand trap through differentiation and barriers to entry; the strategy crib sheet analyses the same industry forces with Porter's 5 Forces."),
        ("Energy Transition", "The energy memo proposes a platform for buying electricity from competing retail suppliers in Texas, negotiating price and quantity bands: a competition and pricing problem."),
    ],
    "Macroeconomics": [
        ("Strategic Management", "Both contain an essay on Covid-19: the macro essay explains the 2020 global recession, and the strategy essay asks how hybrid hotels can come through the same disruption."),
    ],
    "Strategic Management": [
        ("Macroeconomics", "The individual essay on hybrid hotels is set in the Covid-19 disruption that the macroeconomics essay explains as a global recession."),
        ("Microeconomics", "Porter's 5 Forces in the crib sheet (barriers to entry, rivalry) covers the same industry-structure ideas as the microeconomics work on market power and concentration."),
        ("Technology Adoption Curves", "Week 5 (disruption strategy) and the technology essay both deal with how strategy must change as a technology matures."),
    ],
    "Technology Adoption Curves": [
        ("Strategic Management", "The essay's point that a firm's playbook differs between the fluid and transitional phases connects to the Week 5 disruption-strategy lecture in Strategic Management."),
        ("Power and Influence", "Both essays are framed around Billy's post-MBA consulting role at Bain."),
    ],
    "Brand Management": [
        ("Marketing Strategy", "The Tata Group assignment in Marketing Strategy compares 'branded house' and 'house of brands'; the Quest and Avocados from Mexico work here builds a single brand position."),
    ],
    "Marketing Strategy": [
        ("Brand Management", "The Tata Group analysis of 'branded house' versus 'house of brands' is the portfolio-level view of the single-brand positioning work in Brand Management."),
    ],
    "Leading People": [
        ("Negotiation", "The second teaching session explains reservation price and the zone of possible agreement; the Negotiations elective applies the same bargaining ideas (walk-away price, BATNA) to live exercises."),
    ],
    "Negotiation": [
        ("Leading People", "Reservation price and ZOPA are taught to the AI student in Leading People; the negotiation journal applies the related ideas of walk-away price and BATNA in the Salt Harbour, MedLee and Harborco exercises."),
        ("Power and Influence", "The negotiation journal uses power-dependence theory (BATNAs as a source of power); the Power and Influence essays analyse sources of power at Bain."),
    ],
    "Organizational Behaviour": [
        ("Power and Influence", "Week 8 defines leadership as intentionally influencing others; the Power and Influence essays analyse how that influence is built (credibility, likeability)."),
    ],
    "Power and Influence": [
        ("Negotiation", "BATNAs as a source of power in the negotiation journal connect to the essay's analysis of formal and informal power."),
        ("Organizational Behaviour", "The essay's informal power sources (expertise, social capital) relate to the OB notes' definition of leadership as influencing others."),
        ("Technology Adoption Curves", "Both essays are framed around Billy's post-MBA consulting role at Bain."),
    ],
    "Energy Transition": [
        ("Microeconomics", "The memo has firms buying electricity from competing retail suppliers and negotiating price and quantity bands; the microeconomics notes cover competition, pricing and market power."),
    ],
}


def main():
    titles = {p.stem: p for p in notes.all_notes()}
    log = ["# Note review log", "",
           "Every generated note was checked against its original files (term coverage in "
           "[term_coverage.md](term_coverage.md), plus targeted searches of the cited files for each "
           "name, quote and number). Corrections were made in the wiki notes only; originals are unchanged.", "",
           "## Text corrections", "", "| Note | Change | Reason |", "|---|---|---|"]
    for title, kind, old, new, why in EDITS:
        p = titles.get(title)
        if not p:
            continue
        t = p.read_text(encoding="utf-8")
        t2 = re.sub(old, new, t) if kind == "regex" else t.replace(old, new)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            log.append(f"| {title} | `{old[:60]}` -> `{new[:70]}` | {why} |")
    for p in titles.values():     # stray [S#] labels left inside idea text by early generations
        t = p.read_text(encoding="utf-8")
        t2 = re.sub(r"\s*\[S\d+(?:,\s*S\d+)*\]\.?(?= \(\[\[)", "", t)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            log.append(f"| {p.stem} | removed `[S#]` labels from idea text | Labels belong in the source link, not the sentence. |")

    log += ["", "## Related links (rewritten by hand)", "",
            "Gemma's first-pass links often had generic reasons. Each link below names a shared concept confirmed in both subjects' originals.", ""]
    for title, links in RELATED.items():
        p = titles.get(title)
        if not p:
            continue
        t = p.read_text(encoding="utf-8")
        old = notes.section(t, "Related")
        keep = [f"- [[{n}]]: {r}" for n, r in links if n in titles]
        new_block = "\n".join(keep) if keep else "- (none)"
        t2 = re.sub(r"(^## Related\n)(.*?)(?=^## )", lambda m: m.group(1) + new_block + "\n\n", t, flags=re.S | re.M)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
        removed = [l for l in old.splitlines() if l.strip() and l not in keep]
        log.append(f"**{title}**")
        log += [f"- kept/added: [[{n}]]: {r}" for n, r in links if n in titles]
        log += [f"- removed: {l.lstrip('- ')}" for l in removed]
        log.append("")

    reviewed = []
    for p in notes.all_notes():
        t = p.read_text(encoding="utf-8")
        if p.stem in REVIEWED and "reviewed: false" in t:
            p.write_text(t.replace("reviewed: false", "reviewed: true", 1), encoding="utf-8")
        if p.stem in REVIEWED:
            reviewed.append(p.stem)
    log += ["## Notes marked reviewed", "", ", ".join(sorted(reviewed)), ""]
    out = config.ROOT / "evidence" / "review" / "note_review.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(log), encoding="utf-8")
    print(f"review applied; log at {out}")


REVIEWED = set(RELATED)   # extended as further notes are reviewed

if __name__ == "__main__":
    main()
