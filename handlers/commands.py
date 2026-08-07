from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.session import session_manager
from utils.cleanup import cleanup_session_files

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>📖 How to use Photo Collage Grid Bot:</b>\n\n"
        "1️⃣ Click <b>Create Collage</b> or type /start.\n"
        "2️⃣ Send your photos directly to the chat.\n"
        "3️⃣ Customize your Grid (2x2, 3x3, 4x4), Spacing, Background, and Quality.\n"
        "4️⃣ Click <b>🖼 Generate Collage</b> to combine your images into one grid!\n\n"
        "<b>Commands:</b>\n"
        "/start - Welcome screen\n"
        "/help - Instructions\n"
        "/cancel - Abort current collage process\n"
        "/about - Information about this bot"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>ℹ️ About @photocollgripbot</b>\n\n"
        "A fast, privacy-friendly Telegram bot designed to combine multiple photos "
        "into stunning grid collages instantly.\n\n"
        "• <b>Privacy:</b> Photos are processed temporarily and immediately discarded.\n"
        "• <b>Engine:</b> Python 3.11+, Pillow & python-telegram-bot."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    session = session_manager.get_session(user_id)
    cleanup_session_files(session)
    session_manager.clear_session(user_id)

    keyboard = [[InlineKeyboardButton("🚀 Start New Collage", callback_data="cmd_start_collage")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "❌ Current collage session has been cancelled and temporary photos deleted.",
            reply_markup=reply_markup
        )
