# Choices and expected behaviour (written before testing)

Written 2026-09-29, after the retrieval index was built but **before** any ask/chat test or
Gemma-generated note. Results are compared against these expectations in the README.

## 1. Data
- **Purpose:** a personal academic wiki. It lets me find and question my own coursework, essays and projects
  across two degrees and my GitHub.
- **Sources (194 unique files, copied unchanged into `vault/raw/`):**
  - Cambridge Management Studies Year 3 (158)
  - Berkeley MBA academics (23; spreadsheets and media excluded)
  - README/assignment docs from my two public GitHub repos (13)
- **Questions it should answer:** what a course covered, what I argued in an essay, facts from my
  project work (e.g. the Mott MacDonald project), frameworks from my notes.
- **Scope limits:**
  - Law and economics from Cambridge Years 1–2 are excluded.
  - Personal and professional documents are excluded.
  - Ten scanned PDFs have no text layer and are not searchable until OCR is added.

## 2. Model
- **Model:** `gemma4:e4b-it-q4_K_M` via Ollama 0.34.4 (7.5B total parameters, Q4_K_M, 6.6 GB download).
- **Why this model:**
  - The laptop has 13.3 GB of usable RAM and no discrete GPU; the Radeon 660M shares system memory.
  - `26b-a4b` needs 18 GB at Q4_K_M, even though only about 4B parameters are active per token, so it does not fit.
- **First measured run:** prompt 12.8 tok/s, generation 8.4 tok/s, 100% CPU.
- **Expectation:** E4B will follow the citation rules more reliably than E2B, but E2B will be about 1.5–2x faster.
  If E2B passes the same four tests, it is the better choice under "smallest model that works".
  Both are benchmarked.
- **Thinking mode is off.** Gemma 4 enables it by default, and it would multiply CPU latency.

## 3. Retrieval
- **Passages:** about 900 characters with 150 characters of overlap, cut along document structure. Each keeps its raw path and
  locator (section heading, page or slide).
- **Method:** hybrid.
  - BM25 keyword scoring, in-process and always available.
  - `embeddinggemma` cosine similarity, local through Ollama.
  - The two rankings are merged by reciprocal rank fusion, and near-identical passages (a .docx and its PDF copy) are removed.
- **Keyword baseline, measured before embeddings:**
  - T1: expected source at rank 2.
  - T3: both expected sources at ranks 3 and 4.
  - T2 (paraphrased): missed.
- **Expectation for hybrid:**
  - T2's source enters the top 4, because the wording differs but the meaning matches.
  - T1 and T3 stay in the top 4.
- **Risk:** the 1,400-passage accounting textbook may crowd out my own notes on finance questions.

## 4. Prompts and modes
- **ask:**
  - Uses `wiki-instructions.md` only. It is stateless and runs at temperature 0.1.
  - Shows at most 4 passages / 3,600 characters (about 900 tokens) to fit CPU prompt speed.
  - Must cite [n] or reply `INSUFFICIENT_EVIDENCE`. The harness rejects any answer with no valid citation.
- **Expected ask results:**
  - T1–T3 are answered with correct citations.
  - T4 returns insufficient evidence. Retrieval will surface the essay itself, so the *model* has to recognise that no mark is stated.
    This is the hardest test for a small model.
- **chat:**
  - Uses `persona.md` (Quill) and keeps history up to 8,000 characters.
  - Gemma decides whether to call `search_notes`.
  - Expected: no search for "what can you help me with?" or "make that shorter"; search for questions about course
    content.
  - Risk: a 7.5B model may over-call or under-call the tool.
- **search:** never calls the model, and works with Ollama stopped (keyword only).

## 5. Wiki design
- **Notes:**
  - One note per subject (19 notes) in 6 topic folders.
  - Titles are fixed by a human in `subjects.yaml`, so re-ingestion cannot bring back machine-style names.
  - Gemma writes the summary, key ideas and related links with reasons.
- **Machine data:** IDs go in note properties; chunks, embeddings and the manifest live in `.wiki/`, outside the vault.
- **Expectation:** some generated key ideas will be vague or slightly wrong. Each note is reviewed against the originals,
  and corrections are logged.
