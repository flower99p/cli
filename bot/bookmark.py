from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BookmarkedPackage:
    family_code: str
    variant_code: str
    option_order: int
    package_name: str
    price: int
    created_at: str = field(default_factory=lambda: "")


class PackageBookmarkManager:
    def __init__(self, filename: str = "bookmarks.json"):
        self.filename = filename
        self.bookmarks: dict[int, list[dict[str, Any]]] = {}
        self.load_bookmarks()

    def load_bookmarks(self) -> None:
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf8") as f:
                    self.bookmarks = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.bookmarks = {}
        else:
            self.bookmarks = {}

    def save_bookmarks(self) -> None:
        with open(self.filename, "w", encoding="utf8") as f:
            json.dump(self.bookmarks, f, indent=4, ensure_ascii=False)

    def add_bookmark(self, chat_id: int, family_code: str, variant_code: str, option_order: int, package_name: str, price: int) -> bool:
        if str(chat_id) not in self.bookmarks:
            self.bookmarks[str(chat_id)] = []

        existing = next(
            (b for b in self.bookmarks[str(chat_id)] if b["family_code"] == family_code and b["variant_code"] == variant_code and b["option_order"] == option_order),
            None,
        )
        if existing:
            return False

        self.bookmarks[str(chat_id)].append(
            {
                "family_code": family_code,
                "variant_code": variant_code,
                "option_order": option_order,
                "package_name": package_name,
                "price": price,
            }
        )
        self.save_bookmarks()
        return True

    def get_bookmarks(self, chat_id: int) -> list[dict[str, Any]]:
        return self.bookmarks.get(str(chat_id), [])

    def remove_bookmark(self, chat_id: int, family_code: str, variant_code: str, option_order: int) -> bool:
        if str(chat_id) not in self.bookmarks:
            return False

        original_len = len(self.bookmarks[str(chat_id)])
        self.bookmarks[str(chat_id)] = [
            b for b in self.bookmarks[str(chat_id)] if not (b["family_code"] == family_code and b["variant_code"] == variant_code and b["option_order"] == option_order)
        ]

        if len(self.bookmarks[str(chat_id)]) < original_len:
            self.save_bookmarks()
            return True
        return False

    def clear_bookmarks(self, chat_id: int) -> bool:
        if str(chat_id) in self.bookmarks:
            del self.bookmarks[str(chat_id)]
            self.save_bookmarks()
            return True
        return False


bookmark_manager = PackageBookmarkManager()

__all__ = ["BookmarkedPackage", "PackageBookmarkManager", "bookmark_manager"]
