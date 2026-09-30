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
        "• /help - Bantuan\n"
        "• /login - Simpan nomor yang akan diproses di CLI\n\n"
        "Catatan: bot ini memanfaatkan data auth yang sudah ada pada aplikasi CLI."
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Panduan bot:\n\n"
        "/start - Tampilkan menu\n"
        "/status - Status pengguna aktif\n"
        "/balance - Saldo saat ini\n"
        "/login - Menyimpan nomor tujuan login\n"
        "/help - Bantuan\n"
    )
    await update.message.reply_text(text)


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = session_manager.get_or_create(update.effective_chat.id)
    session.state = "waiting_phone"
    session.data = {}
    await update.message.reply_text(
        "Silakan kirim nomor HP yang akan dipakai untuk login.\n"
        "Contoh: 6281234567890"
    )


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
        message += f"Nama profil: {profile.get('profile', {}).get('name', 'N/A')}"

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

    if session and session.state == "waiting_phone":
        phone = update.message.text.strip()
        session.state = "idle"
        session.data["phone_number"] = phone
        await update.message.reply_text(
            f"Nomor yang disimpan: {phone}\n\n"
            "Gunakan data ini di aplikasi CLI untuk melanjutkan proses login atau autentikasi."
        )
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


def main() -> None:
    application = build_application()
    logger.info("Bot Telegram is starting...")
    application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
