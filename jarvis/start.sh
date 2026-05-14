#!/usr/bin/env bash
# ============================================================
#  JARVIS — Start Script
#  Starts the backend server (frontend is pre-built and served by server)
# ============================================================

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check .env exists
if [ ! -f .env ]; then
    echo -e "${RED}No .env file found. Run:  bash setup.sh${NC}"
    exit 1
fi

# Load env vars
set -a; source .env; set +a

# Validate required keys
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your-anthropic-api-key-here" ]; then
    echo -e "${RED}ANTHROPIC_API_KEY not set in .env${NC}"
    echo "Get one at: console.anthropic.com"
    exit 1
fi

PORT="${PORT:-8340}"
HOST="${HOST:-0.0.0.0}"

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   J.A.R.V.I.S.  Starting...          ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Get local IP for display
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig getifaddr en0 2>/dev/null || echo "localhost")

echo -e "${GREEN}  Server:    http://${LOCAL_IP}:${PORT}${NC}"
echo -e "${GREEN}  iPhone:    Open http://${LOCAL_IP}:${PORT} in Safari/Chrome${NC}"
if [ -n "$AUTH_TOKEN" ]; then
    echo -e "${YELLOW}  Auth:      Token required (set in .env)${NC}"
fi
echo ""
echo "  Press Ctrl+C to stop."
echo ""

# Ensure data dir
mkdir -p data

# Start the server
exec python3 server.py --host "$HOST" --port "$PORT"
