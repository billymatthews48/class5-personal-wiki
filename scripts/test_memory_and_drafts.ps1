# Optional feature check: explicit memory (/remember) and drafts (/draft) in chat, and proof that
# neither is treated as evidence by ask or returned by search.
#   powershell -ExecutionPolicy Bypass -File scripts\test_memory_and_drafts.ps1
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONUNBUFFERED = "1"
$wiki = ".\.venv\Scripts\wiki.exe"

"### 1. chat: /remember, then /reset, then a question that needs the memory, a draft, /draft, an unknown command"
$lines = @(
    "/remember My preferred revision method is active recall with flashcards.",
    "/reset",
    "What revision method do I prefer?",
    "Draft a two-line reminder to myself about revising Negotiation.",
    "/draft",
    "/savememory please",
    "/exit"
)
$lines | & $wiki chat

"### 2. files written (inside the vault, outside raw/)"
Get-ChildItem vault\memory, vault\drafts -File -ErrorAction SilentlyContinue |
    ForEach-Object { $_.FullName.Substring((Resolve-Path vault).Path.Length + 1) }
"--- vault\memory\Chat Memory.md"
Get-Content "vault\memory\Chat Memory.md" -ErrorAction SilentlyContinue

"### 3. ask must NOT treat the remembered fact as evidence"
& $wiki ask "What revision method do I prefer?"

"### 4. search must not return the memory or the draft (the index covers raw/ only)"
& $wiki search "active recall flashcards preferred revision method" -k 3 --keyword |
    Select-String "^\[" | ForEach-Object Line
