# Optional feature check: chat in online mode (hosted Gemma). Needs GEMINI_API_KEY in the user environment.
#   powershell -ExecutionPolicy Bypass -File scripts\test_online_chat.ps1
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:GEMINI_API_KEY = [Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONUNBUFFERED = "1"
$lines = @(
    "what can you help me with?",
    "Draft a three-line study plan for Operations Management.",
    "make that shorter",
    "/notes lean operations waste",
    "/exit"
)
$lines | & .\.venv\Scripts\wiki.exe chat --mode online
