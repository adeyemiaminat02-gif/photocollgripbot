from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.session import session_manager
from utils.cleanup import cleanup_session_files

def get_start_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🖼 Create Collage", callback_data="cmd_start_collage")],
        [InlineKeyboardButton("📖 Help", callback_data="cmd_help"), InlineKeyboardButton("ℹ️ About", callback_data="cmd_about")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    session = session_manager.get_session(user_id)
    cleanup_session_files(session)
    session.state = "IDLE"

    first_name = update.effective_user.first_name if update.effective_user else "there"
    welcome_text = (
        f"👋 Welcome, <b>{first_name}</b>!\n\n"
        "I can help you build clean, high-resolution grid collages from your photos.\n\n"
        "Tap <b>Create Collage</b> below to begin uploading your images!"
    )

    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_start_keyboard(),
            parse_mode="HTML"
        )

async def start_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "cmd_start_collage":
        session = session_manager.get_session(user_id)
        cleanup_session_files(session)
        session.state = "COLLECTING"

        text = (
            "📸 <b>Send me your photos!</b>\n\n"
            "Upload photos one by one or as a batch. When finished, select an action below."
        )
        keyboard = [
            [InlineKeyboardButton("⚙️ Settings & Layout", callback_data="cmd_settings")],
            [InlineKeyboardButton("🖼 Create Collage", callback_data="cmd_generate")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cmd_cancel")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "cmd_help":
        from handlers.commands import help_command
        await help_command(update, context)

    elif data == "cmd_about":
        from handlers.commands import about_command
        await about_command(update, context)

    elif data == "cmd_cancel":
        session = session_manager.get_session(user_id)
        cleanup_session_files(session)
        session_manager.clear_session(user_id)
        await query.edit_message_text("❌ Session cancelled. Temporary files deleted.")
