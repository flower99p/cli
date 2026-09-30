from __future__ import annotations

import logging
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters

from bot.api_client import TelegramAPIClient
from bot.config import TELEGRAM_BOT_TOKEN
from bot.user_session import session_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = session_manager.get_or_create(chat_id)
    session.state = "idle"

    keyboard = [
        [InlineKeyboardButton("Status Akun", callback_data="status"), InlineKeyboardButton("Saldo", callback_data="balance")],
        [InlineKeyboardButton("Login", callback_data="login"), InlineKeyboardButton("Akun Tersimpan", callback_data="accounts")],
        [InlineKeyboardButton("Bantuan", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "Halo! 👋 Saya adalah bot Telegram untuk MYnyak CLI.\n\n"
        "Pilih menu di bawah atau gunakan perintah:\n"
        "/status - Cek status akun\n"
        "/balance - Cek saldo\n"
        "/packages FAMILY_CODE - Lihat paket\n"
        "/buy FAMILY_CODE VARIANT_CODE ORDER - Beli paket\n"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Perintah yang tersedia:\n\n"
        "/start - Menu utama\n"
        "/status - Status pengguna aktif\n"
        "/balance - Saldo saat ini\n"
        "/login - Login akun baru via OTP\n"
        "/accounts - Daftar akun yang tersimpan\n"
        "/packages FAMILY_CODE - Tampilkan daftar paket\n"
        "/buy FAMILY_CODE VARIANT_CODE ORDER - Ringkasan & beli paket\n"
        "/cancel - Batalkan proses login\n"
        "/help - Bantuan ini\n\n"
        "Contoh:\n"
        "/packages UNLIMITED_TURBO\n"
        "/buy UNLIMITED_TURBO VARIANT001 1"
    )
    await update.message.reply_text(text)


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
        text = "❌ Belum ada akun yang tersimpan di CLI."
    else:
        text = "✅ Akun tersimpan:\n" + "\n".join(f"📱 {account}" for account in accounts)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = session_manager.get_or_create(update.effective_chat.id)
    session.state = "waiting_phone"
    session.data = {}
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "📞 Silakan kirim nomor HP untuk login.\nFormat: 6281234567890"
        )
    else:
        await update.message.reply_text(
            "📞 Silakan kirim nomor HP untuk login.\nFormat: 6281234567890"
        )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = session_manager.get_or_create(update.effective_chat.id)
    session.state = "idle"
    session.data = {}
    await update.message.reply_text("❌ Proses login dibatalkan.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    status = TelegramAPIClient.get_status()
    if not status.get("ok"):
        text = f"❌ {status.get('message', 'Status tidak tersedia.')}"
    else:
        profile = status.get("profile", {})
        text = (
            "✅ Status akun aktif:\n"
            f"📱 Nomor: {status.get('number')}\n"
            f"🆔 Subscriber ID: {status.get('subscriber_id')}\n"
            f"📋 Tipe: {status.get('subscription_type')}\n"
            f"💰 Saldo: {status.get('balance')}\n"
        )

        if profile:
            profile_name = profile.get("profile", {}).get("name")
            if profile_name:
                text += f"👤 Nama: {profile_name}"

    if update.callback_query:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    balance = TelegramAPIClient.get_balance()
    if not balance.get("ok"):
        text = f"❌ {balance.get('message', 'Saldo tidak tersedia.')}"
    else:
        payload = balance.get("data")
        if isinstance(payload, dict):
            items = [f"• {key}: {value}" for key, value in payload.items()]
            text = "💰 Saldo saat ini:\n" + "\n".join(items)
        else:
            text = f"💰 Saldo saat ini:\n{payload}"

    if update.callback_query:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)


async def packages_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("Format: /packages FAMILY_CODE\nContoh: /packages UNLIMITED_TURBO")
        return

    family_code = args[0].strip()
    result = TelegramAPIClient.get_package_options(family_code)
    if not result.get("ok"):
        await update.message.reply_text(f"❌ {result.get('message', 'Tidak dapat mengambil data family.')}")
        return

    family = result["data"]["family"]
    options = result["data"]["options"]
    if not options:
        await update.message.reply_text(f"❌ Family {family_code} tidak memiliki opsi paket.")
        return

    lines = [
        f"📦 Family: {family.get('name', family_code)}",
        f"Code: {family_code}",
        "\n🎯 Opsi paket:",
    ]
    for idx, option in enumerate(options[:10], start=1):
        lines.append(
            f"\n{idx}. {option['variant_name']}\n"
            f"   {option['option_name']}\n"
            f"   💵 Rp {option['price']:,}\n"
            f"   `/buy {family_code} {option['variant_code']} {option['order']}`"
        )

    if len(options) > 10:
        lines.append(f"\n... dan {len(options)-10} opsi lain")

    await update.message.reply_text("\n".join(lines))


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Format: /buy FAMILY_CODE VARIANT_CODE ORDER\nContoh: /buy UNLIMITED_TURBO VARIANT001 1"
        )
        return

    family_code = args[0].strip()
    variant_code = args[1].strip()
    option_order = args[2].strip()

    try:
        order_int = int(option_order)
    except ValueError:
        await update.message.reply_text("❌ ORDER harus berupa angka bulat.")
        return

    result = TelegramAPIClient.get_offer_summary(family_code, variant_code, order_int)
    if not result.get("ok"):
        await update.message.reply_text(f"❌ {result.get('message', 'Gagal membuat ringkasan paket.')}")
        return

    offer = result["data"]
    benefits_text = "\n".join([f"• {b}" for b in offer.get("benefits", [])]) if offer.get("benefits") else "N/A"
    
    message = (
        "📋 Ringkasan Paket\n"
        "="*40 + "\n"
        f"📦 Nama: {offer['package_name']}\n"
        f"💵 Harga: Rp {offer['price']:,}\n"
        f"⏱️ Masa Aktif: {offer['validity']}\n"
        f"⭐ Poin: {offer['points']}\n"
        f"📋 Tipe Plan: {offer['plan_type']}\n\n"
        f"Manfaat:\n{benefits_text}\n\n"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Beli Sekarang (Pulsa)", callback_data=f"confirm_buy|{family_code}|{variant_code}|{order_int}")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel_buy")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)


