# Offline demonstration. Run with Wi-Fi/Ethernet OFF:
#   powershell -ExecutionPolicy Bypass -File scripts\offline_demo.ps1
# Records everything to evidence\offline\transcript.txt
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONIOENCODING = "utf-8"
$wiki = ".\.venv\Scripts\wiki.exe"
$py = ".\.venv\Scripts\python.exe"
$ollama = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
New-Item -ItemType Directory -Force evidence\offline | Out-Null
Start-Transcript -Path evidence\offline\transcript.txt -Force

Write-Host "`n===== 1. Device and time =====" -ForegroundColor Cyan
Get-Date
$os = Get-CimInstance Win32_OperatingSystem; $cs = Get-CimInstance Win32_ComputerSystem
"OS: $($os.Caption) $($os.Version)"
"CPU: $((Get-CimInstance Win32_Processor).Name)"
"RAM total GB: $([math]::Round($cs.TotalPhysicalMemory/1GB,1)) | free GB: $([math]::Round($os.FreePhysicalMemory/1MB,1))"
"GPU: $((Get-CimInstance Win32_VideoController).Name -join ', ')"

Write-Host "`n===== 2. Proof the internet is disconnected =====" -ForegroundColor Cyan
Get-NetAdapter | Select-Object Name, Status | Format-Table -AutoSize
Test-NetConnection 8.8.8.8 -Port 53 -WarningAction SilentlyContinue | Select-Object ComputerName, TcpTestSucceeded
try { Resolve-DnsName github.com -ErrorAction Stop | Out-Null; "DNS: github.com RESOLVED (still online!)" } catch { "DNS: github.com could not be resolved (offline)" }

Write-Host "`n===== 3. Restart the local runtime (Ollama) =====" -ForegroundColor Cyan
Get-Process | Where-Object { $_.Name -like "ollama*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Start-Process $ollama -ArgumentList "serve" -WindowStyle Hidden
for ($i = 0; $i -lt 30; $i++) { try { Invoke-RestMethod http://localhost:11434/api/tags -TimeoutSec 2 | Out-Null; break } catch { Start-Sleep 1 } }
& $ollama --version
& $ollama list

Write-Host "`n===== 4. Restart the CLI: help and doctor =====" -ForegroundColor Cyan
& $wiki --help
& $wiki doctor

Write-Host "`n===== 5. Ingest a NEW local source while offline =====" -ForegroundColor Cyan
& $wiki ingest "offline_source\Energy Transition Memo.docx"
Get-ChildItem "vault\wiki" -Recurse -File | Select-Object -ExpandProperty Name

Write-Host "`n===== 6. Search (original passages, no model) =====" -ForegroundColor Cyan
& $wiki search "AI-assisted energy procurement platform for mid-sized firms" -k 3

Write-Host "`n===== 7. Ask (one example from the CLI) =====" -ForegroundColor Cyan
& $wiki ask "According to my personal development notes, what are the three components of career success and how much does each matter?"

Write-Host "`n===== 8. All four ask tests + chat/search mode checks =====" -ForegroundColor Cyan
& $py tests\run_tests.py --label offline

Write-Host "`n===== 9. Memory in use after the run =====" -ForegroundColor Cyan
& $ollama ps
Get-Process | Where-Object { $_.Name -like "ollama*" } | Select-Object Name, Id, @{n='RSS_MB';e={[math]::Round($_.WorkingSet64/1MB)}} | Format-Table -AutoSize
"free RAM GB: $([math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1))"
Get-Date
Stop-Transcript
Write-Host "`nDONE. Reconnect Wi-Fi and tell Claude." -ForegroundColor Green
