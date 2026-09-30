# Retrieval tuning experiment: fusion weight (2026-09-29, before any answer test)

**Observation:** with equal-weight reciprocal rank fusion, the T2 source was at rank 4.
- It had the highest cosine of any passage (0.547; the next best was 0.392).
- Keyword matches on "gap" and "price" in unrelated notes ranked above it.

**Experiment:** weight the embedding ranking by w, with BM25 kept at weight 1. The table shows the rank of the expected source in the top 5.

| w_emb | T1 | T2 | T3 | T4 max cosine |
|---|---|---|---|---|
| 1.0 | 1 | 4 | 2, 4 | 0.489 |
| 1.5 | 1 | 4 | 3, 4, 5 | 0.489 |
| 2.0 | 1 | 4 | 3, 4, 5 | 0.489 |
| 3.0 | 1 | 3 | 3, 4, 5 | 0.489 |

**Decision:**
- Keep w = 1.0. Higher weights did not lift T2 into the top 3 until w = 3, and they pushed T3's sources down.
- Instead, raise the ask evidence budget from 3,600 to 4,000 characters, so all 4 retrieved passages reach Gemma untruncated.

**Also recorded:**
- Top cosine for the answerable questions is 0.547–0.556.
- Top cosine for the unsupported T4 is 0.489.
- The ask retrieval gate (0.45) therefore lets T4 through to the model, as intended. Retrieval finds the essay itself, so it is the *model* that must notice that no mark is stated.
