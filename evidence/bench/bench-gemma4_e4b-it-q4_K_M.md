# Benchmark: gemma4:e4b-it-q4_K_M (bench)

```
time: 2026-09-30T00:55:40
internet: reachable
execution: local
model: gemma4:e4b-it-q4_K_M
embed_model: embeddinggemma
runtime: ollama version is 0.35.0
num_ctx: 8192
think: False
os: Windows-11-10.0.26200-SP0
cpu: AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD
ram_total_gb: 13.3
ram_available_gb: 6.6
```

| Step | Wall s | Load s | First token s | Prompt tok (tok/s) | Gen tok (tok/s) | Peak Ollama RSS GB | Min free RAM GB | ollama ps |
|---|---|---|---|---|---|---|---|---|
| RAG answer, cold (model load included) | 63.85 | 18.22 | 56.82 | 1085 (29.8) | 46 (11.1) | 7.62 | 0.2 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
| RAG answer, warm | 9.75 | 0.04 | 2.56 | 1085 (2334.8) | 47 (9.6) | 5.35 | 1.89 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
| keyword search (no model) | 0.01 |  |  |  () |  () | 5.35 | 1.87 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
| hybrid search (embeddinggemma) | 2.11 |  |  |  () |  () | 5.35 | 1.84 | embeddinggemma:latest 0.63 GB; gemma4:e4b-it-q4_K_M 1.76 GB |
| ingest: Gemma writes one note (Career Networking) | 78.19 |  | 37.65 | 1025 (29.2) | 438 (10.8) | 5.43 | 1.52 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
| ingest: parse + index all raw files (cached parse) | 0.87 |  |  |  () |  () | 5.42 | 1.95 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
