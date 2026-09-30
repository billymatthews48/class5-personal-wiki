# Experiment log and decision record

This is a chronological record of what we did, the decisions we made and why, what I predicted
before each run, and what actually happened. All numbers come from the saved run folders in
`llm_runs/`. The 48 language evals are a **public development benchmark**: they guided the
corpus changes below. The scores therefore show progress on these tests, not generalization
to unseen tests.

Every run used training seed 42 (eval sampling seed 2026) and the notebook's fixed train/validation split method, eval panels
and generation settings (temperature 0.8, 24 tokens). Unless stated, runs used 3,000 steps and
learning rate 0.001. Everything ran on a local Windows CPU.

---

## 0. Setup (22 Sep 2026)

- Cloned the course repository and installed `requirements.txt` into `.venv`, with the CPU build
  of PyTorch 2.14.
- **Problem:** the notebook refused to run with "run_evals.py differs from this notebook's fixed version".
  - **Cause:** Git on Windows converted the line endings (LF→CRLF), which changed the files' SHA-256 hashes.
  - **Fix:** `git config core.autocrlf false` and a fresh checkout. The helper files now
    match the notebook's pinned hashes byte for byte, and none of them were edited.
- **10-step smoke test** (`llm_runs/_smoke_test/`): the full notebook ran in about 20 s, and
  `run_evals.py` worked on the saved model. This only checked the setup, not the experiment.

## 1. Experiment A: starter corpus

- **Notebook:** `custom_llm_A_starter.ipynb`
- **Run:** `llm_runs/20260922T231357_098765Z`
- **Settings:** `CORPUS="classroom"` (the supplied sentences only), 3,000 steps, learning rate 0.001.
  These are the suggested defaults, chosen so A is a clean baseline that B can repeat exactly.
- **Prediction:**
  - untrained, about random (1 in 4)
  - trained, good on the 16 starter patterns, okay on the 8 new wordings, and zero on the 24
    extension cases (missing vocabulary)

| Stage | Correct | Starter (16) | New wording (8) | Extension (24) | Coverage |
|---|---|---|---|---|---|
| Untrained | 9/48 | 6 | 3 | 0 | 24/48 |
| Trained | 20/48 | 16 | 4 | 0 | 24/48 |

- **Outcome:** the prediction matched.
  - The loss panels fell from 4.93 to 0.68 at step 1,500, then flattened (0.68 at 3,000).
  - Samples went from word soup to fluent template sentences.
  - All 24 extension cases were unscorable: words like "opposite", "kitten" and "umbrella" were
    never in the starter vocabulary (133 word types).

## 2. Choosing extension categories

- The brief requires at least 2 of the 8 extension skills.
- **Decision:** cover **all 8**. My instructor said the eval score, and the number of evals
  the model can attempt (coverage), matter.
- **Constraint:** the model keeps only the 509 most frequent word types. So new material
  had to add about 144 missing eval words without pushing total vocabulary over that limit.

## 3. How the teaching corpus is built

- **Generated, not hand-typed.**
  - `make_teaching_corpus.py` writes one file per skill into `corpus/extension/`.
  - This gives thousands of varied, reproducible sentences with different people, objects and wording.
  - The generator never reads `evals/`.
- **Keeping stories together.**
  - The notebook splits imported files at every ". " (full stop plus space), so each
    sentence would become a separate training passage.
  - Many skills need 2–3 sentence stories (e.g. "X is not A . it is B . X is B").
  - So sentences inside a story are joined with no space after the full stop (`green .it is`).
  - The tokenizer produces exactly the same tokens, and the story stays one passage.
