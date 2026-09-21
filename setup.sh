#!/bin/bash
# Product Management Skill Jev - Setup Script

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}Product Management Skill Jev - Setup${NC}"
echo "════════════════════════════════════════"
echo ""

# ── Step 1: Check Claude Code ────────────────────────────────────
if ! command -v claude &> /dev/null; then
  echo -e "${YELLOW}Claude Code is not installed.${NC}"
  echo "Install from: https://claude.ai/download"
  echo "Then run this setup again."
  echo ""
fi

# ── Step 2: Activate agent config ────────────────────────────────
if [ ! -f "CLAUDE.md" ]; then
  cp AGENT.md CLAUDE.md
  echo -e "${GREEN}✓${NC} Agent config activated (CLAUDE.md)"
else
  echo -e "${GREEN}✓${NC} Agent config already active"
fi

# ── Step 3: Choose install mode ──────────────────────────────────
echo ""
echo -e "${BOLD}What would you like to install?${NC}"
echo ""
echo "  1) Telegram bot only"
echo "     Chat with the co-pilot via Telegram"
echo ""
echo "  2) Web portal only"
echo "     Full web UI with project management, document viewer, audit log"
echo ""
echo "  3) Web portal + Telegram bot"
echo "     Both — recommended for teams"
echo ""
read -p "Enter option [1/2/3]: " OPTION

# ── Functions ────────────────────────────────────────────────────

install_telegram() {
  echo ""
  echo -e "${BOLD}Setting up Telegram bot...${NC}"
  echo ""

  # Check Docker
  if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is required. Install from https://www.docker.com/get-started${NC}"
    exit 1
  fi

  # Create .env if not exists
  if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}! Created .env from .env.example${NC}"
    echo ""
    echo "  Edit .env and fill in:"
    echo "  - ANTHROPIC_API_KEY (get from console.anthropic.com)"
    echo "  - TELEGRAM_BOT_TOKEN (get from @BotFather on Telegram)"
    echo "  - ALLOWED_CHAT_IDS (your Telegram chat ID from @userinfobot)"
    echo ""
    read -p "Press Enter after filling in .env..."
  fi

  # Build and start bot
  docker compose -f bot/docker-compose.yml up -d --build
  echo ""
  echo -e "${GREEN}✓ Telegram bot is running!${NC}"
  echo ""
  echo "  Open Telegram → find your bot → /start"
  echo ""
  echo "  Manage: make start / make stop / make logs"
}

install_web() {
  echo ""
  echo -e "${BOLD}Setting up Web Portal...${NC}"
  echo ""

  if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is required. Install from https://www.docker.com/get-started${NC}"
    exit 1
  fi

  if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}! Created .env from .env.example${NC}"
    echo ""
    echo "  Edit .env and fill in:"
    echo "  - ANTHROPIC_API_KEY (recommended)"
    echo "  OR configure from the web portal Settings page after startup"
    echo ""
    read -p "Press Enter to continue..."
  fi

  cd apps
  docker compose up -d --build
  cd ..


  # Copy example project if my-projects/ is empty
  if [ -d "my-projects" ] && [ -z "$(ls -A my-projects 2>/dev/null)" ]; then
    echo "Copying example project to my-projects/..."
    cp -r examples/aipm-skills-project my-projects/PROJ-001-aipm-skills
    echo -e "${GREEN}✓${NC} Example project added: my-projects/PROJ-001-aipm-skills"
  elif [ ! -d "my-projects" ]; then
    mkdir -p my-projects
    cp -r examples/aipm-skills-project my-projects/PROJ-001-aipm-skills
    echo -e "${GREEN}✓${NC} Example project added: my-projects/PROJ-001-aipm-skills"
  fi

  echo ""
  echo -e "${GREEN}✓ Web portal is running!${NC}"
  echo ""
  echo -e "  ${BOLD}Open:${NC} http://localhost:80"
  echo ""
  echo "  Pages:"
  echo "    /chat      Chat with the co-pilot"
  echo "    /projects  Manage your projects"
  echo "    /audit     Document change timeline"
  echo "    /settings  Configure API keys"
  echo ""
  echo "  Manage: cd apps && make start / make stop / make logs"
}

install_both() {
  echo ""
  echo -e "${BOLD}Setting up Web Portal + Telegram bot...${NC}"
  echo ""

  if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is required. Install from https://www.docker.com/get-started${NC}"
    exit 1
  fi

  if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}! Created .env from .env.example${NC}"
    echo ""
    echo "  Edit .env and fill in:"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - TELEGRAM_BOT_TOKEN"
    echo "  - ALLOWED_CHAT_IDS"
    echo ""
    read -p "Press Enter after filling in .env..."
  fi

  # Start web portal
  echo "Starting web portal..."
  cd apps
  docker compose up -d --build
  cd ..

  # Start Telegram bot
  echo "Starting Telegram bot..."
  docker compose -f bot/docker-compose.yml up -d --build

  echo ""
  echo -e "${GREEN}✓ Everything is running!${NC}"
  echo ""
  echo -e "  Web portal: ${BOLD}http://localhost:80${NC}"
  echo "  Telegram:   Open Telegram → find your bot → /start"
  echo ""
  echo "  Both share the same workspace — changes sync automatically."
  echo ""
  echo "  Manage web:      cd apps && make start/stop/logs"
  echo "  Manage Telegram: make start/stop/logs  (from root folder)"
}

# ── Run ──────────────────────────────────────────────────────────
case $OPTION in
  1) install_telegram ;;
  2) install_web ;;
  3) install_both ;;
  *) echo -e "${RED}Invalid option. Please enter 1, 2, or 3.${NC}"; exit 1 ;;
esac
