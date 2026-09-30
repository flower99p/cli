from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.api_client import TelegramAPIClient
from bot.config import TELEGRAM_BOT_TOKEN
from bot.user_session import session_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def _send_or_edit(update: Update, text: str, reply_markup=None) -> None:
    query = getattr(update, "callback_query", None)
    if query is not None:
        await query.edit_message_text(text, reply_markup=reply_markup)
        return
    await update.message.reply_text(text, reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = session_manager.get_or_create(update.effective_chat.id)
    session.state = "idle"

    keyboard = [
        [InlineKeyboardButton("Status", callback_data="status"), InlineKeyboardButton("Saldo", callback_data="balance")],
        [InlineKeyboardButton("Login", callback_data="login"), InlineKeyboardButton("Akun", callback_data="accounts")],
        [InlineKeyboardButton("Bantuan", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "Halo! Saya adalah bot Telegram untuk MYnyak CLI.\n\n"
        "Pilih menu di bawah atau gunakan command berikut:\n"
        "/status - status akun\n"
        "/balance - cek saldo\n"
        "/packages FAMILY_CODE - lihat paket\n"
        "/buy FAMILY_CODE VARIANT_CODE ORDER - ringkasan paket\n"
    )
    await start_or_reply(update, text, reply_markup)


async def start_or_reply(update: Update, text: str, reply_markup=None) -> None:
    query = getattr(update, "callback_query", None)
    if query is not None:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Panduan bot:\n\n"
        "/start - menu utama\n"
        "/status - status akun aktif\n"
        "/balance - saldo akun\n"
        "/login - login via OTP\n"
        "/accounts - daftar akun tersimpan\n"
        "/packages FAMILY_CODE - list paket\n"
        "/buy FAMILY_CODE VARIANT_CODE ORDER - ringkasan & pembelian\n"
        "/cancel - batalkan sesi login\n"
        "/help - bantuan\n"
    )
    await _send_or_edit(update, text)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "status":
        await status_command(update, context)
    elif query.data == "balance":
        await balance_command(update, context)
    elif query.data == "login":
        await login_command(update, context)
    elif query.data == "accounts":
        await accounts_command(update, context)
    elif query.data == "help":
        await help_command(update, context)


async def accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    accounts = TelegramAPIClient.get_saved_accounts()
    if not accounts:
        text = "Belum ada akun yang tersimpan di CLI."
    else:
        text = "Akun tersimpan:\n" + "\n".join(f"• {account}" for account in accounts)
    await _send_or_edit(update, text)


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = session_manager.get_or_create(update.effective_chat.id)
    session.state = "waiting_phone"
    session.data = {}
    text = "Silakan kirim nomor HP untuk login.\nFormat: 6281234567890"
    await _send_or_edit(update, text)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = session_manager.get_or_create(update.effective_chat.id)
    session.state = "idle"
    session.data = {}
    await _send_or_edit(update, "Proses login dibatalkan.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    status = TelegramAPIClient.get_status()
    if not status.get("ok"):
        text = f"Status tidak tersedia: {status.get('message', 'Unknown')}"
    else:
        profile = status.get("profile", {})
        text = (
            "Status akun aktif:\n"
            f"Nomor: {status.get('number')}\n"
            f"Subscriber ID: {status.get('subscriber_id')}\n"
            f"Tipe langganan: {status.get('subscription_type')}\n"
            f"Saldo: {status.get('balance')}\n"
        )
        if profile and profile.get("profile", {}).get("name"):
            text += f"Nama profil: {profile['profile']['name']}"

    await _send_or_edit(update, text)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    balance = TelegramAPIClient.get_balance()
    if not balance.get("ok"):
        text = f"Saldo tidak tersedia: {balance.get('message', 'Unknown')}"
    else:
        payload = balance.get("data")
        if isinstance(payload, dict):
            text = "Saldo saat ini:\n" + "\n".join(f"{key}: {value}" for key, value in payload.items())
        else:
            text = f"Saldo saat ini:\n{payload}"
    await _send_or_edit(update, text)


async def packages_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await _send_or_edit(update, "Format: /packages FAMILY_CODE\nContoh: /packages MYFAMILY")
        return

    family_code = args[0].strip()
    result = TelegramAPIClient.get_package_options(family_code)
    if not result.get("ok"):
        await _send_or_edit(update, f"Gagal: {result.get('message', 'Tidak dapat mengambil data family.')}")
        return

    family = result["data"]["family"]
    options = result["data"]["options"]
    if not options:
        await _send_or_edit(update, f"Family {family_code} tidak memiliki opsi paket yang tersedia.")
        return

    lines = [f"Family: {family.get('name', family_code)}", "Paket tersedia:"]
    for index, option in enumerate(options[:10], start=1):
        lines.append(
            f"{index}. {option['variant_name']} | {option['option_name']} | Rp {option['price']:,} | order={option['order']}"
        )
    if len(options) > 10:
        lines.append(f"... dan {len(options)-10} opsi lainnya")
    await _send_or_edit(update, "\n".join(lines))


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await _send_or_edit(update, "Format: /buy FAMILY_CODE VARIANT_CODE ORDER\nContoh: /buy MYFAMILY VAR001 1")
        return

    family_code = args[0].strip()
    variant_code = args[1].strip()
    try:
        option_order = int(args[2].strip())
    except ValueError:
        await _send_or_edit(update, "ORDER harus berupa angka bulat.")
        return

    result = TelegramAPIClient.get_offer_summary(family_code, variant_code, option_order)
    if not result.get("ok"):
        await _send_or_edit(update, f"Gagal: {result.get('message', 'Tidak dapat menghasilkan ringkasan paket.')}")
        return

    offer = result["data"]
    benefits = "\n".join(f"• {item}" for item in offer.get("benefits", [])) or "Tidak ada detail benefit"
    text = (
        "Ringkasan paket:\n"
        f"Nama: {offer['package_name']}\n"
        f"Harga: Rp {offer['price']:,}\n"
        f"Masa aktif: {offer['validity']}\n"
        f"Plan type: {offer['plan_type']}\n"
        f"Payment For: {offer['payment_for']}\n\n"
        f"Benefit:\n{benefits}\n\n"
        "Pilih tombol di bawah untuk membeli dengan saldo."
    )

    keyboard = [[InlineKeyboardButton("✅ Beli dengan Pulsa", callback_data=f"confirm_buy|{family_code}|{variant_code}|{option_order}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await _send_or_edit(update, text, reply_markup)


async def confirm_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("Memproses pembelian...")
    data = query.data or ""
    if not data.startswith("confirm_buy|"):
        await query.edit_message_text("Pembelian dibatalkan.")
        return

    _, family_code, variant_code, order_raw = data.split("|", 3)
    try:
        order_int = int(order_raw)
    except ValueError:
        await query.edit_message_text("Order tidak valid.")
        return

    result = TelegramAPIClient.purchase_with_balance(family_code, variant_code, order_int)
    if result.get("ok"):
        await query.edit_message_text(f"Pembelian berhasil.\n{result.get('message', 'Sukses')}")
    else:
        await query.edit_message_text(f"Pembelian gagal.\n{result.get('message', 'Unknown error')}")


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
            session.state = "idle"
            session.data = {}
            await update.message.reply_text(f"{result.get('message', 'Gagal memulai login.')}")
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

    await update.message.reply_text("Perintah tidak dikenali. Ketik /help untuk melihat daftar perintah yang tersedia.")


def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN belum diatur. Isi variabel environment atau file .env terlebih dahulu.")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("accounts", accounts_command))
    application.add_handler(CommandHandler("packages", packages_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^(status|balance|login|accounts|help)$"))
    application.add_handler(CallbackQueryHandler(confirm_buy_callback, pattern="^confirm_buy"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


def main() -> None:
    application = build_application()
    logger.info("Bot Telegram sedang berjalan...")
    application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
