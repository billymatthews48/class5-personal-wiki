# Open vault/ in Obsidian and capture the three required screenshots into evidence\screenshots\.
#   powershell -ExecutionPolicy Bypass -File scripts\obsidian_screenshots.ps1
# 1. an open wiki note with related links and source references
# 2. the topic-organised index
# 3. the graph view filtered to curated notes (filter: path:wiki/ , Attachments off)
# Registers the vault with Obsidian if Obsidian has no vault list yet, and writes the graph filter
# to vault\.obsidian\graph.json. Captures only the Obsidian window region (ffmpeg gdigrab).
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$vault = Join-Path $root "vault"
$out = Join-Path $root "evidence\screenshots"
New-Item -ItemType Directory -Force $out, "$vault\.obsidian" | Out-Null

Get-Process Obsidian -ErrorAction SilentlyContinue | Stop-Process -Force   # so the graph settings below are read fresh
Start-Sleep 1
$cfg = "$env:APPDATA\obsidian\obsidian.json"
if (-not (Test-Path $cfg)) {
    $id = -join ((1..16) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 16) })
    $ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    # Write without a BOM: Obsidian ignores a vault list it cannot parse.
    [IO.File]::WriteAllText($cfg, (@{ vaults = @{ $id = @{ path = $vault; ts = $ts; open = $true } } } | ConvertTo-Json -Depth 5 -Compress))
    "registered vault with Obsidian: $vault"
}

$graph = @'
{
  "collapse-filter": false,
  "search": "path:wiki/",
  "showTags": false,
  "showAttachments": false,
  "hideUnresolved": true,
  "showOrphans": true,
  "collapse-color-groups": true,
  "colorGroups": [],
  "collapse-display": true,
  "showArrow": true,
  "textFadeMultiplier": -3,
  "nodeSizeMultiplier": 1.3,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.5,
  "repelStrength": 14,
  "linkStrength": 1,
  "linkDistance": 160,
  "scale": 0.62,
  "close": false
}
'@
[IO.File]::WriteAllText("$vault\.obsidian\graph.json", $graph)

Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Win {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, UIntPtr e);
}
"@
[Win]::SetProcessDPIAware() | Out-Null
Add-Type -AssemblyName System.Windows.Forms

$ff = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ff) {
    $ff = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter ffmpeg.exe |
        Select-Object -First 1 -ExpandProperty FullName
}

function Get-Obsidian {
    for ($i = 0; $i -lt 40; $i++) {
        $p = Get-Process Obsidian -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
        if ($p) { return $p }
        Start-Sleep -Milliseconds 500
    }
    throw "Obsidian window not found"
}

function Open-Note($relPath) {
    $uri = "obsidian://open?path=" + [uri]::EscapeDataString((Join-Path $vault $relPath))
    Start-Process $uri
    Start-Sleep 4
}

function Capture($name) {
    $p = Get-Obsidian
    [Win]::ShowWindow($p.MainWindowHandle, 3) | Out-Null        # maximise
    [Win]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    Start-Sleep 2
    $r = New-Object Win+RECT
    [Win]::GetWindowRect($p.MainWindowHandle, [ref]$r) | Out-Null
    $x = [Math]::Max(0, $r.L); $y = [Math]::Max(0, $r.T)
    $scr = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $w = [Math]::Min($r.R, $scr.Width) - $x; $h = [Math]::Min($r.B, $scr.Height) - $y
    $w -= $w % 2; $h -= $h % 2
    & $ff -y -loglevel error -f gdigrab -framerate 1 -offset_x $x -offset_y $y -video_size "${w}x${h}" -i desktop -frames:v 1 (Join-Path $out $name)
    "captured $name (${w}x${h}) window title: $($p.MainWindowTitle)"
}

Open-Note "wiki\People and Leadership\Negotiation.md"
Start-Sleep 4                                  # first launch: let the vault index
Capture "1-note-negotiation.png"

# Scroll the same note to its end so the Related links and Sources section are visible.
$p = Get-Obsidian
$r = New-Object Win+RECT
[Win]::GetWindowRect($p.MainWindowHandle, [ref]$r) | Out-Null
[Win]::SetCursorPos([int]($r.L + ($r.R - $r.L) * 0.62), [int]($r.T + ($r.B - $r.T) * 0.55)) | Out-Null
[Win]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero); [Win]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)   # click into the editor
Start-Sleep -Milliseconds 500
[System.Windows.Forms.SendKeys]::SendWait("^{END}")
Start-Sleep 1
Capture "1b-note-related-and-sources.png"

Open-Note "index.md"
Capture "2-index.png"

$p = Get-Obsidian
[Win]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
Start-Sleep 1
[System.Windows.Forms.SendKeys]::SendWait("^g")   # Ctrl+G: open graph view
Start-Sleep 8                                   # let the force layout settle
Capture "3-graph-path-wiki.png"

# Second graph shot with the filter panel collapsed, so no labels are hidden behind it.
Get-Process Obsidian -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 1
[IO.File]::WriteAllText("$vault\.obsidian\graph.json", $graph.Replace('"close": false', '"close": true'))
Open-Note "index.md"
Start-Sleep 3
$p = Get-Obsidian
[Win]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
Start-Sleep 1
[System.Windows.Forms.SendKeys]::SendWait("^g")
Start-Sleep 8
Capture "3b-graph-all-notes.png"
Get-Process Obsidian -ErrorAction SilentlyContinue | Stop-Process -Force
