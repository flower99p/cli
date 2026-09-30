from __future__ import annotations

from bot.api_client import TelegramAPIClient
from bot.config import TELEGRAM_BOT_TOKEN
from bot.telegram_bot import build_application, main
from bot.user_session import SessionManager, UserSession, session_manager

__version__ = "1.0.0"
__author__ = "purplemashu"
__email__ = "contact@mashu.lol"

__all__ = [
    "TELEGRAM_BOT_TOKEN",
    "TelegramAPIClient",
    "SessionManager",
    "UserSession",
    "session_manager",
    "build_application",
    "main",
]