- **Independent audit.** `check_extension_corpus.py` compares the corpus with the eval suite
  *before* training. It reports:
  - exact prompt leaks (the notebook's own rule)
  - 5-token overlaps
  - "prompt ending + answer" matches
  - near-copies (added in v2)
  - vocabulary coverage

## 4. Experiment B v1: "strict" separation

**Rule used:** no eval prompts. In addition, wherever a teaching sentence had the same shape as
an eval question, it never used that eval's specific words. For example:
- "kitten" never appeared in "X grows into a Y"
- "breakfast" was never "the earlier meal"
- "door" never appeared in negation stories

This was **stricter than the brief requires**.

**Audit iterations before training.** The audit caught real problems, each fixed and re-checked:
1. **Near-copies of eval questions**, e.g. "the taxi arrived before the bus . the vehicle that
   arrived later was the bus", one word from an eval item. Fixed by keeping each eval's objects
   out of its own frame.
2. **Too many new words:** 596 total types, over the 509 limit, so eval words risked becoming
   unknown. Fixed by trimming word lists and turning one-off sentences into small templates (487 types).
3. **A leaked answer pairing,** "leo thanked maya", in 3 passages. Fixed by never pairing
   people from the same eval story.

**Final v1 audit:** 0 exact prompts, 48/48 cases with full vocabulary, 3,733 passages.
The files are saved in `results/corpus_v1_strict/` and `results/extension_corpus_audit_v1_strict.json`.
The generator is kept as `make_teaching_corpus_v1_strict.py`.

- **Notebook:** `custom_llm_B_extended.ipynb`
- **Run:** `llm_runs/20260923T000319_361728Z`
- **Prediction:** it will get more of the 24 extension cases right than A (0/24).

| Stage | Correct | Starter (16) | New wording (8) | Extension (24) | Coverage |
|---|---|---|---|---|---|
| Untrained | 8/48 | 2 | 2 | 4 | 48/48 |
| Trained | **39/48** | 16 | 8 | 15 | 48/48 |

**Outcome:** the prediction matched. There were 9 failures, from two sources:
- **Blind spots created by my strict rule.** Examples:
  - door → "open": the door was only ever taught as "not closed → open"
  - "the earlier meal is" → lunch
  - salmon → "bird"
  - kitten → "duck"
  - "turn on a" → "pillow"
- **Model limits.** It could not copy a name or colour from earlier in the prompt (references,
  box colour), and it made a plural slip ("the dogs" → is).
- **One lucky pass:** "water freezes into" → ice, with about 0% probability on every choice.
  It was not real learning.

## 5. Decision: relax to the brief's actual line (v2)

My instructor said he checks for intentional cheating but expects some "bleeding" between
evals and training. The goal is to pass as many evals as possible without cheating.

We redrew the line to match the brief's wording: *ordinary words and underlying subject
knowledge may overlap; the test items themselves must stay separate.*

**Still forbidden:**
- any eval prompt (the notebook would reject the corpus)
- a **near-copy**: a passage containing all of an eval item's distinctive words plus its answer,
  e.g. box + red + blue, in either order
- answer lists, eval outputs and chat transcripts

**Now allowed:**
- plain facts in different wording ("a salmon is a fish", "a kitten grows into a cat",
  "when it is dark we turn on a light")
- eval words in the same sentence shapes with other combinations
- both directions of other pairs

**We also added more practice for the weak skills:**
- references, 500 → 900 passages
- negation, 500 → 900
- plural agreement

**Audit.** The new near-copy check caught 3 passages that reversed an eval item's combination:
"the box is not blue . it is red", and "the door is not closed . it is open". Those combinations
are now blocked in both directions.

**Final v2 audit** (`results/extension_corpus_audit.json`):
- 0 exact prompts
- 0 near-copies
- 48/48 coverage
- 478 word types
- 4,691 passages

Shared facts and sentence shapes remain on purpose, and the audit lists them.

## 6. Experiment B v2: "relaxed" separation, 3,000 steps

- **Notebook:** `custom_llm_B2_extended.ipynb`
- **Run:** `llm_runs/20260923T003152_798951Z`
- **Settings:** identical to A and B v1. Only the teaching material changed.
- **Prediction:** higher than v1's 39/48.

| Stage | Correct | Starter (16) | New wording (8) | Extension (24) | Coverage |
|---|---|---|---|---|---|
| Untrained | 14/48 | 3 | 3 | 8 | 48/48 |
| Trained | **43/48** | 16 | 8 | 19 | 48/48 |

**Outcome:** the prediction matched.

**Fixed since v1:**
- salmon → fish (97%)
- kitten → cat
- box colour → blue (87%): colour copying was learned
- "the dogs" → are
- water → ice (12%, now a real preference)
- one reference case (→ omar)

**Still wrong:**
- **door → "open"** (65% vs 19% for closed).
- **2 reference cases.** The name probabilities are nearly flat, 4–9%.
- **"the earlier meal is" → supper.**
- **"we turn on a" → pillow.** The model matched the look-alike training sentence "to sleep
  well we use a soft pillow": it follows sentence shape, not meaning.

Loss panels (training/validation): 6.20/6.19 at step 0, 0.94/0.86 at 1,500, 0.86/0.83 at 3,000.
Losses are not comparable with Experiment A, because the vocabulary and corpus differ.

## 7. Experiment B v2 with longer training: 6,000 steps

- **Change one thing only:** 6,000 steps instead of 3,000. The corpus and all other settings
  are unchanged.
  - Warmup stays at 100 steps: `min(100, steps//10)`.
  - The cosine learning-rate decay stretches over the longer run.
- **Notebook:** `custom_llm_B2_6000steps.ipynb`
- **Run:** `llm_runs/20260923T003555_129361Z`
- **Elapsed:** 124 s of training.
- **Prediction:** slightly more accurate than 43/48, but only slightly.

| Stage | Correct | Starter (16) | New wording (8) | Extension (24) | Coverage |
|---|---|---|---|---|---|
| Untrained | 14/48 | 3 | 3 | 8 | 48/48 |
| Trained | **45/48** | 16 | 8 | 21 | 48/48 |

**Outcome:** the score rose slightly, as predicted (+2). The bigger change was in **confidence**.
- **Two reference cases** went from nearly flat guesses (4–9% per name) to confident, correct
  copying:
  - finn at 93%
  - omar at 98%
- **The door case** flipped to closed (86%).
- **"the earlier meal is"** flipped to breakfast (52%).
- **Most other correct answers** rose above 85%.

**Still wrong:**
- **"maya lent a book to leo . leo thanked" → leo (85%).** The model now copies a name
  confidently, but the wrong one: the most recent name, not the giver.
- **"the dogs" → was (51%) vs are (19%).** This is a regression from the 3,000-step run, where
  it was narrowly correct (23% vs 22%). The margin was always thin.
- **"to see in a dark room we turn on a" → pillow (3.7%) vs light (0.7%).** All choices are
  low. The prompt shape resembles "to sleep well we use a soft pillow".

The loss panels barely moved (training/validation):
- step 3,000: 0.84/0.80
- step 6,000: 0.81/0.79

The eval behaviour still changed noticeably. **A small loss change can hide a qualitative
change in behaviour**, such as learning to copy a name from earlier in the prompt. The 3,000-step
run's panel values differ slightly from this run's step-3,000 values, because the
learning-rate schedule differs.

## 8. Control: starter corpus at 6,000 steps

- **Why:** without this run, comparing "B v2 at 6,000 steps" with "A at 3,000 steps" changes two
  things at once. This control matches the training length. It also tests the brief's statement
  that more training on the original corpus cannot supply missing vocabulary.
- **Notebook:** `custom_llm_A_6000steps.ipynb`
- **Run:** `llm_runs/20260923T033614_161710Z`
- **Settings:** identical to A except 6,000 steps. The teaching files were moved out of `corpus/`
  during this run, so it saw the supplied sentences only.
- **Prediction:** written by Claude, because this run was added while I was away. The 24
  extension cases stay unscorable, and the starter cases stay at or near their 3,000-step scores.

| Stage | Correct | Starter (16) | New wording (8) | Extension (24) | Coverage |
|---|---|---|---|---|---|
| Untrained | 9/48 | 6 | 3 | 0 | 24/48 |
| Trained | 22/48 | 16 | 6 | 0 | 24/48 |

**Outcome:** as predicted.
- The extra steps improved new wording (4 → 6), but the extension group stayed 0/24 because
  the words are missing. That confirms the brief's point.
- Loss panels (training/validation): 4.93/4.93 at step 0, 0.68/0.71 at 3,000, 0.67/0.70 at 6,000.

## 9. Final choices

- **Official A-vs-B comparison (the README's four-row table):** Experiment A (3,000 steps)
  against Experiment B v2 (3,000 steps). Same settings, so the corpus is the only difference.
- **Matched longer-training comparison:** A at 6,000 steps (22/48) against B v2 at 6,000 steps (45/48).
- **Model used for chat and the detailed walkthrough:** B v2 at 6,000 steps
  (`llm_runs/20260923T003555_129361Z`), the best-scoring model.
- We stopped at this point. Each further round would tune the corpus more tightly to these
  48 public tests.
