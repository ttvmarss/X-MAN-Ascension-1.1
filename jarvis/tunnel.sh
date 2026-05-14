#!/usr/bin/env bash
# ============================================================
#  JARVIS — Free Public Access via Cloudflare Tunnel
#
#  Works from ANYWHERE: T-Mobile 5G, home WiFi, work, anywhere.
#  100% FREE. No account needed. Gives real HTTPS so mic works.
#  Only YOU know the URL — no one else can find it.
#
#  Usage:  bash tunnel.sh
# ============================================================
set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PORT="${PORT:-8340}"

echo ""
echo -e "${BLUE}  ╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}  ║   J.A.R.V.I.S.  — Public Tunnel Setup   ║${NC}"
echo -e "${BLUE}  ╚═══════════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: Load .env ────────────────────────────────────────
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || touch .env
fi
set -a; source .env; set +a 2>/dev/null || true

# ── Step 2: Check/install cloudflared ───────────────────────
install_cloudflared() {
    echo -e "${YELLOW}  Installing cloudflared (free Cloudflare tunnel)...${NC}"
    OS="$(uname -s)"
    ARCH="$(uname -m)"

    if [ "$OS" = "Linux" ]; then
        if [ "$ARCH" = "x86_64" ]; then
            URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
            URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
        else
            echo -e "${RED}  Unsupported arch: $ARCH${NC}"; exit 1
        fi
        curl -fsSL "$URL" -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
    elif [ "$OS" = "Darwin" ]; then
        if command -v brew &>/dev/null; then
            brew install cloudflare/cloudflare/cloudflared
        else
            if [ "$ARCH" = "arm64" ]; then
                URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
            else
                URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
            fi
            curl -fsSL "$URL" | tar -xz -C /usr/local/bin
            chmod +x /usr/local/bin/cloudflared
        fi
    else
        echo -e "${RED}  OS not detected. Download cloudflared from: https://github.com/cloudflare/cloudflared/releases${NC}"
        exit 1
    fi
    echo -e "${GREEN}  ✓ cloudflared installed${NC}"
}

if ! command -v cloudflared &>/dev/null; then
    install_cloudflared
else
    echo -e "${GREEN}  ✓ cloudflared already installed${NC}"
fi

# ── Step 3: Install Python deps if needed ───────────────────
if ! python3 -c "import fastapi,uvicorn,anthropic,httpx" 2>/dev/null; then
    echo -e "${YELLOW}  Installing Python dependencies...${NC}"
    pip3 install -r requirements.txt -q
fi

# ── Step 4: Start JARVIS server in background ────────────────
mkdir -p data
echo -e "${YELLOW}  Starting JARVIS server on port ${PORT}...${NC}"
python3 server.py --host 127.0.0.1 --port "$PORT" &
SERVER_PID=$!

# Wait for server to be ready
for i in {1..15}; do
    if curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
        echo -e "${GREEN}  ✓ JARVIS server running (PID $SERVER_PID)${NC}"
        break
    fi
    sleep 1
done

if ! curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
    echo -e "${RED}  Server failed to start. Check for errors above.${NC}"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# ── Step 5: Generate or load secret token ───────────────────
TOKEN_FILE=".tunnel_token"
if [ -z "$AUTH_TOKEN" ]; then
    if [ -f "$TOKEN_FILE" ]; then
        AUTH_TOKEN=$(cat "$TOKEN_FILE")
    else
        # Generate a random token
        AUTH_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
        echo "$AUTH_TOKEN" > "$TOKEN_FILE"
        chmod 600 "$TOKEN_FILE"
    fi
    # Save to .env
    python3 -c "
import re, pathlib
env = pathlib.Path('.env')
text = env.read_text() if env.exists() else ''
if 'AUTH_TOKEN=' in text:
    text = re.sub(r'^AUTH_TOKEN=.*$', f'AUTH_TOKEN=${AUTH_TOKEN}', text, flags=re.MULTILINE)
else:
    text += f'\nAUTH_TOKEN=${AUTH_TOKEN}\n'
env.write_text(text)
"
fi

echo ""

# ── Step 6: Start the tunnel ─────────────────────────────────
TUNNEL_LOG=$(mktemp)
cloudflared tunnel --url "http://127.0.0.1:${PORT}" --no-autoupdate 2>"$TUNNEL_LOG" &
TUNNEL_PID=$!

# Wait for tunnel URL to appear
echo -e "${YELLOW}  Starting Cloudflare tunnel (free, no account needed)...${NC}"
PUBLIC_URL=""
for i in {1..30}; do
    PUBLIC_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -1)
    if [ -n "$PUBLIC_URL" ]; then
        break
    fi
    sleep 1
done

if [ -z "$PUBLIC_URL" ]; then
    echo -e "${RED}  Could not get tunnel URL. Check internet connection.${NC}"
    cat "$TUNNEL_LOG"
    kill $SERVER_PID $TUNNEL_PID 2>/dev/null
    exit 1
fi

rm -f "$TUNNEL_LOG"

# ── Done — print everything the user needs ───────────────────
echo ""
echo -e "${GREEN}  ╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}  ║  JARVIS IS LIVE — accessible from ANYWHERE          ║${NC}"
echo -e "${GREEN}  ╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}  ║                                                      ║${NC}"
echo -e "${CYAN}  ║  Your URL:  ${PUBLIC_URL}  ║${NC}"
echo -e "${CYAN}  ║                                                      ║${NC}"
echo -e "${GREEN}  ╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}  ║  ✓ Works on T-Mobile 5G, any WiFi, anywhere         ║${NC}"
echo -e "${GREEN}  ║  ✓ HTTPS — microphone will work on iPhone           ║${NC}"
echo -e "${GREEN}  ║  ✓ Private — only you know this URL                 ║${NC}"
echo -e "${GREEN}  ╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ── API keys reminder ────────────────────────────────────────
MISSING=0
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your-anthropic-api-key-here" ]; then
    echo -e "${YELLOW}  ⚠  Missing: ANTHROPIC_API_KEY (JARVIS needs this to think)${NC}"
    echo -e "${YELLOW}     → Free at: https://console.anthropic.com${NC}"
    MISSING=1
fi
if [ -z "$FISH_API_KEY" ] || [ "$FISH_API_KEY" = "your-fish-audio-api-key-here" ]; then
    echo -e "${YELLOW}  ⚠  Missing: FISH_API_KEY (JARVIS needs this to speak)${NC}"
    echo -e "${YELLOW}     → Free tier at: https://fish.audio (API Keys section)${NC}"
    MISSING=1
fi
if [ "$MISSING" = "1" ]; then
    echo ""
    echo -e "${YELLOW}  Add keys: open ${PUBLIC_URL} → tap ⋮ menu → Settings${NC}"
    echo ""
fi

echo -e "  Open this on your iPhone (Safari):  ${CYAN}${PUBLIC_URL}${NC}"
echo ""
echo -e "  ${YELLOW}Note: URL changes each restart (free tier). Bookmark it after each start.${NC}"
echo "  Press Ctrl+C to stop everything."
echo ""

# ── Cleanup on exit ──────────────────────────────────────────
cleanup() {
    echo ""
    echo -e "${YELLOW}  Shutting down...${NC}"
    kill $TUNNEL_PID 2>/dev/null
    kill $SERVER_PID 2>/dev/null
    echo -e "${GREEN}  Done.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Keep running
wait $SERVER_PID
