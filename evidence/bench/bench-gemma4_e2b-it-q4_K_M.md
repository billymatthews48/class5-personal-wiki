# Benchmark: gemma4:e2b-it-q4_K_M (bench)

```
time: 2026-09-30T01:01:41
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
ram_available_gb: 2.4
```

| Step | Wall s | Load s | First token s | Prompt tok (tok/s) | Gen tok (tok/s) | Peak Ollama RSS GB | Min free RAM GB | ollama ps |
|---|---|---|---|---|---|---|---|---|
| RAG answer, cold (model load included) | 38.89 | 13.22 | 33.88 | 1085 (58.4) | 44 (19.9) | 5.32 | 2.89 | gemma4:e2b-it-q4_K_M 0.94 GB; embeddinggemma:latest 0.63 GB |
| RAG answer, warm | 7.94 | 0.04 | 2.3 | 1085 (5102.3) | 44 (13.1) | 5.33 | 2.92 | gemma4:e2b-it-q4_K_M 0.94 GB; embeddinggemma:latest 0.63 GB |
| keyword search (no model) | 0.01 |  |  |  () |  () | 5.33 | 2.93 | gemma4:e2b-it-q4_K_M 0.94 GB; embeddinggemma:latest 0.63 GB |
| hybrid search (embeddinggemma) | 2.1 |  |  |  () |  () | 5.33 | 2.87 | embeddinggemma:latest 0.63 GB; gemma4:e2b-it-q4_K_M 0.94 GB |
| ingest: Gemma writes one note (Career Networking) | 43.0 |  | 20.19 | 1025 (57.2) | 373 (16.4) | 5.36 | 2.68 | gemma4:e2b-it-q4_K_M 0.94 GB; embeddinggemma:latest 0.63 GB |
| ingest: parse + index all raw files (cached parse) | 0.92 |  |  |  () |  () | 5.35 | 2.89 | gemma4:e2b-it-q4_K_M 0.94 GB; embeddinggemma:latest 0.63 GB |
