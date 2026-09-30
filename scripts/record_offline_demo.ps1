# Unattended, recorded offline demonstration.
#
#   conhost.exe powershell -NoProfile -ExecutionPolicy Bypass -File scripts\record_offline_demo.ps1
#
# In order:
#   1. records THIS console window only (ffmpeg gdigrab, by window title) to evidence\<Label>\offline-demo.mp4
#   2. disconnects Wi-Fi (netsh wlan disconnect; no admin, no settings changed)
#   3. runs scripts\offline_demo.ps1 (offline proof, restart, doctor, ingest twice, search, ask, chat, all tests)
#   4. scrolls through the saved evidence so it is readable in the video
#   5. stops the recording and reconnects Wi-Fi (always, even if a step fails)
# Do not resize, minimise or cover the window while it runs.
param(
    [string]$Label = "offline-recorded",
    [string]$Source = "offline_source\Netflix Live Sports Strategy.docx",
    [string]$SearchQuery = "Netflix live sports broadcasting strategy",
    [switch]$TestOnly      # 6-second capture test: no Wi-Fi change, no demo
)
Set-Location (Split-Path $PSScriptRoot -Parent)
$title = "Wiki Offline Demo"
$Host.UI.RawUI.WindowTitle = $title
cmd /c "mode con: cols=150 lines=42" | Out-Null
Start-Sleep 1
New-Item -ItemType Directory -Force "evidence\$Label" | Out-Null
$video = Join-Path (Get-Location) "evidence\$Label\offline-demo.mp4"

$ff = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ff) {
    $ff = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
}
$rec = $null
if ($ff) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo $ff
    $psi.Arguments = "-y -loglevel quiet -f gdigrab -framerate 8 -i title=`"$title`" -c:v libx264 -preset ultrafast -crf 30 " +
                     "-pix_fmt yuv420p -vf `"scale=trunc(iw/2)*2:trunc(ih/2)*2`" `"$video`""
    $psi.UseShellExecute = $false
    $psi.RedirectStandardInput = $true     # so we can send 'q' to finish the file cleanly
    $psi.CreateNoWindow = $true
    $rec = [System.Diagnostics.Process]::Start($psi)
    Start-Sleep 2
    Write-Host "Recording this window to $video" -ForegroundColor Yellow
} else {
    Write-Host "ffmpeg not found: running without video (transcript is still saved)." -ForegroundColor Yellow
}

function Show-File($path, $delayMs = 50) {
    Write-Host "`n`n================ $path ================" -ForegroundColor Cyan
    Start-Sleep 2
    foreach ($line in Get-Content $path -Encoding UTF8) {
        if ($line.Length -gt 420) { $line = $line.Substring(0, 420) + " ..." }
        Write-Host $line
        Start-Sleep -Milliseconds $delayMs
    }
    Start-Sleep 3
}

$wifi = (netsh wlan show interfaces | Select-String '^\s*Profile\s*:\s*(.+)$' | Select-Object -First 1)
$profile = if ($wifi) { $wifi.Matches[0].Groups[1].Value.Trim() } else { $null }

try {
    if ($TestOnly) {
        1..12 | ForEach-Object { Write-Host "capture test line $_  $(Get-Date -Format T)" -ForegroundColor Green; Start-Sleep -Milliseconds 500 }
        return
    }
    Write-Host "Wi-Fi profile to restore afterwards: $profile"
    Write-Host "`nDisconnecting Wi-Fi..." -ForegroundColor Yellow
    netsh wlan disconnect | Out-Host
    Start-Sleep 3

    & powershell -NoProfile -ExecutionPolicy Bypass -File scripts\offline_demo.ps1 -Label $Label -Source $Source -SearchQuery $SearchQuery

    Write-Host "`n`n######## Scrolling through the saved evidence ########" -ForegroundColor Green
    $ev = "evidence\$Label"
    Show-File "$ev\summary.md" 120
    foreach ($t in "T1", "T2", "T3", "T4") { Show-File "$ev\ask\$t.md" }
    Show-File "$ev\mode_checks.md"
    Write-Host "`n`n######## Wiki pages in the vault ########" -ForegroundColor Green
    Get-ChildItem vault\wiki -Recurse -File | ForEach-Object { $_.FullName.Substring((Resolve-Path vault).Path.Length + 1) }
    Start-Sleep 4
    Show-File "vault\index.md" 120
    Write-Host "`nStill offline:" -ForegroundColor Yellow
    Test-NetConnection 8.8.8.8 -Port 53 -WarningAction SilentlyContinue | Select-Object ComputerName, TcpTestSucceeded | Out-String | Write-Host
    Get-Date
    Start-Sleep 3
}
finally {
    if ($rec -and -not $rec.HasExited) {
        $rec.StandardInput.Write("q")
        $rec.WaitForExit(20000) | Out-Null
    }
    if (-not $TestOnly -and $profile) {
        netsh wlan connect name="$profile" | Out-Host
        for ($i = 0; $i -lt 30; $i++) {      # wait for the connection before closing the window
            if ((Test-NetConnection 8.8.8.8 -Port 53 -WarningAction SilentlyContinue).TcpTestSucceeded) { break }
            Start-Sleep 2
        }
    }
}
