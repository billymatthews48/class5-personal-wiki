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
    ("Mott MacDonald Consulting Project", "regex",
     r"- The project aimed to determine what the future multi-disciplinary consultancy office should look like\.[^\n]*",
     "- The project, titled 'Office of the future', set out to understand what future offices need to look like for the "
     "company to stay successful. An earlier 2018 group project on the same question is also in the sources. "
     "([[raw/cambridge/Electives/Project/PID.docx|Project / PID]])",
     "WRONG ATTRIBUTION: the note cited a previous team's 2018 slide deck as the aim of this project. The aim is in the PID."),
    ("Custom LLM Training", "text",
     "Language evaluation scores were based on four-choice next-word selections, where 1 indicated the highest probability.",
     "Each language eval is a four-choice next-word selection: a case scores 1 when the correct word has the highest probability, and 0 otherwise.",
     "IMPRECISE: '1 indicated the highest probability' misreads the scoring rule in eval_comparison.md and ASSIGNMENT.md."),
    ("Management Studies Revision", "text",
     "The impact of collusion on society includes the loss of agglomeration economies from labour poaching.",
     "For the no-poaching collusion question, the noted consequences include X-inefficiency for the firms and the loss of the agglomeration economies that 'poaching' brings.",
     "IMPRECISE: the source lists the loss of agglomeration economies of 'poaching' as a consequence of firms agreeing not to poach, not of poaching itself."),
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


