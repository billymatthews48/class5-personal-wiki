# Optional extras: local web page and online mode

Tested 2026-09-30, `gemma4:e4b-it-q4_K_M`, Ollama 0.35.0.

## Local web page (`wiki serve`): works

`wiki serve --port 8765` starts a standard-library HTTP server bound to 127.0.0.1. Its three endpoints call the same
`Harness` methods as the CLI, so citation checks and saved runs are identical.

| Request | Result |
|---|---|
| `GET /` | 200; the page loads with Chat / Ask / Search tabs |
| `POST /api/search` "lean operations waste" | 2.9 s. Top 3: `Week 6 - Lean Operations.docx` (two sections) and `Summary and news stories.docx`; method hybrid. |
| `POST /api/ask` "Who was the client for my Cambridge consulting project, and how did we plan to gather primary data?" | 38.4 s; status `answered`. "Your client is Mott MacDonald [4]. You planned to gather primary data using focus groups, and you could also use surveys [3]." It cites `Notes from first few meetings.docx` and `Intro and project definition .docx`, the same answer and citations as the CLI test T3. |
| `POST /api/chat` "what can you help me with?" | 14.7 s; `retrieved: false`; a capabilities reply |
| `POST /api/nope` | 404 |

Browser check: I opened the page, chose the Search tab, typed "Netflix live sports strategy" and pressed Enter. The passages
appeared with raw paths and note names, and there were no console errors.

![Search tab in the local web page](web-ui-search.jpg)

Not tested: the Ask and Chat tabs by hand in the browser (their endpoints were tested above), and concurrent users.

## Online mode (`--mode online`): written, NOT tested end to end

- **What it is:** `wiki ask … --mode online` and `wiki chat --mode online` send the assembled prompt to hosted
  `gemma-4-26b-a4b-it` on the Gemini API (`generativelanguage.googleapis.com`). This is the 26B A4B model that does not fit
  on this laptop. Retrieval and embeddings stay local.
- **What it sends to Google:** the instructions, the question, and the retrieved passages (up to 4,000 characters of my
  notes) for ask; the conversation for chat. Nothing else.
- **How to select it:** set `GEMINI_API_KEY` (from Google AI Studio), then add `--mode online`. Local is the default.
- **Why it is untested:** no API key was available, so no online answer was ever produced. I have no evidence that the
  request format, the response parsing or the answer quality are correct.
- **What was tested:** the failure path. With no key:

```
> wiki ask "Who was the client for my Cambridge consulting project?" --mode online
error: Online mode needs GEMINI_API_KEY (create one in Google AI Studio). Local mode needs nothing; drop --mode online.
exit code: 1
```

It stops with an error and does not fall back to the local model or to any other service. Local mode is unaffected.
