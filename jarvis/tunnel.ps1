Set-Location $PSScriptRoot
$PORT = 8340

Write-Host ""
Write-Host "  JARVIS - Starting..." -ForegroundColor Cyan
Write-Host ""

# Install Python deps if needed
python -c "import fastapi,uvicorn,anthropic,httpx" 2>$null
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
}
Write-Host "  Cloudflare tool: OK" -ForegroundColor Green

# Fix .env — write a clean one with just the Groq key
$groqKey = ""
if (Test-Path ".env") {
    $lines = Get-Content ".env"
    # Find the LAST valid GROQ_API_KEY line (ignore placeholder ones)
    foreach ($line in $lines) {
        if ($line -match "^GROQ_API_KEY=(.{20,})$") {
            $candidate = $Matches[1].Trim()
            if ($candidate -notmatch "PASTE|your|example|here") {
                $groqKey = $candidate
            }
        }
    }
}

# Write a clean .env
$envContent = "GROQ_API_KEY=$groqKey"
Set-Content -Path ".env" -Value $envContent

if (-not $groqKey) {
    Write-Host ""
    Write-Host "  No Groq API key found. Get one free:" -ForegroundColor Yellow
    Write-Host "  1. Go to console.groq.com and sign up (email only)" -ForegroundColor Yellow
    Write-Host "  2. Click API Keys then Create API Key" -ForegroundColor Yellow
    Write-Host "  3. Close this window, open PowerShell in this folder and run:" -ForegroundColor Yellow
    Write-Host "     Add-Content .env 'GROQ_API_KEY=your-key-here'" -ForegroundColor Cyan
    Write-Host "  4. Run JARVIS.bat again" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "  Groq API key: OK" -ForegroundColor Green
}

# Create data dir
New-Item -ItemType Directory -Force -Path "data" | Out-Null

# Start JARVIS server
Write-Host "  Starting JARVIS server..." -ForegroundColor Yellow
$server = Start-Process python -ArgumentList "server.py","--host","127.0.0.1","--port","$PORT" -PassThru -WindowStyle Hidden

# Wait for server to be ready
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$PORT/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
}

if (-not $ready) {
    Write-Host "  ERROR: Server did not start." -ForegroundColor Red
    Write-Host "  Make sure Python is installed from python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  JARVIS server: OK" -ForegroundColor Green

# Start Cloudflare tunnel — use unique log file per run
Write-Host "  Opening tunnel to the internet..." -ForegroundColor Yellow
$logFile = "$env:TEMP\jarvis-cf-$PID.log"
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
    Write-Host "  ERROR: Could not get public URL. Check internet connection." -ForegroundColor Red
    $tunnel | Stop-Process -Force -ErrorAction SilentlyContinue
    $server | Stop-Process -Force -ErrorAction SilentlyContinue
    Read-Host "Press Enter to exit"
    exit 1
}

# Open browser
Start-Process $publicUrl

# Print URL
Write-Host ""
Write-Host "  ======================================================" -ForegroundColor Green
Write-Host "  JARVIS IS LIVE - OPEN THIS ON YOUR iPHONE:" -ForegroundColor Green
Write-Host ""
Write-Host "  $publicUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Works from anywhere: 5G, WiFi, worldwide. Free." -ForegroundColor Green
Write-Host "  ======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  DO NOT CLOSE THIS WINDOW - Closing stops JARVIS." -ForegroundColor Red
Write-Host ""

# Keep alive forever — restart server if it crashes
while ($true) {
    Start-Sleep -Seconds 5
    if ($server.HasExited) {
        Write-Host "  Server restarting..." -ForegroundColor Yellow
        $server = Start-Process python -ArgumentList "server.py","--host","127.0.0.1","--port","$PORT" -PassThru -WindowStyle Hidden
    }
}