# Second review pass (all 21 notes). Entries here replace the first-pass lists above.
RELATED.update({
    "Microeconomics": [
        ("Strategic Management", "The MBA economics memo argues for escaping the Bertrand trap through differentiation and barriers to entry; the strategy crib sheet analyses the same industry forces with Porter's 5 Forces."),
        ("Energy Transition", "The energy memo proposes a platform for buying electricity from competing retail suppliers in Texas, negotiating price and quantity bands: a competition and pricing problem."),
        ("Management Studies Revision", "The revision answer summaries cover the collusion essay question (what makes collusion possible, welfare consequences) answered in full in the MS3 essays."),
    ],
    "Strategic Management": [
        ("Macroeconomics", "The individual essay on hybrid hotels is set in the Covid-19 disruption that the macroeconomics essay explains as a global recession."),
        ("Microeconomics", "Porter's 5 Forces in the crib sheet (barriers to entry, rivalry) covers the same industry-structure ideas as the microeconomics work on market power and concentration."),
        ("Operations Management", "Supervision 1 asks what guests' order winners, qualifiers and losers are when choosing a hotel; that framework is taught in Operations Management (Week 2)."),
        ("Technology Adoption Curves", "Week 5 (disruption strategy) and the technology essay both deal with how strategy must change as a technology matures."),
        ("Netflix Live Sports Strategy", "The Netflix project applies strategy analysis (positioning, competitive advantage) to one company's choice about live sports."),
    ],
    "Marketing Strategy": [
        ("Brand Management", "The Tata Group analysis of 'branded house' versus 'house of brands' is the portfolio-level view of the single-brand positioning work in Brand Management."),
        ("Finance and Accounting", "Customer Lifetime Value is defined in Week 2 as the NPV of a customer's cash flows, the same present-value method used for project appraisal in finance."),
        ("Operations Management", "The 4 Ps are the marketing view of the offering; the supply-chain lecture argues customer experience is determined by the supply chain, not the 4 Ps."),
    ],
    "Organizational Behaviour": [
        ("Power and Influence", "Week 8 defines leadership as intentionally influencing others; the Power and Influence essays analyse how that influence is built (credibility, likeability)."),
        ("Mott MacDonald Consulting Project", "Week 3 defines organisational culture; the Mott interviews describe a concrete one (open, close-knit, not hierarchical)."),
        ("Management Studies Revision", "The revision summaries cover the motivation essay question (motivation theories, expectancy theory) from the MS1 course."),
    ],
    "Power and Influence": [
        ("Negotiation", "BATNAs as a source of power in the negotiation journal connect to the essay's analysis of formal and informal power."),
        ("Organizational Behaviour", "The essay's informal power sources (expertise, social capital) relate to the OB notes' definition of leadership as influencing others."),
        ("Career Networking and Visibility", "The second assignment is about improving likeability; 'liking' is the first principle of influence in the personal development notes."),
        ("Technology Adoption Curves", "Both essays are framed around Billy's post-MBA consulting role at Bain."),
    ],
    "Leading People": [
        ("Negotiation", "The second teaching session explains reservation price and the zone of possible agreement; the Negotiations elective applies the same bargaining ideas (walk-away price, BATNA) to live exercises."),
        ("Business Communication", "The first teaching session explains diversity, equity and inclusion; the Business Communication assignments analyse DEI in practice (Rivkin's hiring steps, whether DEI is zero-sum)."),
    ],
    "Business Communication": [
        ("Leading People", "Both deal with diversity, equity and inclusion: the assignments here analyse Rivkin's steps to increase diversity, and Leading People has Billy teaching the DEI definitions."),
    ],
    "Career Networking and Visibility": [
        ("Power and Influence", "The principles of influence listed here start with liking; the Power and Influence assignment is a plan to improve likeability."),
        ("Secure Networking Tracker", "The notes give advice on building a network; the tracker app is a tool for keeping track of those contacts."),
    ],
    "Operations Management": [
        ("Strategic Management", "Order winners, qualifiers and losers (Week 2) are reused in the strategy supervision on how guests choose hotels."),
        ("Marketing Strategy", "The supply-chain lecture claims customer experience is determined by the supply chain rather than the 4 Ps taught in marketing."),
        ("Management Studies Revision", "The MS5 column of the revision table lists the same lecture sequence: Zara, process design, quality, six sigma, lean."),
    ],
    "Quantitative Methods": [
        ("Custom LLM Training", "The machine learning lecture introduces supervised learning from labelled data; the nanoGPT project trains and evaluates an actual language model."),
        ("Management Studies Revision", "The MS2 column of the revision table lists parameter estimation, hypothesis testing, decision analysis, Monte Carlo simulation and regression."),
    ],
    "Finance and Accounting": [
        ("Marketing Strategy", "NPV from project appraisal is the method behind Customer Lifetime Value, defined in the marketing notes as the NPV of a customer's cash flows."),
        ("Management Studies Revision", "The MS4 column of the revision table lists cash flows, present values and stock valuation."),
    ],
    "Mott MacDonald Consulting Project": [
        ("Organizational Behaviour", "The interviews describe Mott MacDonald's culture (open, close-knit, not hierarchical), an example of the organisational culture concept from OB Week 3."),
        ("Strategic Management", "Both look at working life after Covid-19: this project asks what the office should become, and the strategy essay notes remote working's effect on young professionals."),
    ],
    "Custom LLM Training": [
        ("Quantitative Methods", "The Cambridge machine learning lecture covers learning from data in theory; this project trains a small transformer and measures it on 48 fixed evals."),
        ("Secure Networking Tracker", "Both are Billy's GitHub software projects, documented through their READMEs."),
    ],
    "Secure Networking Tracker": [
        ("Career Networking and Visibility", "The app tracks networking contacts; the personal development notes explain why and how to build that network."),
        ("Custom LLM Training", "Both are Billy's GitHub software projects, documented through their READMEs."),
    ],
    "Management Studies Revision": [
        ("Organizational Behaviour", "MS1: the answer summaries cover the motivation question (motivation theories, expectancy theory)."),
        ("Quantitative Methods", "MS2: the revision table lists hypothesis testing, decision analysis, Monte Carlo simulation and regression."),
        ("Microeconomics", "MS3: the answer summaries cover the collusion question (what makes collusion possible, welfare consequences)."),
        ("Finance and Accounting", "MS4: the revision table lists cash flows, present values and stock valuation."),
        ("Operations Management", "MS5: the revision table lists Zara, process design, quality management, six sigma and lean."),
        ("Marketing Strategy", "MS6: the revision table lists CLV, segmentation, product and price."),
    ],
    "Netflix Live Sports Strategy": [
        ("Strategic Management", "A strategy project: it weighs a deep commitment to live sports against Netflix's existing positioning and long-term competitive advantage."),
    ],
})


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
        # the log lists every correction, whether applied in this run or an earlier one
        log.append(f"| {title} | `{old[:70]}` -> `{new[:90]}` | {why} |")
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
