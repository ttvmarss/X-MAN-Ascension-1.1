#!/usr/bin/env bash
# ============================================================
#  JARVIS — Start Script
# ============================================================

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

cd "$(dirname "$0")"

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   J.A.R.V.I.S.  Starting...          ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ── Auto-create .env if missing ─────────────────────────────
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}  Created .env from .env.example${NC}"
    else
        touch .env
    fi
fi

# Load env vars
set -a; source .env; set +a

PORT="${PORT:-8340}"
HOST="${HOST:-0.0.0.0}"

# ── Build frontend if dist is missing ───────────────────────
if [ ! -d "frontend/dist" ]; then
    echo -e "${YELLOW}  Frontend not built yet — building now...${NC}"
    if command -v node &>/dev/null && [ -d "frontend" ]; then
        cd frontend
        npm install --silent 2>/dev/null
        npm run build --silent 2>/dev/null && echo -e "${GREEN}  ✓ Frontend built${NC}" || echo -e "${RED}  ✗ Frontend build failed (server still starts)${NC}"
        cd ..
    else
        echo -e "${RED}  Node.js not found — skipping frontend build${NC}"
        echo "  Install Node.js from: https://nodejs.org"
    fi
fi

# ── Get IP addresses for display ────────────────────────────
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "")
fi
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="localhost"
fi

echo ""
echo -e "${GREEN}  ┌──────────────────────────────────────────┐${NC}"
echo -e "${GREEN}  │  JARVIS is running at:                   │${NC}"
echo -e "${CYAN}  │                                          │${NC}"
echo -e "${CYAN}  │  Local PC:  http://localhost:${PORT}      │${NC}"
echo -e "${CYAN}  │  Network:   http://${LOCAL_IP}:${PORT}      │${NC}"
echo -e "${CYAN}  │                                          │${NC}"
echo -e "${GREEN}  │  iPhone: Open the Network URL above     │${NC}"
echo -e "${GREEN}  │          in Safari (same WiFi required) │${NC}"
echo -e "${GREEN}  └──────────────────────────────────────────┘${NC}"
echo ""

# ── Warn about missing API keys ──────────────────────────────
MISSING_KEYS=0
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your-anthropic-api-key-here" ]; then
    echo -e "${YELLOW}  ⚠  ANTHROPIC_API_KEY not set — JARVIS won't be able to think${NC}"
    echo "     Get one free at: console.anthropic.com"
    echo "     Then edit .env and add:  ANTHROPIC_API_KEY=sk-ant-..."
    MISSING_KEYS=1
fi
if [ -z "$FISH_API_KEY" ] || [ "$FISH_API_KEY" = "your-fish-audio-api-key-here" ]; then
    echo -e "${YELLOW}  ⚠  FISH_API_KEY not set — JARVIS won't have a voice${NC}"
    echo "     Get one free at: fish.audio → API Keys"
    echo "     Then edit .env and add:  FISH_API_KEY=your-key"
    MISSING_KEYS=1
fi

if [ "$MISSING_KEYS" = "1" ]; then
    echo ""
    echo -e "${YELLOW}  Edit .env now:  nano .env  (or open it in any text editor)${NC}"
    echo -e "${YELLOW}  Then restart:   bash start.sh${NC}"
    echo ""
fi

if [ -n "$AUTH_TOKEN" ]; then
    echo -e "${YELLOW}  Auth token required for remote access (set in .env)${NC}"
fi

echo "  Press Ctrl+C to stop."
echo ""

# Ensure data dir
mkdir -p data

# Start the server
exec python3 server.py --host "$HOST" --port "$PORT"
