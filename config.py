import os

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Claude API
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")
