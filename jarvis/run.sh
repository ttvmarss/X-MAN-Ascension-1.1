#!/usr/bin/env bash
# ============================================================
#  JARVIS — One-command launcher
#  Run this and open the URL it prints in any browser.
# ============================================================
set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${GREEN}  J.A.R.V.I.S. starting...${NC}"
echo ""

# ── 1. Create .env if missing ────────────────────────────────
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || touch .env
fi

# Load env vars
set -a; source .env; set +a 2>/dev/null || true

PORT="${PORT:-8340}"

# ── 2. Install Python deps if needed ────────────────────────
if ! python3 -c "import fastapi,uvicorn,anthropic,httpx" 2>/dev/null; then
    echo -e "${YELLOW}  Installing Python dependencies...${NC}"
    pip3 install -r requirements.txt -q
fi

# ── 3. Get network IP ────────────────────────────────────────
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$IP" ] && IP=$(ipconfig getifaddr en0 2>/dev/null)
[ -z "$IP" ] && IP="localhost"

echo -e "${GREEN}  ╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}  ║  JARVIS is ONLINE                        ║${NC}"
echo -e "${GREEN}  ╠══════════════════════════════════════════╣${NC}"
echo -e "${CYAN}  ║  PC:     http://localhost:${PORT}         ║${NC}"
echo -e "${CYAN}  ║  Phone:  http://${IP}:${PORT}         ║${NC}"
echo -e "${GREEN}  ╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}  ║  ↑ Type the Phone URL into Safari/Chrome ║${NC}"
echo -e "${GREEN}  ║    (phone must be on same WiFi as PC)    ║${NC}"
echo -e "${GREEN}  ╚══════════════════════════════════════════╝${NC}"
echo ""

# ── Warn if API keys are missing ─────────────────────────────
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your-anthropic-api-key-here" ]; then
    echo -e "${YELLOW}  ⚠  No Anthropic key — JARVIS can't think. Open http://${IP}:${PORT}${NC}"
    echo -e "${YELLOW}     then go to Settings (⋮ menu) → enter your API keys there.${NC}"
    echo ""
fi

echo "  Press Ctrl+C to stop."
echo ""

mkdir -p data
exec python3 server.py --host 0.0.0.0 --port "$PORT"
