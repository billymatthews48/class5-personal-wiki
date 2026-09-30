"""Run the four ask-mode tests and the chat/search mode checks through the real harness.

    python tests/run_tests.py [--label offline]
Writes evidence/<label>/ask/T*.md (evidence cards), evidence/<label>/mode_checks.md and summary.md.
Automated checks are recorded as-is; the "Assessment" section of each card is written by a human
after opening the cited sources.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.common import EVIDENCE, CountingClient, dump, environment, write   # noqa: E402
from wiki.harness import Harness                                              # noqa: E402

QUESTIONS = yaml.safe_load((Path(__file__).parent / "questions.yaml").read_text(encoding="utf-8"))


def ask_card(q, rec, env):
    retrieved = [p["raw_path"] for p in rec["retrieved"]]
    cited_paths = {s.split(" (")[0].split("] ", 1)[1] for s in rec["sources"]}
    checks = {"status_as_expected": rec["status"] == q["expected_behavior"].replace("answer", "answered")
              if q["expected_behavior"] == "answer" else rec["status"] == "insufficient_evidence"}
    if q["expected_sources"]:
        checks["expected_source_retrieved"] = any(s in retrieved for s in q["expected_sources"])
        checks["expected_source_cited"] = any(s in cited_paths for s in q["expected_sources"])
        missing = [w for w in q.get("must_mention", []) if w.lower() not in rec["answer"].lower()]
        checks["mentions_key_facts"] = not missing
    passed = all(checks.values())
    md = [f"# {q['id']}: {q['type']}", "",
          f"- **Question:** {q['question']}",
          f"- **Expected behaviour:** {q['expected_behavior']}",
          f"- **Expected source(s):** {', '.join(f'`{s}`' for s in q['expected_sources']) or 'none'}",
          f"- **Expected passage:** {q.get('expected_passage') or q.get('note', '')}",
          f"- **Model:** {rec['model']} | **Execution:** {rec['execution']} | **Internet:** {env['internet']} | {rec['time']}",
          "", "## Retrieved passages (what Gemma was shown, in order)", ""]
    for i, p in enumerate(rec["retrieved"], 1):
        md += [f"{i}. `{p['raw_path']}` ({p['locator']}) cosine {p['cosine']} bm25 {p['bm25']}",
               "   > " + re.sub(r"\s+", " ", p["text"])[:600], ""]
    md += ["## Actual answer", "", rec["answer"], ""]
    if rec.get("raw_answer") and rec["raw_answer"] != rec["answer"]:
        md += ["Raw model output:", "", "> " + rec["raw_answer"].replace("\n", "\n> "), ""]
    md += ["## Citations", ""] + ([f"- {s}" for s in rec["sources"]] or ["- none"]) + [""]
    md += ["## Automated checks", ""] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()]
    st = rec.get("stats") or {}
    if st:
        md += ["", f"Timing: {st['wall_s']}s wall, first token {st['ttft_s']}s, {st['prompt_tokens']} prompt tokens, "
                   f"{st['gen_tokens']} generated ({st['gen_tok_s']} tok/s)."]
    md += ["", "## Assessment", "", "_(to be written after checking the cited passages against the claims)_", ""]
    return passed, checks, "\n".join(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="online-dev", help="evidence subfolder, e.g. offline")
    args = ap.parse_args()
    out = EVIDENCE / args.label
    env = environment()
    client = CountingClient()
    h = Harness(client)
    summary = [f"# Test run: {args.label}", "", "```", *[f"{k}: {v}" for k, v in env.items()], "```", "",
               "| Check | Result | Detail |", "|---|---|---|"]

    # ---- four ask-mode research questions (standalone) ----
    for q in QUESTIONS["ask"]:
        print(f"ask {q['id']} ...", flush=True)
        rec = h.ask(q["question"])
        passed, checks, md = ask_card(q, rec, env)
        write(out / "ask" / f"{q['id']}.md", md)
        dump(out / "ask" / f"{q['id']}.json", rec)
        summary.append(f"| ask {q['id']} ({q['type']}) | {'PASS' if passed else 'FAIL'} | "
                       f"status={rec['status']}, cited={rec['citations']} [card](ask/{q['id']}.md) |")

    mc = QUESTIONS["mode_checks"]
    md = [f"# Mode checks ({args.label})", "", f"model {env['model']} | local | internet: {env['internet']}", ""]
    log = {}

    # ---- chat: capabilities, no retrieval expected ----
    s = h.chat_session()
    for prompt in mc["chat_capabilities"]:
        print(f"chat: {prompt}", flush=True)
        e = s.turn(prompt)
        ok = (not e["retrieved"]) and "insufficient" not in e["reply"].lower() and not e["citations"]
        md += [f"## Chat: {prompt!r}", f"retrieved notes: {e['retrieved']} | citations: {e['citations']}", "",
               e["reply"], "", f"**{'PASS' if ok else 'FAIL'}**: expected capabilities, no notes search, "
               "no citations, no insufficient-evidence refusal.", ""]
        summary.append(f"| chat capabilities {prompt!r} | {'PASS' if ok else 'FAIL'} | retrieved={e['retrieved']} |")
        log[prompt] = e
    s.save()

    # ---- chat: follow-up uses conversation ----
    s = h.chat_session()
    first, follow = mc["chat_followup"]
    print("chat follow-up ...", flush=True)
    e1 = s.turn(first)
    e2 = s.turn(follow)
    ok = len(e2["reply"]) < len(e1["reply"]) and len(e2["reply"]) > 0
    md += ["## Chat follow-up", f"**You:** {first}", f"(notes searched: {e1['search_query']!r})" if e1["retrieved"] else "(no notes search)",
           "", e1["reply"], ""] + [f"- {x}" for x in e1["sources"]] + [
           "", f"**You:** {follow}", f"(notes searched: {e2['search_query']!r})" if e2["retrieved"] else "(no notes search)",
           "", e2["reply"], "",
           f"**{'PASS' if ok else 'FAIL'}**: second reply ({len(e2['reply'])} chars) is a shorter version of the first "
           f"({len(e1['reply'])} chars), produced from conversation context.", ""]
    summary.append(f"| chat follow-up 'make that shorter' | {'PASS' if ok else 'FAIL'} | {len(e1['reply'])} -> {len(e2['reply'])} chars |")
    s.save()
    log["followup"] = [e1, e2]

    # ---- search: passages only, no model call ----
    before = client.chat_calls
    passages, srec = h.search(mc["search"], k=5)
    ok = client.chat_calls == before and passages and all(p.raw_path for p in passages)
    md += [f"## Search: {mc['search']!r}", f"model calls during search: {client.chat_calls - before} | method: {passages[0].method}", ""]
    md += [f"{p.rank}. `{p.raw_path}` ({p.locator})\n   > {re.sub(r'\s+', ' ', p.text)[:300]}" for p in passages]
    md += ["", f"**{'PASS' if ok else 'FAIL'}**: original passages and paths, no generated answer.", ""]
    summary.append(f"| search {mc['search']!r} | {'PASS' if ok else 'FAIL'} | {len(passages)} passages, 0 model calls |")

    # ---- separation: a chat claim is not evidence for ask ----
    sep = mc["separation"]
    s = h.chat_session()
    print("separation ...", flush=True)
    e = s.turn(sep["chat_claim"])
    rec = h.ask(sep["ask_question"])
    leaked = "78" in (rec.get("raw_answer") or rec["answer"]) or "first-class" in rec["answer"].lower()
    ok = rec["status"] == "insufficient_evidence" and not leaked
    md += ["## Separation: chat claim vs ask evidence", f"**Chat:** {sep['chat_claim']}", "", f"**Quill:** {e['reply']}", "",
           f"**Then ask:** {sep['ask_question']}", "", f"**Ask answer:** {rec['answer']}", f"status: {rec['status']}", "",
           f"**{'PASS' if ok else 'FAIL'}**: ask builds a fresh prompt from retrieved passages only, so the chat "
           "claim cannot be used as evidence.", ""]
    summary.append(f"| separation (chat claim not evidence) | {'PASS' if ok else 'FAIL'} | ask status={rec['status']} |")
    s.save()

    write(out / "mode_checks.md", "\n".join(md))
    dump(out / "mode_checks.json", {"env": env, "log": log, "separation_ask": rec})
    write(out / "summary.md", "\n".join(summary) + "\n")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
