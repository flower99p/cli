from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

for env_path in [ROOT / ".env", ROOT / "bot" / ".env"]:
    if env_path.exists():
        load_dotenv(env_path, override=False)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_API_URL = os.getenv("BASE_API_URL", "")
BASE_CIAM_URL = os.getenv("BASE_CIAM_URL", "")
BASIC_AUTH = os.getenv("BASIC_AUTH", "")
API_KEY = os.getenv("API_KEY", "")
ENCRYPTED_FIELD_KEY = os.getenv("ENCRYPTED_FIELD_KEY", "")
XDATA_KEY = os.getenv("XDATA_KEY", "")
AX_API_SIG_KEY = os.getenv("AX_API_SIG_KEY", "")
X_API_BASE_SECRET = os.getenv("X_API_BASE_SECRET", "")
CIRCLE_MSISDN_KEY = os.getenv("CIRCLE_MSISDN_KEY", "")
UA = os.getenv("UA", "")


def has_required_env() -> bool:
    required = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "API_KEY": API_KEY,
        "BASE_API_URL": BASE_API_URL,
        "BASE_CIAM_URL": BASE_CIAM_URL,
    }
    return all(value for value in required.values())


def get_missing_env() -> list[str]:
    required = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "API_KEY": API_KEY,
        "BASE_API_URL": BASE_API_URL,
        "BASE_CIAM_URL": BASE_CIAM_URL,
    }
    return [name for name, value in required.items() if not value]


__all__ = [
    "TELEGRAM_BOT_TOKEN",
    "BASE_API_URL",
    "BASE_CIAM_URL",
    "BASIC_AUTH",
    "API_KEY",
    "ENCRYPTED_FIELD_KEY",
    "XDATA_KEY",
    "AX_API_SIG_KEY",
    "X_API_BASE_SECRET",
    "CIRCLE_MSISDN_KEY",
    "UA",
    "has_required_env",
    "get_missing_env",
]
