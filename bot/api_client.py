from __future__ import annotations

from typing import Any


def _load_auth_instance():
    from app.service.auth import AuthInstance

    return AuthInstance


def _load_engsel_helpers():
    from app.client.engsel import get_balance, get_profile, get_tiering_info

    return get_balance, get_profile, get_tiering_info


class TelegramAPIClient:
    @staticmethod
    def get_active_user() -> dict[str, Any] | None:
        auth = _load_auth_instance()
        return auth.get_active_user() if hasattr(auth, "get_active_user") else None

    @staticmethod
    def get_status() -> dict[str, Any]:
        auth = _load_auth_instance()
        user = auth.get_active_user()
        if user is None:
            return {
                "ok": False,
                "message": "Belum ada pengguna aktif di CLI. Jalankan proses login di aplikasi CLI terlebih dahulu.",
            }

        get_balance_fn, get_profile_fn, get_tiering_info_fn = _load_engsel_helpers()

        try:
            balance = get_balance_fn(auth.api_key, user["tokens"]["id_token"])
            profile = get_profile_fn(auth.api_key, user["tokens"]["access_token"], user["tokens"]["id_token"])

            result = {
                "ok": True,
                "number": user.get("number"),
                "subscriber_id": user.get("subscriber_id"),
                "subscription_type": user.get("subscription_type"),
                "balance": balance,
                "profile": profile,
            }

            if user.get("subscription_type") == "PREPAID":
                tiering = get_tiering_info_fn(auth.api_key, user["tokens"])
                result["tiering"] = tiering

            return result
        except Exception as exc:
            return {
                "ok": False,
                "message": f"Gagal mengambil status akun: {exc}",
            }

    @staticmethod
    def get_balance() -> dict[str, Any]:
        user = TelegramAPIClient.get_active_user()
        if user is None:
            return {"ok": False, "message": "Tidak ada user aktif."}

        auth = _load_auth_instance()
        get_balance_fn = _load_engsel_helpers()[0]

        try:
            balance = get_balance_fn(auth.api_key, user["tokens"]["id_token"])
            return {"ok": True, "data": balance}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}


__all__ = ["TelegramAPIClient"]
