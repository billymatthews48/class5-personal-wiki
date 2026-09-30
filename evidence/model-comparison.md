# Model comparison: Gemma 4 E2B vs E4B on this laptop

**Setup:** both at Q4_K_M, Ollama 0.35.0, 100% CPU (Ryzen 5 7533HS, 13.3 GB RAM), same wiki (5,119 passages), same prompts,
same tests. Run 2026-09-30, local model, internet connected (this run is a comparison, not the offline proof).

**Sources:**
- [e2b/summary.md](e2b/summary.md) and the [e2b/ask](e2b/ask) cards
- [offline-recorded/summary.md](offline-recorded/summary.md) for E4B
- [bench/bench-gemma4_e2b-it-q4_K_M.md](bench/bench-gemma4_e2b-it-q4_K_M.md)
- [bench/bench-gemma4_e4b-it-q4_K_M.md](bench/bench-gemma4_e4b-it-q4_K_M.md)

## Results

| | E2B (`gemma4:e2b-it-q4_K_M`, 4.6 GB) | E4B (`gemma4:e4b-it-q4_K_M`, 6.6 GB) |
|---|---|---|
| Ask tests T1–T4 | 4 / 4 pass | 4 / 4 pass |
| Mode checks (2 capabilities, follow-up, search, separation) | 5 / 5 pass | 5 / 5 pass |
| T4 unsupported question | refused correctly | refused correctly |
| Citation accuracy | **one unsupported citation** (T3, see below) | all citations supported |
| RAG answer, cold (load included) | 38.9 s (13.2 s load) | 63.9 s (18.2 s load) |
| RAG answer, uncached prompt | 20.3–21.2 s | 35.3–37.9 s |
| RAG answer, prompt cached | 7.9 s | 9.8 s |
| Prompt speed / generation speed | ~58–65 tok/s / 15–20 tok/s | ~30–32 tok/s / 10–13 tok/s |
| Gemma writes one wiki note | 43.0 s | 78.2 s |
| Peak resident memory, all Ollama processes (cold load) | 5.32 GB | 7.62 GB |
| Resident memory once warm | 5.33 GB | 5.35 GB |
| Lowest free system RAM during the run | 2.68 GB | **0.20 GB** (cold load), 1.5–1.9 GB after |
| `ollama ps` reported size | 0.94 GB | 1.76 GB |

**Memory notes:**
- "Resident memory" is the sum of the working sets of `ollama.exe` and its `llama-server.exe` runners, including the embedding
  model. It is sampled every 0.25 s.
- The weights are memory-mapped, so Windows can trim the working set after loading. That is why the warm figures are close
  for the two models while the free-RAM figures differ.
- `ollama ps` understates both.

## The one quality difference observed

T3 asks who the client was and how primary data was to be gathered.
- **E4B:** "Your client is Mott MacDonald [4]. You planned to gather primary data using focus groups, and you could also use
  surveys [3]." Both citations are supported.
- **E2B:** "The client … is Mott MacDonald [1, 4]. To gather primary data, you can use surveys [3] or focus groups [3]. Other
  data sources mentioned include demographic data, ONS statistics, and shift times around employees [3]."
  - Passage [4] names Mott MacDonald. Passage [1] (Discussion draft) does not, so that citation is unsupported.
  - The other claims are in passage [3].
  - The answer is fuller than E4B's but less careful about what each citation supports.

Smaller differences:
- In chat, E2B referred to "Billy's academic wiki" while talking to Billy. E4B said "your".
- E2B's "make that shorter" reply was 507 characters from 1,004; E4B's was 375 from 793.

## Conclusion

**E2B is the smallest model that works for this wiki on this laptop.**
- It passes the same nine checks.
- It answers in about 20 s where E4B takes about 35 s.
- It writes notes almost twice as fast.
- It leaves about 1 GB more free RAM. E4B's cold load drove free memory down to 0.2 GB.

Its cost is citation care: one over-citation in four answers. The harness cannot catch that, because it only checks that a
cited number exists, not that the passage supports the claim.

**What the repository uses:** the default stays E4B. All the offline evidence, the recording and the 21 wiki notes were
produced with E4B, and its citations were exact. Switching is one setting: `WIKI_MODEL=gemma4:e2b-it-q4_K_M`.

**Limits of this comparison:**
- One run per model, four questions.
- E2B was not run offline.
- E2B has not been used to write wiki notes, so its note quality is unknown.

My expectation before testing (docs/choices-and-expectations.md) was "E4B follows the citation rules more reliably, E2B is
1.5–2x faster". Both parts held, on this small sample.
