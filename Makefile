COMPOSE = docker compose -f bot/docker-compose.yml

.DEFAULT_GOAL := help

help:
	@echo ""
	@echo "  PM Bot Commands"
	@echo "  ---------------"
	@echo "  make start    Start the Telegram bot"
	@echo "  make stop     Stop the bot"
	@echo "  make restart  Restart the bot"
	@echo "  make logs     See what the bot is doing"
	@echo "  make status   Check if the bot is running"
	@echo "  make update   Rebuild and restart after changes"
	@echo ""

start:
	$(COMPOSE) up -d --build
	@echo "Bot is running. Open Telegram and send /start to your bot."

stop:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart pm-bot

logs:
	$(COMPOSE) logs -f pm-bot

status:
	$(COMPOSE) ps

update:
	$(COMPOSE) down
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d
	@echo "Update complete."

.PHONY: help start stop restart logs status update
