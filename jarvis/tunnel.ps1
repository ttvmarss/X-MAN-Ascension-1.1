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
$logFile = "$env:TEMP\cf-tunnel-$PID.log"
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

# Check which AI key is configured
$envLines = if (Test-Path ".env") { Get-Content ".env" } else { @() }
$hasGroq      = ($envLines | Where-Object { $_ -match "^GROQ_API_KEY=.{10}" }).Count -gt 0
$hasAnthropic = ($envLines | Where-Object { $_ -match "^ANTHROPIC_API_KEY=.{10}" }).Count -gt 0
$hasAnyLLM    = $hasGroq -or $hasAnthropic

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
Write-Host "  Mic works: YES - HTTPS enabled" -ForegroundColor Green
Write-Host "  Voice: Browser built-in (free, no signup)" -ForegroundColor Green
Write-Host "  ======================================================" -ForegroundColor Green
Write-Host ""

if (-not $hasAnyLLM) {
    Write-Host "  ACTION NEEDED - Add a free AI key so JARVIS can think:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Go to console.groq.com" -ForegroundColor Cyan
    Write-Host "  2. Sign up free with your email (no credit card)" -ForegroundColor Cyan
    Write-Host "  3. Click API Keys then Create API Key" -ForegroundColor Cyan
    Write-Host "  4. Open the URL above on your phone" -ForegroundColor Cyan
    Write-Host "  5. Tap the 3-dot menu, tap Settings, paste key as GROQ_API_KEY" -ForegroundColor Cyan
    Write-Host ""
}

# Open in browser on PC too
Start-Process $publicUrl

Write-Host "  DO NOT CLOSE THIS WINDOW - JARVIS stops if you close it." -ForegroundColor Red
Write-Host ""

# Keep alive - loop so it never exits until user closes window
while ($true) {
    Start-Sleep -Seconds 5
    # Restart server if it crashed
    if ($server.HasExited) {
        Write-Host "  Server stopped - restarting..." -ForegroundColor Yellow
        $server = Start-Process python -ArgumentList "server.py","--host","127.0.0.1","--port","$PORT" -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 3
    }
}
