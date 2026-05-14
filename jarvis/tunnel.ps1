# ============================================================
#  JARVIS — Windows Tunnel Launcher (PowerShell)
#  Run: powershell -ExecutionPolicy Bypass -File tunnel.ps1
# ============================================================

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "  J.A.R.V.I.S. - Starting tunnel..." -ForegroundColor Cyan
Write-Host ""

# ── Install Python deps if needed ───────────────────────────
Write-Host "  Checking Python dependencies..." -ForegroundColor Yellow
$depsOk = python -c "import fastapi,uvicorn,anthropic,httpx" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing Python dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt -q
}
Write-Host "  OK: Python ready" -ForegroundColor Green

# ── Download cloudflared.exe if missing ──────────────────────
$cf = "cloudflared.exe"
if (-not (Test-Path $cf)) {
    Write-Host "  Downloading cloudflared (free tunnel, one-time)..." -ForegroundColor Yellow
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $url -OutFile $cf -UseBasicParsing
    Write-Host "  OK: cloudflared downloaded" -ForegroundColor Green
} else {
    Write-Host "  OK: cloudflared already here" -ForegroundColor Green
}

# ── Create .env if missing ───────────────────────────────────
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "  Created .env — open it to add your API keys" -ForegroundColor Yellow
    }
}

# ── Create data dir ──────────────────────────────────────────
New-Item -ItemType Directory -Force -Path "data" | Out-Null

# ── Start JARVIS server ──────────────────────────────────────
$PORT = 8340
Write-Host "  Starting JARVIS server on port $PORT..." -ForegroundColor Yellow
$server = Start-Process python -ArgumentList "server.py","--host","127.0.0.1","--port","$PORT" -PassThru -WindowStyle Hidden

# Wait for server to be ready
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$PORT/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
}

if (-not $ready) {
    Write-Host ""
    Write-Host "  ERROR: Server did not start. Make sure Python is installed." -ForegroundColor Red
    Write-Host "  Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    $server | Stop-Process -Force -ErrorAction SilentlyContinue
    Read-Host "  Press Enter to exit"
    exit 1
}
Write-Host "  OK: JARVIS server running" -ForegroundColor Green

# ── Start Cloudflare tunnel ──────────────────────────────────
Write-Host "  Opening Cloudflare tunnel (free, works from anywhere)..." -ForegroundColor Yellow
$tunnelLog = [System.IO.Path]::GetTempFileName()
$tunnel = Start-Process ".\$cf" -ArgumentList "tunnel","--url","http://127.0.0.1:$PORT","--no-autoupdate" -PassThru -WindowStyle Hidden -RedirectStandardError $tunnelLog

# Wait for tunnel URL
$publicUrl = ""
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $tunnelLog) {
        $content = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
        if ($content -match 'https://[a-z0-9\-]+\.trycloudflare\.com') {
            $publicUrl = $Matches[0]
            break
        }
    }
}

Remove-Item $tunnelLog -ErrorAction SilentlyContinue

if (-not $publicUrl) {
    Write-Host ""
    Write-Host "  ERROR: Could not get tunnel URL. Check your internet connection." -ForegroundColor Red
    $tunnel | Stop-Process -Force -ErrorAction SilentlyContinue
    $server | Stop-Process -Force -ErrorAction SilentlyContinue
    Read-Host "  Press Enter to exit"
    exit 1
}

# ── Print the URL ────────────────────────────────────────────
Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host "   JARVIS IS LIVE - OPEN THIS ON YOUR IPHONE:" -ForegroundColor Green
Write-Host ""
Write-Host "   $publicUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Works from: T-Mobile 5G, any WiFi, anywhere in the world" -ForegroundColor Green
Write-Host "   Microphone: YES (HTTPS so Safari will allow it)" -ForegroundColor Green
Write-Host "   Cost: FREE" -ForegroundColor Green
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host ""

# Load .env to check keys
$envContent = if (Test-Path ".env") { Get-Content ".env" } else { @() }
$hasAnthropic = ($envContent | Where-Object { $_ -match "^ANTHROPIC_API_KEY=.{10}" }).Count -gt 0
$hasFish = ($envContent | Where-Object { $_ -match "^FISH_API_KEY=.{10}" }).Count -gt 0

if (-not $hasAnthropic -or -not $hasFish) {
    Write-Host "  !! Missing API keys - JARVIS needs these to work:" -ForegroundColor Yellow
    if (-not $hasAnthropic) {
        Write-Host "     ANTHROPIC_API_KEY  ->  console.anthropic.com  (free)" -ForegroundColor Yellow
    }
    if (-not $hasFish) {
        Write-Host "     FISH_API_KEY       ->  fish.audio  (free)" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "  After getting keys: open $publicUrl" -ForegroundColor Yellow
    Write-Host "  Then tap the menu (3 dots) -> Settings -> paste keys there" -ForegroundColor Yellow
    Write-Host ""
}

# Also open in default browser on the PC
Start-Process $publicUrl

Write-Host "  Close this window to stop JARVIS." -ForegroundColor Gray
Write-Host ""

# Keep running until window is closed
try {
    Wait-Process -Id $server.Id
} catch {
    # Server stopped
}

$tunnel | Stop-Process -Force -ErrorAction SilentlyContinue
$server | Stop-Process -Force -ErrorAction SilentlyContinue
