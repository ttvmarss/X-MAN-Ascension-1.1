Set-Location $PSScriptRoot

Write-Host ""
Write-Host "  JARVIS - Starting..." -ForegroundColor Cyan
Write-Host ""

$PORT = 8340

# Install Python deps if needed
$check = python -c "import fastapi,uvicorn,anthropic,httpx" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing Python packages..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt -q
}
Write-Host "  Python: OK" -ForegroundColor Green

# Download cloudflared.exe if missing
if (-not (Test-Path "cloudflared.exe")) {
    Write-Host "  Downloading Cloudflare tunnel tool..." -ForegroundColor Yellow
    $dlUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $dlUrl -OutFile "cloudflared.exe" -UseBasicParsing
    Write-Host "  Cloudflare tool: OK" -ForegroundColor Green
} else {
    Write-Host "  Cloudflare tool: OK" -ForegroundColor Green
}

# Create .env if missing
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "  Created .env file" -ForegroundColor Yellow
    }
}

# Create data dir
New-Item -ItemType Directory -Force -Path "data" | Out-Null

# Start JARVIS server
Write-Host "  Starting JARVIS server..." -ForegroundColor Yellow
$server = Start-Process python -ArgumentList "server.py","--host","127.0.0.1","--port","$PORT" -PassThru -WindowStyle Hidden

# Wait for server
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$PORT/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {}
}

if (-not $ready) {
    Write-Host ""
    Write-Host "  ERROR: Server did not start." -ForegroundColor Red
    Write-Host "  Make sure Python is installed: https://www.python.org/downloads/" -ForegroundColor Yellow
    $server | Stop-Process -Force -ErrorAction SilentlyContinue
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  JARVIS server: OK" -ForegroundColor Green

# Start Cloudflare tunnel
Write-Host "  Opening tunnel to the internet..." -ForegroundColor Yellow
$logFile = "$env:TEMP\cf-tunnel.log"
if (Test-Path $logFile) { Remove-Item $logFile }
$tunnel = Start-Process ".\cloudflared.exe" -ArgumentList "tunnel","--url","http://127.0.0.1:$PORT","--no-autoupdate" -PassThru -WindowStyle Hidden -RedirectStandardError $logFile

# Wait for tunnel URL
$publicUrl = ""
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $logFile) {
        $txt = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
        if ($txt -match 'https://[a-z0-9\-]+\.trycloudflare\.com') {
            $publicUrl = $Matches[0]
            break
        }
    }
}

if (-not $publicUrl) {
    Write-Host ""
    Write-Host "  ERROR: Could not get public URL." -ForegroundColor Red
    Write-Host "  Check your internet connection and try again." -ForegroundColor Yellow
    if (Test-Path $logFile) { Get-Content $logFile }
    $tunnel | Stop-Process -Force -ErrorAction SilentlyContinue
    $server | Stop-Process -Force -ErrorAction SilentlyContinue
    Read-Host "Press Enter to exit"
    exit 1
}

# Check API keys
$envLines = if (Test-Path ".env") { Get-Content ".env" } else { @() }
$hasAnthropic = ($envLines | Where-Object { $_ -match "^ANTHROPIC_API_KEY=.{10}" }).Count -gt 0
$hasFish = ($envLines | Where-Object { $_ -match "^FISH_API_KEY=.{10}" }).Count -gt 0

# Print the URL
Write-Host ""
Write-Host "  ======================================================" -ForegroundColor Green
Write-Host "  JARVIS IS LIVE" -ForegroundColor Green
Write-Host "  ======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Open this on your iPhone:" -ForegroundColor White
Write-Host ""
Write-Host "  $publicUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Works on: T-Mobile 5G, any WiFi, anywhere in the world" -ForegroundColor Green
Write-Host "  Mic works: YES - it uses HTTPS" -ForegroundColor Green
Write-Host "  Cost: FREE" -ForegroundColor Green
Write-Host "  ======================================================" -ForegroundColor Green
Write-Host ""

if (-not $hasAnthropic -or -not $hasFish) {
    Write-Host "  WARNING: Missing API keys - JARVIS needs these:" -ForegroundColor Yellow
    if (-not $hasAnthropic) {
        Write-Host "    Anthropic key: console.anthropic.com (free)" -ForegroundColor Yellow
    }
    if (-not $hasFish) {
        Write-Host "    Fish Audio key: fish.audio then API Keys (free)" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "  Open the URL above, tap the 3-dot menu, tap Settings" -ForegroundColor Yellow
    Write-Host "  and paste your keys there. No file editing needed." -ForegroundColor Yellow
    Write-Host ""
}

# Open in browser on PC too
Start-Process $publicUrl

Write-Host "  Close this window to stop JARVIS." -ForegroundColor Gray
Write-Host ""

# Keep alive
try {
    Wait-Process -Id $server.Id -ErrorAction SilentlyContinue
} catch {}

$tunnel | Stop-Process -Force -ErrorAction SilentlyContinue
$server | Stop-Process -Force -ErrorAction SilentlyContinue
