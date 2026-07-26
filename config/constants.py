"""
Constants - Application-wide constants and default values.

Centralized location for magic numbers, default strings, and
other constants used across the application.
"""

# ── Application Metadata ──────────────────────────────────────────────
APP_NAME = "Pinterest AI Agent"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Autonomous AI agent for Pinterest automation powered by local LLM"

# ── Pinterest URLs ─────────────────────────────────────────────────────
PINTEREST_BASE_URL = "https://www.pinterest.com"
PINTEREST_LOGIN_URL = "https://www.pinterest.com/login/"
PINTEREST_SEARCH_URL = "https://www.pinterest.com/search/pins/?q={query}"
PINTEREST_PROFILE_URL = "https://www.pinterest.com/{username}/"

# ── Rate Limiting ──────────────────────────────────────────────────────
MIN_ACTION_DELAY_SECONDS = 1.0
MAX_ACTION_DELAY_SECONDS = 5.0
MAX_REQUESTS_PER_MINUTE = 30

# ── File Extensions ────────────────────────────────────────────────────
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# ── Database ───────────────────────────────────────────────────────────
DB_FILENAME = "pinterest_agent.db"
MAX_CONVERSATION_HISTORY = 100
MAX_MEMORY_ENTRIES = 10000

# ── LLM ────────────────────────────────────────────────────────────────
DEFAULT_CONTEXT_WINDOW = 8192
MAX_RETRIES_ON_PARSE_FAILURE = 3
