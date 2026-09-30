"""Thin client for the local Ollama server. No cloud backend and no fallback."""
import json
import time

import requests

from . import config


class LLMError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url=config.OLLAMA_URL, model=config.CHAT_MODEL,
                 embed_model=config.EMBED_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embed_model = embed_model

    def _post(self, path, payload, stream=False):
        try:
            r = requests.post(self.base_url + path, json=payload, stream=stream,
                              timeout=config.REQUEST_TIMEOUT)
        except requests.ConnectionError:
            raise LLMError(f"Ollama is not reachable at {self.base_url}. Start the Ollama app "
                           f"(or run `ollama serve`) and try again.")
        except requests.Timeout:
            raise LLMError(f"Ollama timed out after {config.REQUEST_TIMEOUT}s.")
        if r.status_code == 404:
            raise LLMError(f"Model not found in Ollama. Run `ollama pull {payload.get('model')}`.")
        if r.status_code >= 400:
            raise LLMError(f"Ollama error {r.status_code}: {r.text[:300]}")
        return r

    def chat(self, messages, temperature=0.7, fmt=None, on_token=None, max_tokens=None, tools=None):
        """Streamed chat call. Returns (text, stats); stats["tool_calls"] lists any tool calls
        the model requested (Gemma 4 native function calling via Ollama's `tools` field)."""
        options = {"num_ctx": config.NUM_CTX, "temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens
        payload = {"model": self.model, "messages": messages, "stream": True,
                   "think": config.THINK, "options": options}
        if fmt is not None:
            payload["format"] = fmt
        if tools:
            payload["tools"] = tools
        start = time.perf_counter()
        first = None
        parts, final, tool_calls = [], {}, []
        r = self._post("/api/chat", payload, stream=True)
        for line in r.iter_lines():
            if not line:
                continue
            msg = json.loads(line)
            if "error" in msg:
                raise LLMError(f"Ollama error: {msg['error']}")
            tool_calls.extend(msg.get("message", {}).get("tool_calls") or [])
            piece = msg.get("message", {}).get("content", "")
            if piece:
                if first is None:
                    first = time.perf_counter()
                parts.append(piece)
                if on_token:
                    on_token(piece)
            if msg.get("done"):
                final = msg
        end = time.perf_counter()
        ns = 1e9
        stats = {
            "model": self.model,
            "wall_s": round(end - start, 2),
            "ttft_s": round((first or end) - start, 2),
            "load_s": round(final.get("load_duration", 0) / ns, 2),
            "prompt_tokens": final.get("prompt_eval_count", 0),
            "prompt_tok_s": _rate(final.get("prompt_eval_count"), final.get("prompt_eval_duration")),
            "gen_tokens": final.get("eval_count", 0),
            "gen_tok_s": _rate(final.get("eval_count"), final.get("eval_duration")),
            "tool_calls": tool_calls,
        }
        return "".join(parts), stats

    def embed(self, texts, batch=16):
        out = []
        for i in range(0, len(texts), batch):
            r = self._post("/api/embed", {"model": self.embed_model, "input": texts[i:i + batch]})
            out.extend(r.json()["embeddings"])
        return out

    def installed_models(self):
        try:
            r = requests.get(self.base_url + "/api/tags", timeout=10)
        except requests.ConnectionError:
            raise LLMError(f"Ollama is not reachable at {self.base_url}.")
        return [m["name"] for m in r.json().get("models", [])]

    def loaded_models(self):
        r = requests.get(self.base_url + "/api/ps", timeout=10)
        return r.json().get("models", [])


class GeminiGemmaClient:
    """OPTIONAL online mode: hosted Gemma on the Gemini API (Google AI Studio).

    Only constructed when the user passes --mode online; never used as a fallback. Sends the
    assembled prompt (instructions + question + retrieved passages, or the chat turn) to Google.
    Embeddings and retrieval stay local. Hosted Gemma takes no system role, so instructions are
    prepended to the first user turn; it does not get the search_notes tool.
    """
    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, model=None, local=None):
        import os
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise LLMError("Online mode needs GEMINI_API_KEY (create one in Google AI Studio). "
                           "Local mode needs nothing; drop --mode online.")
        self.model = model or os.environ.get("WIKI_ONLINE_MODEL", "gemma-4-26b-a4b-it")
        self.local = local or OllamaClient()   # embeddings for retrieval stay local

    def embed(self, texts, batch=16):
        return self.local.embed(texts, batch)

    def chat(self, messages, temperature=0.7, fmt=None, on_token=None, max_tokens=None, tools=None):
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        contents = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "model" if m["role"] == "assistant" else "user"
            text = m["content"] if m["role"] != "tool" else f"[search_notes results]\n{m['content']}"
            if not text:
                continue
            if contents and contents[-1]["role"] == role:
                contents[-1]["parts"][0]["text"] += "\n\n" + text
            else:
                contents.append({"role": role, "parts": [{"text": text}]})
        if system and contents:
            contents[0]["parts"][0]["text"] = f"{system}\n\n---\n\n{contents[0]['parts'][0]['text']}"
        gen = {"temperature": temperature}
        if max_tokens:
            gen["maxOutputTokens"] = max_tokens
        if fmt is not None:
            gen["responseMimeType"] = "application/json"
        start = time.perf_counter()
        try:
            r = requests.post(self.ENDPOINT.format(model=self.model), timeout=180,
                              headers={"x-goog-api-key": self.api_key},
                              json={"contents": contents, "generationConfig": gen})
        except requests.RequestException as e:
            raise LLMError(f"Online mode could not reach the Gemini API ({e.__class__.__name__}). "
                           f"No fallback is attempted; use local mode.")
        if r.status_code >= 400:
            raise LLMError(f"Gemini API error {r.status_code}: {r.text[:300]}")
        data = r.json()
        parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if on_token:
            on_token(text)
        wall = round(time.perf_counter() - start, 2)
        usage = data.get("usageMetadata", {})
        return text, {"model": f"{self.model} (online, Gemini API)", "wall_s": wall, "ttft_s": wall,
                      "load_s": 0, "prompt_tokens": usage.get("promptTokenCount", 0), "prompt_tok_s": None,
                      "gen_tokens": usage.get("candidatesTokenCount", 0), "gen_tok_s": None, "tool_calls": []}

    def installed_models(self):
        return self.local.installed_models()


def _rate(count, duration_ns):
    if not count or not duration_ns:
        return None
    return round(count / (duration_ns / 1e9), 1)
