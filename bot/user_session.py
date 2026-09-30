from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserSession:
    chat_id: int
    state: str = "idle"
    data: dict[str, Any] = field(default_factory=dict)


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[int, UserSession] = {}

    def get_or_create(self, chat_id: int) -> UserSession:
        session = self._sessions.get(chat_id)
        if session is None:
            session = UserSession(chat_id=chat_id)
            self._sessions[chat_id] = session
        return session

    def get(self, chat_id: int) -> UserSession | None:
        return self._sessions.get(chat_id)

    def clear(self, chat_id: int) -> None:
        self._sessions.pop(chat_id, None)

    def set_state(self, chat_id: int, state: str) -> UserSession:
        session = self.get_or_create(chat_id)
        session.state = state
        return session


session_manager = SessionManager()

__all__ = ["UserSession", "SessionManager", "session_manager"]
