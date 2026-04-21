import os

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Claude API
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "").strip().strip('"').strip("'")

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

# Validación al arrancar
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN no configurado en Railway")
if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY no configurado en Railway")
