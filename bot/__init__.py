from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from bot.api_client import TelegramAPIClient
from bot.config import TELEGRAM_BOT_TOKEN
from bot.user_session import session_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = session_manager.get_or_create(chat_id)
    session.state = "idle"

    text = (
        "Halo! Saya adalah bot Telegram untuk MYnyak CLI.\n\n"
        "Perintah yang tersedia:\n"
        "• /start - Menampilkan menu awal\n"
        "• /status - Cek status akun aktif\n"
        "• /balance - Cek saldo akun\n"
        "• /login - Login akun baru via OTP\n"
        "• /accounts - Lihat akun yang tersimpan\n"
        "• /help - Bantuan\n"
        "• /cancel - Batalkan proses login\n\n"
        "Catatan: bot ini memanfaatkan data auth yang sudah ada pada aplikasi CLI."
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Panduan bot:\n\n"
        "/start - Tampilkan menu\n"
        "/status - Status pengguna aktif\n"
        "/balance - Saldo saat ini\n"
        "/login - Login akun baru via OTP\n"
        "/accounts - Daftar akun yang tersimpan\n"
        "/cancel - Batalkan sesi aktif\n"
        "/help - Bantuan\n"
    )
    await update.message.reply_text(text)


async def accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    accounts = TelegramAPIClient.get_saved_accounts()
    if not accounts:
        await update.message.reply_text("Belum ada akun yang tersimpan di CLI.")
        return

    list_text = "Akun tersimpan:\n" + "\n".join(f"• {account}" for account in accounts)
    await update.message.reply_text(list_text)


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = session_manager.get_or_create(update.effective_chat.id)
    session.state = "waiting_phone"
    session.data = {}
    await update.message.reply_text(
        "Silakan kirim nomor HP untuk login.\n"
        "Format: 6281234567890"
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = session_manager.get_or_create(update.effective_chat.id)
    session.state = "idle"
    session.data = {}
    await update.message.reply_text("Proses login dibatalkan.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    status = TelegramAPIClient.get_status()
    if not status.get("ok"):
        await update.message.reply_text(status.get("message", "Status tidak tersedia."))
        return

    profile = status.get("profile", {})
    message = (
        "Status akun aktif:\n"
        f"Nomor: {status.get('number')}\n"
        f"Subscriber ID: {status.get('subscriber_id')}\n"
        f"Tipe langganan: {status.get('subscription_type')}\n"
        f"Saldo: {status.get('balance')}\n"
    )

    if profile:
        profile_name = profile.get("profile", {}).get("name")
        if profile_name:
            message += f"Nama profil: {profile_name}"

    await update.message.reply_text(message)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    balance = TelegramAPIClient.get_balance()
    if not balance.get("ok"):
        await update.message.reply_text(balance.get("message", "Saldo tidak tersedia."))
        return

    payload = balance.get("data")
    if isinstance(payload, dict):
        msg = "Saldo saat ini:\n" + "\n".join(f"{key}: {value}" for key, value in payload.items())
    else:
        msg = f"Saldo saat ini:\n{payload}"
    await update.message.reply_text(msg)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = session_manager.get(chat_id)

    if not session:
        await update.message.reply_text("Ketik /help untuk melihat daftar perintah yang tersedia.")
        return

    if session.state == "waiting_phone":
        phone = update.message.text.strip()
        result = TelegramAPIClient.request_login(phone)
        if not result.get("ok"):
            await update.message.reply_text(result.get("message", "Gagal memulai login."))
            session.state = "idle"
            session.data = {}
            return

        session.state = "waiting_otp"
        session.data = {"phone_number": result["phone_number"]}
        await update.message.reply_text(result["message"])
        return

    if session.state == "waiting_otp":
        otp = update.message.text.strip()
        result = TelegramAPIClient.verify_login(session.data.get("phone_number", ""), otp)
        if not result.get("ok"):
            await update.message.reply_text(result.get("message", "OTP gagal diverifikasi."))
            return

        session.state = "idle"
        session.data = {}
        await update.message.reply_text(result.get("message", "Login berhasil."))
        return

    await update.message.reply_text(
        "Perintah tidak dikenali. Ketik /help untuk melihat daftar perintah yang tersedia."
    )


def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN belum diatur. Isi variabel environment atau file .env terlebih dahulu."
        )

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("accounts", accounts_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


def main() -> None:
    application = build_application()
    logger.info("Bot Telegram is starting...")
    application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
