# Test run: online

```
time: 2026-09-30T01:31:33
internet: reachable
execution: ONLINE (hosted Gemma on the Gemini API)
model: gemma-4-26b-a4b-it
embed_model: embeddinggemma
runtime: Gemini API; retrieval and embeddings local (Ollama)
num_ctx: 8192
think: False
os: Windows-11-10.0.26200-SP0
cpu: AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD
ram_total_gb: 13.3
ram_available_gb: 6.3
```

| Check | Result | Detail |
|---|---|---|
| ask T1 (direct, one source) | PASS | status=answered, cited=[1] [card](ask/T1.md) |
| ask T2 (answerable, paraphrased away from the source wording (no drug name, no dollar signs)) | PASS | status=answered, cited=[4] [card](ask/T2.md) |
| ask T3 (connects two sources) | PASS | status=answered, cited=[2, 3, 4] [card](ask/T3.md) |
| ask T4 (unsupported (plausible, but no source states it)) | PASS | status=insufficient_evidence, cited=[] [card](ask/T4.md) |
