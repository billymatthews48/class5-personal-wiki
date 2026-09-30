# Academic Wiki CLI: local Gemma + RAG (Class 5, Assignment 4)

This is my own command-line tool and harness for talking to my own academic notes. It uses an open-weight Gemma
model that runs on my laptop and works with the internet disconnected.

**Status at submission (honest summary):**
- The CLI, the harness and all five commands work.
- All four ask-mode tests and all five mode checks **passed offline**.
- The wiki is **partial**: 11 of the 20 planned subject notes were generated before the deadline.
- The Obsidian screenshots, the E2B comparison and the online-mode test are **not done**.

See [What is incomplete](#what-is-incomplete).

## 1. Purpose and sources

The wiki lets me find and question my coursework and projects across two degrees and my GitHub.

| Source | Files | What |
|---|---|---|
| Cambridge Management Studies, Year 3 | 158 | lecture notes, supervision work, essays, the Mott MacDonald project |
| Berkeley MBA academics | 23 | essays, memos, homework (spreadsheets and media excluded) |
| My GitHub repos (`Assignment-1`, `class4-custom-llm`) | 13 | README, assignment and log Markdown |
| Added during the offline demo | 1 | Energy Transition memo |

**How the originals connect to the pages:**
- Originals are copied byte-for-byte into `vault/raw/` and sha256-verified by
  [scripts/collect_sources.py](scripts/collect_sources.py). They are never edited.
- [subjects.yaml](subjects.yaml) maps the raw files to subject notes in `vault/wiki/<Topic>/`.
- Each note links to its originals under `## Sources`.
- [vault/Source Catalog.md](vault/Source%20Catalog.md) lists every original with its origin, fingerprint, passage count and note.

**Not in the repo:** some third-party files (a textbook, classmates' summaries, interview transcripts) are kept local through
`.gitignore`. They are still listed in the catalog.

## 2. Setup and device

| | |
|---|---|
| OS | Windows 11 Pro 10.0.26200 |
| CPU | AMD Ryzen 5 7533HS (6 cores / 12 threads) |
| RAM | 13.3 GB usable (16 GB installed, part reserved for the integrated GPU); 1.8–3.2 GB free during runs |
| GPU | AMD Radeon 660M integrated, shared memory, no dedicated VRAM. Ollama ran 100% on CPU. |
| Free disk | 348 GB |
| Runtime | Ollama 0.34.4 |
| Chat model | `gemma4:e4b-it-q4_K_M`: Gemma 4 E4B, 7.5B total parameters, Q4_K_M, 6.6 GB download |
| Embedding model | `embeddinggemma` (307M parameters, 621 MB), also local |
| Settings | `num_ctx` 8192, thinking off, temperature 0.1 (ask) / 0.7 (chat) |

Official sources: <https://ai.google.dev/gemma/docs/core> and <https://ollama.com/library/gemma4>. The weights are not in this
repo.

```powershell
winget install Ollama.Ollama
ollama pull gemma4:e4b-it-q4_K_M
ollama pull embeddinggemma
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -e .
# optional, for OCR of scanned PDFs: winget install UB-Mannheim.TesseractOCR ; pip install pypdfium2 pytesseract
```

```powershell
wiki --help
wiki doctor
wiki ingest                       # or: wiki ingest path\to\new-source.docx
wiki search "lean operations waste" -k 5
wiki ask "Who was the client for my Cambridge consulting project?" --mode local
wiki chat
```

### Why this model

- The 26B A4B MoE model is 18 GB at Q4_K_M in Ollama. It activates about 4B parameters per token, but all 26B must be
  loaded, so it cannot fit in 13.3 GB.
- E2B (4.6 GB) and E4B (6.6 GB) both fit.
- I chose E4B because I expected it to follow citation and refusal rules more reliably. It passed all four tests.
- **I did not get to benchmark E2B, so I have not shown that E4B is the smallest model that works.** That is an open item.

### Measured memory and response time (E4B, this laptop, my wiki)

| Measurement | Value | Where |
|---|---|---|
| First call, cold: model load | 28.2 s | first smoke test |
| First call: prompt / generation speed | 12.8 tok/s / 8.4 tok/s | first smoke test |
| Ask, uncached prompt (T2, T3, T4, offline) | 35.3–37.9 s wall; first token after 32–36 s; ~950–1,040 prompt tokens at ~31 tok/s; 9.6–13.8 tok/s generation | [evidence/offline/ask](evidence/offline/ask) |
| Ask, repeated question with cached prompt (T1, offline) | 7.8 s | [T1](evidence/offline/ask/T1.md) |
| Chat turn without retrieval (offline) | 11.4–30.1 s | [mode_checks.json](evidence/offline/mode_checks.json) |
| Ingest of one new source, offline (copy, parse, embed, Gemma writes the note, rebuild index) | 108.4 s total; the note alone 98.3 s (838 prompt tokens, 401 generated) | [transcript](evidence/offline/transcript.txt) |
| First full ingest: embedding 5,087 passages | 2,184 s (2.3 passages/s) | one-off; cached afterwards |
| First full ingest: note writing | ~2.5 min per note | [ingest log](evidence/ingest/01-first-ingest.log) |
| Memory: `ollama ps` size for the chat model | 1.9 GB (8192 context, 100% CPU) | smoke tests |
| Memory: system free RAM | 3.0–3.2 GB before runs; 1.8–1.9 GB during the offline run | transcript |

A fuller memory benchmark (`tests/bench.py`, which samples peak process memory) was written but had not finished at
submission. If `evidence/bench/` exists, it holds those results.

## 3. Architecture

- **Model:** local Gemma. It only sees the text the harness puts in a prompt.
- **Retrieval tool** ([wiki/retrieval.py](wiki/retrieval.py)): `Retriever.search()` ranks original passages and returns them
  with raw path, locator and owning note. It never generates text.
- **RAG workflow** (`Harness.ask` in [wiki/harness.py](wiki/harness.py)): retrieve → number the evidence → prompt with the
  research rules → Gemma → check citations.
- **Harness** ([wiki/harness.py](wiki/harness.py)):
  - chooses the behaviour per mode
  - loads the right instruction file
  - keeps chat history
  - decides whether retrieval happens
  - calls the model through [wiki/llm.py](wiki/llm.py)
  - validates citations
  - turns failures into clear errors (Ollama down, model missing, empty index)
  - saves every run under `.wiki/runs/`.
- **CLI** ([wiki/cli.py](wiki/cli.py)): argument parsing and printing only.

**One path, from command to result:** `wiki ask "What price gap …?"`
1. `cli.main` parses the arguments and builds `Harness(OllamaClient())`.
2. `Harness.ask` calls `Retriever.search(question, k=4)`:
   - BM25 scores over 5,113 passages
   - an `embeddinggemma` query vector and cosine scores
   - reciprocal rank fusion, then near-duplicate removal.
3. If the best cosine is below 0.45, it returns insufficient evidence without calling Gemma.
4. `format_evidence` numbers the passages `[1]..[4]` with source labels, up to 4,000 characters.
5. A fresh two-message prompt is built: `prompts/wiki-instructions.md` plus the question and evidence. It contains no chat
   history and no persona.
6. `OllamaClient.chat` streams from `localhost:11434`.
7. The reply is checked:
   - `INSUFFICIENT_EVIDENCE` → refusal.
   - No valid `[n]` → rejected as ungrounded.
   - Invalid numbers are stripped.
8. The answer and the cited raw paths are printed, and the run is saved as JSON and Markdown.

**Chat** uses `prompts/persona.md` (Quill) and a rolling history of 8,000 characters.
- Gemma gets a `search_notes` tool through Ollama's native function calling and decides whether to call it.
- If it does, the harness runs the retrieval tool, returns numbered passages, and checks the citations in the reply.
- `/notes QUERY` forces a lookup.

**Search** prints the retrieval tool's output. It runs keyword-only if Ollama is not running.

## 4. Design choices

Written before testing: [docs/choices-and-expectations.md](docs/choices-and-expectations.md).

- **Passages:** about 900 characters with 150 characters of overlap, cut on document structure. Locators are the section heading, page or slide.
- **How much text Gemma sees:**
  - Ask: at most 4 passages / 4,000 characters (about 1,000 prompt tokens).
  - Note writing: opening excerpts of up to 12 files, about 6,000 characters.
- **Retrieval:** hybrid BM25 plus local embeddings with equal-weight fusion. I tested heavier embedding weights and
  rejected them ([fusion_weights.md](evidence/retrieval/fusion_weights.md)).
- **Instructions are separate files:**
  - [persona.md](prompts/persona.md) for chat only
  - [wiki-instructions.md](prompts/wiki-instructions.md) for ask only
  - [note-writer.md](prompts/note-writer.md) for ingest only.
- **Note naming:**
  - Titles are 2–6 words and fixed in `subjects.yaml`. Gemma writes the body, not the name.
  - Machine IDs (`subject_key`, `wiki_id`) live in note properties.
  - Chunks, embeddings and the manifest live in `.wiki/`, outside the vault.
  - `wiki lint` rejects hash-, date-, export- and sentence-style names and broken links.
  - `wiki rename` updates incoming links and the subject map.
- **Re-ingestion:**
  - A note is found by its `subject_key` property, not its filename.
  - It is regenerated only if the sha256 set of its sources changed.
  - It is rewritten in place and keeps its `## My Notes` section.
- **Thinking mode is off.** Gemma 4 turns it on by default, and it multiplies CPU latency.
- **Optional extras built:**
  - local OCR with a confidence gate ([ocr_check.md](evidence/ocr/ocr_check.md))
  - `/remember` and `/draft` in chat, saved outside `raw/` so ask never treats them as evidence
  - `wiki serve`, a local web page
  - `--mode online`, hosted `gemma-4-26b-a4b-it` on the Gemini API. It needs `GEMINI_API_KEY`, sends the question and
    retrieved passages to Google, and is never a fallback. **Only the OCR was tested; the other three are untested.**

## 5. Evidence

All ask tests and mode checks below ran with Wi-Fi and Ethernet disconnected, after restarting Ollama and the CLI.
- Model: `gemma4:e4b-it-q4_K_M`, local.
- Proof of being offline: adapter status, a failed TCP test to 8.8.8.8 and a failed DNS lookup. These are in
  [evidence/offline/transcript.txt](evidence/offline/transcript.txt).
- Summary: [evidence/offline/summary.md](evidence/offline/summary.md).

| Test | Result | Card |
|---|---|---|
| T1 direct, one source | answered, cited the expected source | [T1](evidence/offline/ask/T1.md) |
| T2 paraphrased | answered, cited the expected source (retrieved at rank 4 of 4) | [T2](evidence/offline/ask/T2.md) |
| T3 two sources | answered, cited two Mott project files | [T3](evidence/offline/ask/T3.md) |
| T4 unsupported | `INSUFFICIENT_EVIDENCE` from the model | [T4](evidence/offline/ask/T4.md) |
| Chat "what can you help me with?" / "what can we do?" | capabilities, no notes search, no citations | [mode_checks.md](evidence/offline/mode_checks.md) |
| Chat draft → "make that shorter" | 930 → 398 characters from conversation context | same |
| Search "lean operations waste" | 5 original passages, 0 model calls | same |
| Separation: mark claimed in chat, then asked in ask | ask still returned insufficient evidence | same |

Each card has the question, expected source, retrieved passages and paths, the answer, the citations, automated checks and my
assessment after opening the cited passage.

Other evidence:
- **Retrieval alone:** [retrieval_check.md](evidence/retrieval/retrieval_check.md) compares keyword-only and hybrid. Keyword-only
  missed T2 completely; hybrid found it.
- **Offline ingest:** transcript section 5. It produced
  [Energy Transition.md](vault/wiki/Economics%20and%20Strategy/Energy%20Transition.md).
- **Test questions:** [tests/questions.yaml](tests/questions.yaml). They were written before retrieval was built and are kept
  outside the vault.

## 6. Reflection: failures and limitations

1. **Keyword retrieval failed the paraphrased question (T2).**
   - BM25 alone did not return the source in the top 5; adding embeddings brought it to rank 4.
   - It is still last among the passages shown, because keyword matches on "gap" and "price" outrank it under equal-weight fusion.
   - Reweighting hurt T3.
   - Improvement to try: rerank the top 20 by cosine only, or add a small local reranker.
2. **Handwritten scans are unreadable.** Tesseract scored 40–46 confidence on nine handwritten supervisions, so they are
   excluded from the index. A handwriting model such as TrOCR is the next step.
3. **Speed.** About 35 s per uncached answer on CPU, with first token after 32–36 s. Ollama did not use the integrated GPU.
   I did not test the Vulkan backend or E2B.
4. **Note quality.**
   - Gemma sees only the opening excerpts of up to 12 files per subject, so large subjects are summarised from a sample.
   - The first notes put `[S1]` labels in the text and proposed weak "related" links.
   - I tightened the prompt and stripped the labels, but I did **not** complete a line-by-line review of every note against
     its originals. All notes are still marked `reviewed: false`.

## What is incomplete

- **Wiki:** 11 of 20 subject notes exist.
  - Missing: Business Communication, Career Networking and Visibility, Operations Management, Quantitative Methods, Finance
    and Accounting, Mott MacDonald Consulting Project, Custom LLM Training, Secure Networking Tracker, Management Studies Revision.
  - Their raw files are indexed and searchable. T1 and T3 answer from them, and their citations name notes that do not exist yet.
  - Links to missing notes were removed, so the graph is sparser than intended.
- **Obsidian screenshots** (open note, index, graph): not captured.
- **Re-ingestion and rename evidence:** the code exists (`wiki ingest`, `wiki rename`, `wiki lint`), but I did not record a
  duplicate-free re-ingest run.
- **E2B comparison, online mode, web UI, memory commands:** E2B was never benchmarked; the other three are written but untested.
- **Recording:** no usable screen recording of the offline run was captured. The proof is the PowerShell transcript
  ([evidence/offline/transcript.txt](evidence/offline/transcript.txt)), which records the disconnected adapters, the failed
  connectivity checks, and every command with its output.
