Set-Location $PSScriptRoot
$PORT = 8340

Write-Host ""
Write-Host "  JARVIS - Starting..." -ForegroundColor Cyan
Write-Host ""

# Kill anything already on port 8340
$oldProc = netstat -ano 2>$null | Select-String ":$PORT " | ForEach-Object {
    ($_ -split '\s+')[-1]
} | Select-Object -First 1
if ($oldProc -and $oldProc -match '^\d+$') {
    try { Stop-Process -Id ([int]$oldProc) -Force -ErrorAction SilentlyContinue } catch {}
}

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

# Read Groq key from .env — look for any line with a real key value
$groqKey = ""
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^GROQ_API_KEY=(.+)$") {
            $val = $Matches[1].Trim().Trim('"').Trim("'")
            if ($val.Length -gt 10 -and $val -notmatch "PASTE|your-key|example") {
                $groqKey = $val
            }
        }
    }
}

if ($groqKey) {
    Write-Host "  Groq API key: OK" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  No Groq API key found in .env" -ForegroundColor Yellow
    Write-Host "  JARVIS will start but cannot answer questions." -ForegroundColor Yellow
    Write-Host "  Get a free key at console.groq.com then add it:" -ForegroundColor Yellow
    Write-Host "  Add-Content .env 'GROQ_API_KEY=your-key'" -ForegroundColor Cyan
    Write-Host ""
}

# Write clean .env
Set-Content -Path ".env" -Value "GROQ_API_KEY=$groqKey"

# Create data dir
New-Item -ItemType Directory -Force -Path "data" | Out-Null

# Start JARVIS server — log output so we can debug crashes
Write-Host "  Starting JARVIS server..." -ForegroundColor Yellow
$serverLog = "$env:TEMP\jarvis-server-$PID.log"
$server = Start-Process python -ArgumentList "server.py","--host","127.0.0.1","--port","$PORT" -PassThru -WindowStyle Hidden -RedirectStandardOutput $serverLog -RedirectStandardError $serverLog

# Wait for server to be ready
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$PORT/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    # Show error if server already died
    if ($server.HasExited) {
        Write-Host "  Server crashed on startup. Error:" -ForegroundColor Red
        if (Test-Path $serverLog) { Get-Content $serverLog | Select-Object -Last 10 }
        Read-Host "Press Enter to exit"
        exit 1
    }
}

if (-not $ready) {
    Write-Host "  Server did not respond. Last log:" -ForegroundColor Red
    if (Test-Path $serverLog) { Get-Content $serverLog | Select-Object -Last 10 }
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "  JARVIS server: OK" -ForegroundColor Green

# Start Cloudflare tunnel
Write-Host "  Opening tunnel to the internet..." -ForegroundColor Yellow
$cfLog = "$env:TEMP\jarvis-cf-$PID.log"
$tunnel = Start-Process ".\cloudflared.exe" -ArgumentList "tunnel","--url","http://127.0.0.1:$PORT","--no-autoupdate" -PassThru -WindowStyle Hidden -RedirectStandardError $cfLog

# Wait for tunnel URL
$publicUrl = ""
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $cfLog) {
        $txt = Get-Content $cfLog -Raw -ErrorAction SilentlyContinue
        if ($txt -match 'https://[a-z0-9\-]+\.trycloudflare\.com') {
            $publicUrl = $Matches[0]; break
        }
    }
}

if (-not $publicUrl) {
    Write-Host "  ERROR: Could not get public URL. Check internet." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Open in browser
Start-Process $publicUrl

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

# Keep alive — show message only when something changes
$restartCount = 0
while ($true) {
    Start-Sleep -Seconds 5
    if ($server.HasExited) {
        $restartCount++
        Write-Host "  Server stopped (restart #$restartCount) - restarting in 3 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        $server = Start-Process python -ArgumentList "server.py","--host","127.0.0.1","--port","$PORT" -PassThru -WindowStyle Hidden -RedirectStandardOutput $serverLog -RedirectStandardError $serverLog
        Start-Sleep -Seconds 3
        Write-Host "  Server restarted. JARVIS URL still works: $publicUrl" -ForegroundColor Green
    }
}
