"""Paths, model names and tunable limits. Everything is local; env vars can override."""
import os
from pathlib import Path

ROOT = Path(os.environ.get("WIKI_ROOT", Path(__file__).resolve().parent.parent))
VAULT = ROOT / "vault"            # the Obsidian vault (open this folder in Obsidian)
RAW = VAULT / "raw"               # unchanged originals, read-only
WIKI = VAULT / "wiki"             # generated, reviewed subject notes
STATE = ROOT / ".wiki"            # machine state: manifest, chunks, vectors, saved runs
SUBJECTS_FILE = ROOT / "subjects.yaml"   # which raw files belong to which subject note
PROMPTS = ROOT / "prompts"
RUNS = STATE / "runs"
ARCHIVE = STATE / "archive"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.environ.get("WIKI_MODEL", "gemma4:e4b-it-q4_K_M")
EMBED_MODEL = os.environ.get("WIKI_EMBED_MODEL", "embeddinggemma")
NUM_CTX = int(os.environ.get("WIKI_NUM_CTX", "8192"))
THINK = os.environ.get("WIKI_THINK", "0") == "1"   # Gemma 4 thinks by default; off keeps CPU latency sane
REQUEST_TIMEOUT = 900

# Topic folders in the vault. Kept few and broad so the Obsidian tree stays browsable.
FOLDERS = [
    "AI and Technology",
    "Work and Career",
    "Learning and Courses",
    "Health and Wellbeing",
    "Money and Admin",
    "Life and Relationships",
]

CHUNK_CHARS = 900        # target characters per retrieval chunk
CHUNK_OVERLAP = 150
ASK_TOP_K = 4            # passages handed to the model in ask mode
ASK_MIN_COSINE = 0.45    # below this, ask refuses (tuned against the real wiki; see README)
ASK_EVIDENCE_CHARS = 4000  # prompt budget for evidence (4 passages); prompt eval is ~13 tok/s on this CPU
CHAT_HISTORY_CHARS = 8000  # rolling chat context budget
TITLE_INPUT_CHARS = 3000   # how much of a source the titler reads
