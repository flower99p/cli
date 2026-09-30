from __future__ import annotations

from typing import Any


def _load_auth_instance():
    from app.service.auth import AuthInstance

    return AuthInstance


def _load_engsel_helpers():
    from app.client.engsel import get_balance, get_profile, get_tiering_info

    return get_balance, get_profile, get_tiering_info


def _load_ciam_helpers():
    from app.client.ciam import get_otp, submit_otp

    return get_otp, submit_otp


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

    @staticmethod
    def get_saved_accounts() -> list[int]:
        auth = _load_auth_instance()
        auth.load_tokens()
        return [int(item["number"]) for item in getattr(auth, "refresh_tokens", [])]

    @staticmethod
    def request_login(phone_number: str) -> dict[str, Any]:
        cleaned = (phone_number or "").strip()
        if not cleaned.startswith("628") or len(cleaned) < 10 or len(cleaned) > 14:
            return {"ok": False, "message": "Nomor tidak valid. Format yang benar: 6281234567890"}

        get_otp_fn, _ = _load_ciam_helpers()
        try:
            subscriber_id = get_otp_fn(cleaned)
            if not subscriber_id:
                return {"ok": False, "message": "Gagal mengirim OTP. Silakan cek nomor Anda."}
            return {
                "ok": True,
                "phone_number": cleaned,
                "subscriber_id": subscriber_id,
                "message": "OTP telah dikirim. Kirim kode OTP 6 digit yang diterima via SMS.",
            }
        except Exception as exc:
            return {"ok": False, "message": f"Gagal mengirim OTP: {exc}"}

    @staticmethod
    def verify_login(phone_number: str, otp_code: str) -> dict[str, Any]:
        cleaned_phone = (phone_number or "").strip()
        cleaned_otp = (otp_code or "").strip()

        if not cleaned_phone.startswith("628") or len(cleaned_phone) < 10 or len(cleaned_phone) > 14:
            return {"ok": False, "message": "Nomor tidak valid."}
        if len(cleaned_otp) != 6 or not cleaned_otp.isdigit():
            return {"ok": False, "message": "OTP harus 6 digit angka."}

        auth = _load_auth_instance()
        _, submit_otp_fn = _load_ciam_helpers()

        try:
            tokens = submit_otp_fn(auth.api_key, "SMS", cleaned_phone, cleaned_otp)
            if not tokens:
                return {"ok": False, "message": "OTP salah atau sudah kadaluarsa. Silakan ulang login."}

            auth.add_refresh_token(int(cleaned_phone), tokens["refresh_token"])
            auth.set_active_user(int(cleaned_phone))

            return {
                "ok": True,
                "message": "Login berhasil. Akun sudah tersimpan dan aktif.",
                "number": int(cleaned_phone),
                "refresh_token": tokens.get("refresh_token"),
            }
        except Exception as exc:
            return {"ok": False, "message": f"Gagal memverifikasi OTP: {exc}"}


__all__ = ["TelegramAPIClient"]
