# Test run: offline-recorded

```
time: 2026-09-30T00:38:12
internet: unreachable (offline)
execution: local
model: gemma4:e4b-it-q4_K_M
embed_model: embeddinggemma
runtime: ollama version is 0.35.0
num_ctx: 8192
think: False
os: Windows-11-10.0.26200-SP0
cpu: AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD
ram_total_gb: 13.3
ram_available_gb: 2.3
```

| Check | Result | Detail |
|---|---|---|
| ask T1 (direct, one source) | PASS | status=answered, cited=[1] [card](ask/T1.md) |
| ask T2 (answerable, paraphrased away from the source wording (no drug name, no dollar signs)) | PASS | status=answered, cited=[4] [card](ask/T2.md) |
| ask T3 (connects two sources) | PASS | status=answered, cited=[3, 4] [card](ask/T3.md) |
| ask T4 (unsupported (plausible, but no source states it)) | PASS | status=insufficient_evidence, cited=[] [card](ask/T4.md) |
| chat capabilities 'what can you help me with?' | PASS | retrieved=False |
| chat capabilities 'what can we do?' | PASS | retrieved=False |
| chat follow-up 'make that shorter' | PASS | 793 -> 375 chars |
| search 'lean operations waste' | PASS | 5 passages, 0 model calls |
| separation (chat claim not evidence) | PASS | ask status=insufficient_evidence |
