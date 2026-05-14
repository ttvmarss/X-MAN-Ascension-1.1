#!/usr/bin/env bash
# ============================================================
#  JARVIS — First-Time Setup Script
#  Works on: macOS, Linux, Cloud VPS (Ubuntu/Debian)
# ============================================================
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   J.A.R.V.I.S. Setup                 ║"
echo "  ║   Just A Rather Very Intelligent Sys. ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: Python check ────────────────────────────────────
echo -e "${YELLOW}[1/6] Checking Python...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Python 3 not found. Install it from python.org${NC}"
    exit 1
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}  ✓ Python $PY_VER${NC}"

# ── Step 2: Node.js check ───────────────────────────────────
echo -e "${YELLOW}[2/6] Checking Node.js...${NC}"
if ! command -v node &>/dev/null; then
    echo -e "${RED}Node.js not found.${NC}"
    echo "  Install from: https://nodejs.org  (v18+ required)"
    echo "  Or on Ubuntu: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt install -y nodejs"
    exit 1
fi
NODE_VER=$(node --version)
echo -e "${GREEN}  ✓ Node.js $NODE_VER${NC}"

# ── Step 3: Python dependencies ─────────────────────────────
echo -e "${YELLOW}[3/6] Installing Python dependencies...${NC}"
pip3 install -r requirements.txt -q
echo -e "${GREEN}  ✓ Python packages installed${NC}"

# ── Step 4: Frontend dependencies ───────────────────────────
echo -e "${YELLOW}[4/6] Installing frontend dependencies...${NC}"
cd frontend && npm install --silent && cd ..
echo -e "${GREEN}  ✓ Frontend packages installed${NC}"

# ── Step 5: Build frontend ──────────────────────────────────
echo -e "${YELLOW}[5/6] Building frontend...${NC}"
cd frontend && npm run build --silent && cd ..
echo -e "${GREEN}  ✓ Frontend built${NC}"

# ── Step 6: Environment file ────────────────────────────────
echo -e "${YELLOW}[6/6] Setting up environment...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}  ✓ Created .env from .env.example${NC}"
    echo ""
    echo -e "${YELLOW}  ⚠ IMPORTANT: Edit .env and add your API keys:${NC}"
    echo "    ANTHROPIC_API_KEY  — from console.anthropic.com"
    echo "    FISH_API_KEY       — from fish.audio"
    echo ""
    echo "  Then run:  bash start.sh"
else
    echo -e "${GREEN}  ✓ .env already exists${NC}"
fi

# ── Data directory ──────────────────────────────────────────
mkdir -p data

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Setup complete!                     ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys"
echo "  2. Run:  bash start.sh"
echo "  3. Open your browser to:  http://YOUR-SERVER-IP:8340"
echo "  4. On iPhone: open the same URL in Safari/Chrome"
echo ""
echo "For cloud deployment (access from anywhere):"
echo "  docker compose up -d"
echo ""
