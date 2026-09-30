"""Shared helpers for the test and benchmark scripts."""
import json
import platform
import socket
import subprocess
from datetime import datetime
from pathlib import Path

import psutil

from wiki import config
from wiki.llm import OllamaClient

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence"


def internet_status():
    """Probe two public hosts. Used only to *label* evidence as online/offline; nothing is sent."""
    for host in (("1.1.1.1", 443), ("8.8.8.8", 53)):
        try:
            socket.create_connection(host, timeout=2).close()
            return "reachable"
        except OSError:
            pass
    return "unreachable (offline)"


def ollama_version():
    try:
        exe = Path.home() / "AppData/Local/Programs/Ollama/ollama.exe"
        return subprocess.run([str(exe), "--version"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return "unknown"


def environment():
    vm = psutil.virtual_memory()
    return {
        "time": datetime.now().isoformat(timespec="seconds"),
        "internet": internet_status(),
        "execution": "local",
        "model": config.CHAT_MODEL, "embed_model": config.EMBED_MODEL,
        "runtime": ollama_version(), "num_ctx": config.NUM_CTX, "think": config.THINK,
        "os": platform.platform(), "cpu": platform.processor(),
        "ram_total_gb": round(vm.total / 2**30, 1), "ram_available_gb": round(vm.available / 2**30, 1),
    }


class CountingClient(OllamaClient):
    """OllamaClient that counts generation calls, so tests can prove search never calls Gemma."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.chat_calls = 0

    def chat(self, *a, **k):
        self.chat_calls += 1
        return super().chat(*a, **k)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dump(path, obj):
    write(path, json.dumps(obj, indent=2, ensure_ascii=False, default=str))
