# Benchmark: gemma4:e4b-it-q4_K_M (bench)

```
time: 2026-09-29T23:54:21
internet: reachable
execution: local
model: gemma4:e4b-it-q4_K_M
embed_model: embeddinggemma
runtime: ollama version is 0.34.4
num_ctx: 8192
think: False
os: Windows-11-10.0.26200-SP0
cpu: AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD
ram_total_gb: 13.3
ram_available_gb: 1.8
```

| Step | Wall s | Load s | First token s | Prompt tok (tok/s) | Gen tok (tok/s) | Peak Ollama RSS GB | Min free RAM GB | ollama ps |
|---|---|---|---|---|---|---|---|---|
| RAG answer, cold (model load included) | 70.36 | 22.67 | 62.89 | 1085 (28.6) | 46 (10.0) | 0.02 | 0.01 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
| RAG answer, warm | 9.82 | 0.02 | 2.46 | 1085 (4625.4) | 46 (9.7) | 0.02 | 1.58 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
| keyword search (no model) | 0.02 |  |  |  () |  () | 0.02 | 1.55 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
| hybrid search (embeddinggemma) | 2.19 |  |  |  () |  () | 0.02 | 1.5 | embeddinggemma:latest 0.63 GB; gemma4:e4b-it-q4_K_M 1.76 GB |
| ingest: Gemma writes one note (Career Networking and Visibility) | 79.45 |  | 36.65 | 1021 (30.1) | 434 (10.2) | 0.02 | 1.32 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
| ingest: parse + index all raw files (cached parse) | 0.77 |  |  |  () |  () | 0.02 | 1.68 | gemma4:e4b-it-q4_K_M 1.76 GB; embeddinggemma:latest 0.63 GB |
