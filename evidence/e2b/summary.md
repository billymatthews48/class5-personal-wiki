# Test run: e2b

```
time: 2026-09-30T00:58:37
internet: reachable
execution: local
model: gemma4:e2b-it-q4_K_M
embed_model: embeddinggemma
runtime: ollama version is 0.35.0
num_ctx: 8192
think: False
os: Windows-11-10.0.26200-SP0
cpu: AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD
ram_total_gb: 13.3
ram_available_gb: 7.3
```

| Check | Result | Detail |
|---|---|---|
| ask T1 (direct, one source) | PASS | status=answered, cited=[1] [card](ask/T1.md) |
| ask T2 (answerable, paraphrased away from the source wording (no drug name, no dollar signs)) | PASS | status=answered, cited=[4] [card](ask/T2.md) |
| ask T3 (connects two sources) | PASS | status=answered, cited=[1, 3, 4] [card](ask/T3.md) |
| ask T4 (unsupported (plausible, but no source states it)) | PASS | status=insufficient_evidence, cited=[] [card](ask/T4.md) |
| chat capabilities 'what can you help me with?' | PASS | retrieved=False |
| chat capabilities 'what can we do?' | PASS | retrieved=False |
| chat follow-up 'make that shorter' | PASS | 1004 -> 507 chars |
| search 'lean operations waste' | PASS | 5 passages, 0 model calls |
| separation (chat claim not evidence) | PASS | ask status=insufficient_evidence |
