from __future__ import annotations

from typing import Any


def _load_auth_instance():
    from app.service.auth import AuthInstance

    return AuthInstance


def _load_engsel_helpers():
    from app.client.engsel import (
        get_active_packages,
        get_balance,
        get_family,
        get_package_details,
        get_profile,
        get_tiering_info,
    )

    return {
        "get_active_packages": get_active_packages,
        "get_balance": get_balance,
        "get_family": get_family,
        "get_package_details": get_package_details,
        "get_profile": get_profile,
        "get_tiering_info": get_tiering_info,
    }


def _load_ciam_helpers():
    from app.client.ciam import get_otp, submit_otp

    return get_otp, submit_otp


def _load_purchase_helpers():
    from app.client.purchase.balance import settlement_balance

    return settlement_balance


class TelegramAPIClient:
    @staticmethod
    def get_active_user() -> dict[str, Any] | None:
        auth = _load_auth_instance()
        return auth.get_active_user() if hasattr(auth, "get_active_user") else None

    @staticmethod
    def get_saved_accounts() -> list[int]:
        auth = _load_auth_instance()
        auth.load_tokens()
        return [int(item["number"]) for item in getattr(auth, "refresh_tokens", [])]

    @staticmethod
    def get_status() -> dict[str, Any]:
        auth = _load_auth_instance()
        user = auth.get_active_user()
        if user is None:
            return {
                "ok": False,
                "message": "Belum ada pengguna aktif di CLI. Jalankan proses login di aplikasi CLI terlebih dahulu.",
            }

        helpers = _load_engsel_helpers()

        try:
            balance = helpers["get_balance"](auth.api_key, user["tokens"]["id_token"])
            profile = helpers["get_profile"](auth.api_key, user["tokens"]["access_token"], user["tokens"]["id_token"])

            result = {
                "ok": True,
                "number": user.get("number"),
                "subscriber_id": user.get("subscriber_id"),
                "subscription_type": user.get("subscription_type"),
                "balance": balance,
                "profile": profile,
            }

            if user.get("subscription_type") == "PREPAID":
                result["tiering"] = helpers["get_tiering_info"](auth.api_key, user["tokens"])

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
        try:
            balance = _load_engsel_helpers()["get_balance"](auth.api_key, user["tokens"]["id_token"])
            return {"ok": True, "data": balance}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    @staticmethod
    def get_active_packages() -> dict[str, Any]:
        user = TelegramAPIClient.get_active_user()
        if user is None:
            return {"ok": False, "message": "Belum ada pengguna aktif."}

        auth = _load_auth_instance()
        try:
            packages = _load_engsel_helpers()["get_active_packages"](auth.api_key, user["tokens"])
            if not packages:
                return {"ok": True, "data": []}
            return {"ok": True, "data": packages}
        except Exception as exc:
            return {"ok": False, "message": f"Gagal mengambil paket aktif: {exc}"}

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

    @staticmethod
    def get_package_family(family_code: str) -> dict[str, Any]:
        auth = _load_auth_instance()
        user = auth.get_active_user()
        if user is None:
            return {"ok": False, "message": "Belum ada pengguna aktif."}

        try:
            family_data = _load_engsel_helpers()["get_family"](auth.api_key, user["tokens"], family_code)
            if not family_data:
                return {"ok": False, "message": f"Tidak bisa mengambil data family {family_code}."}
            return {"ok": True, "data": family_data}
        except Exception as exc:
            return {"ok": False, "message": f"Gagal mengambil data family: {exc}"}

    @staticmethod
    def get_package_options(family_code: str) -> dict[str, Any]:
        family_result = TelegramAPIClient.get_package_family(family_code)
        if not family_result.get("ok"):
            return family_result

        family_data = family_result["data"]
        variants = family_data.get("package_variants", [])
        flattened: list[dict[str, Any]] = []

        for variant in variants:
            variant_name = variant.get("name", "Unnamed")
            for option in variant.get("package_options", []):
                flattened.append(
                    {
                        "variant_name": variant_name,
                        "variant_code": variant.get("package_variant_code", ""),
                        "option_name": option.get("name", ""),
                        "option_code": option.get("package_option_code", ""),
                        "price": option.get("price", 0),
                        "order": option.get("order", 0),
                    }
                )

        return {"ok": True, "data": {"family": family_data.get("package_family", {}), "options": flattened}}

    @staticmethod
    def get_offer_summary(family_code: str, variant_code: str, option_order: int) -> dict[str, Any]:
        auth = _load_auth_instance()
        user = auth.get_active_user()
        if user is None:
            return {"ok": False, "message": "Belum ada pengguna aktif."}

        try:
            details = _load_engsel_helpers()["get_package_details"](
                auth.api_key,
                user["tokens"],
                family_code,
                variant_code,
                int(option_order),
            )
            if not details:
                return {"ok": False, "message": "Gagal membentuk ringkasan paket."}

            option = details.get("package_option", {})
            family = details.get("package_family", {})
            variant = details.get("package_detail_variant", {})

            benefits: list[str] = []
            for benefit in option.get("benefits", []):
                name = benefit.get("name", "Unknown")
                data_type = benefit.get("data_type", "")
                total = benefit.get("total", 0)
                if data_type == "DATA" and total > 0:
                    benefits.append(f"{name}: {total / (1024 ** 3):.2f} GB")
                elif data_type == "VOICE" and total > 0:
                    benefits.append(f"{name}: {total / 60:.2f} menit")
                elif data_type == "TEXT" and total > 0:
                    benefits.append(f"{name}: {total} SMS")
                else:
                    benefits.append(f"{name}: {total} {data_type}")

            return {
                "ok": True,
                "data": {
                    "package_name": f"{family.get('name', '')} - {variant.get('name', '')} - {option.get('name', '')}".strip(),
                    "price": option.get("price", 0),
                    "validity": option.get("validity", "N/A"),
                    "payment_for": family.get("payment_for", "BUY_PACKAGE"),
                    "family_code": family.get("package_family_code", family_code),
                    "option_code": option.get("package_option_code", ""),
                    "token_confirmation": details.get("token_confirmation", ""),
                    "benefits": benefits,
                    "points": option.get("point", 0),
                    "plan_type": family.get("plan_type", "N/A"),
                },
            }
        except Exception as exc:
            return {"ok": False, "message": f"Gagal mengambil detail paket: {exc}"}

    @staticmethod
    def purchase_with_balance(family_code: str, variant_code: str, option_order: int) -> dict[str, Any]:
        auth = _load_auth_instance()
        user = auth.get_active_user()
        if user is None:
            return {"ok": False, "message": "Belum ada pengguna aktif."}

        try:
            details = _load_engsel_helpers()["get_package_details"](
                auth.api_key,
                user["tokens"],
                family_code,
                variant_code,
                int(option_order),
            )
            if not details:
                return {"ok": False, "message": "Gagal mengambil detail paket."}

            option = details.get("package_option", {})
            family = details.get("package_family", {})
            variant = details.get("package_detail_variant", {})

            from app.type_dict import PaymentItem

            payment_item = PaymentItem(
                item_code=option.get("package_option_code", ""),
                product_type="",
                item_price=option.get("price", 0),
                item_name=f"{variant.get('name', '')} {option.get('name', '')}".strip(),
                tax=0,
                token_confirmation=details.get("token_confirmation", ""),
            )

            settlement_fn = _load_purchase_helpers()
            result = settlement_fn(
                auth.api_key,
                user["tokens"],
                [payment_item],
                family.get("payment_for", "BUY_PACKAGE"),
                ask_overwrite=False,
                overwrite_amount=option.get("price", 0),
            )

            if result and result.get("status") == "SUCCESS":
                return {
                    "ok": True,
                    "message": "Pembelian berhasil! Silakan cek aplikasi MyXL untuk detail.",
                    "data": result,
                }

            error_msg = result.get("message", "Pembelian gagal") if isinstance(result, dict) else str(result)
            return {"ok": False, "message": f"Pembelian gagal: {error_msg}"}
        except Exception as exc:
            return {"ok": False, "message": f"Gagal melakukan pembelian: {exc}"}


__all__ = ["TelegramAPIClient"]