async def confirm_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data_parts = query.data.split("|")
    
    if len(data_parts) < 4:
        await query.answer("❌ Data tidak valid", show_alert=True)
        return

    family_code = data_parts[1]
    variant_code = data_parts[2]
    order_int = int(data_parts[3])

    await query.answer("⏳ Memproses pembelian...")
    await query.edit_message_text("⏳ Sedang memproses pembelian, silakan tunggu...")

    result = TelegramAPIClient.purchase_with_balance(family_code, variant_code, order_int)
    if result.get("ok"):
        await query.edit_message_text(
            f"✅ {result.get('message', 'Pembelian berhasil!')}\n\n"
            "Silakan cek aplikasi MyXL untuk melihat detail lengkap."
        )
    else:
        await query.edit_message_text(f"❌ {result.get('message', 'Pembelian gagal.')}")


async def cancel_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Pembelian dibatalkan.")


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
            await update.message.reply_text(f"❌ {result.get('message', 'Gagal memulai login.')}")
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
            await update.message.reply_text(f"❌ {result.get('message', 'OTP gagal diverifikasi.')}")
            return

        session.state = "idle"
        session.data = {}
        await update.message.reply_text(f"✅ {result.get('message', 'Login berhasil.')}")
        return

    await update.message.reply_text(
        "❓ Perintah tidak dikenali. Ketik /help untuk melihat daftar perintah."
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
    application.add_handler(CommandHandler("packages", packages_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^(status|balance|login|accounts|help)$"))
    application.add_handler(CallbackQueryHandler(confirm_buy_callback, pattern="^confirm_buy"))
    application.add_handler(CallbackQueryHandler(cancel_buy_callback, pattern="^cancel_buy"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


def main() -> None:
    application = build_application()
    logger.info("🚀 Bot Telegram is starting...")
    application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
