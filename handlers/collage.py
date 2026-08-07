import os
import uuid
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import TEMP_DIR, MAX_PHOTOS_PER_SESSION
from utils.session import session_manager
from utils.cleanup import cleanup_session_files, safe_remove_file
from services.collage_generator import create_collage

logger = logging.getLogger(__name__)

def build_settings_keyboard(session) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Grid", callback_data="noop"),
            InlineKeyboardButton(f"{'✅ ' if session.grid_size=='2x2' else ''}2×2", callback_data="set_grid_2x2"),
            InlineKeyboardButton(f"{'✅ ' if session.grid_size=='3x3' else ''}3×3", callback_data="set_grid_3x3"),
            InlineKeyboardButton(f"{'✅ ' if session.grid_size=='4x4' else ''}4×4", callback_data="set_grid_4x4")
        ],
        [
            InlineKeyboardButton("Spacing", callback_data="noop"),
            InlineKeyboardButton(f"{'✅ ' if session.spacing=='Small' else ''}Small", callback_data="set_space_Small"),
            InlineKeyboardButton(f"{'✅ ' if session.spacing=='Medium' else ''}Medium", callback_data="set_space_Medium"),
            InlineKeyboardButton(f"{'✅ ' if session.spacing=='Large' else ''}Large", callback_data="set_space_Large")
        ],
        [
            InlineKeyboardButton("Background", callback_data="noop"),
            InlineKeyboardButton(f"{'✅ ' if session.bg_color=='White' else ''}White", callback_data="set_bg_White"),
            InlineKeyboardButton(f"{'✅ ' if session.bg_color=='Black' else ''}Black", callback_data="set_bg_Black")
        ],
        [
            InlineKeyboardButton("Quality", callback_data="noop"),
            InlineKeyboardButton(f"{'✅ ' if session.quality=='Standard' else ''}Standard", callback_data="set_qual_Standard"),
            InlineKeyboardButton(f"{'✅ ' if session.quality=='High' else ''}High", callback_data="set_qual_High")
        ],
        [
            InlineKeyboardButton("➕ Add Photos", callback_data="cmd_add_photos"),
            InlineKeyboardButton("🖼 Create Collage", callback_data="cmd_generate")
        ],
        [InlineKeyboardButton("❌ Cancel Session", callback_data="cmd_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo:
        return

    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)

    if session.state not in ["COLLECTING", "SETTINGS"]:
        session.state = "COLLECTING"

    if len(session.photos) >= MAX_PHOTOS_PER_SESSION:
        await update.message.reply_text(
            f"⚠️ Maximum limit of {MAX_PHOTOS_PER_SESSION} photos reached per collage.\n"
            "Click <b>Create Collage</b> to build your image!",
            parse_mode="HTML"
        )
        return

    try:
        photo_file = await update.message.photo[-1].get_file()
        file_filename = f"{user_id}_{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(TEMP_DIR, file_filename)

        await photo_file.download_to_drive(custom_path=file_path)
        session.photos.append(file_path)

        count = len(session.photos)
        keyboard = [
            [
                InlineKeyboardButton("➕ Add More", callback_data="cmd_add_photos"),
                InlineKeyboardButton("⚙️ Settings", callback_data="cmd_settings")
            ],
            [InlineKeyboardButton("🖼 Create Collage", callback_data="cmd_generate")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cmd_cancel")]
        ]

        await update.message.reply_text(
            f"✅ Photo received! Total: <b>{count}</b> photo(s).",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error downloading photo from user {user_id}: {e}")
        await update.message.reply_text("❌ Failed to download photo. Please try sending it again.")

async def collage_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    session = session_manager.get_session(user_id)

    if data == "noop":
        return

    if data == "cmd_settings":
        session.state = "SETTINGS"
        await query.edit_message_text(
            "⚙️ <b>Configure Your Collage Settings:</b>",
            reply_markup=build_settings_keyboard(session),
            parse_mode="HTML"
        )

    elif data.startswith("set_grid_"):
        session.grid_size = data.replace("set_grid_", "")
        await query.edit_message_reply_markup(reply_markup=build_settings_keyboard(session))

    elif data.startswith("set_space_"):
        session.spacing = data.replace("set_space_", "")
        await query.edit_message_reply_markup(reply_markup=build_settings_keyboard(session))

    elif data.startswith("set_bg_"):
        session.bg_color = data.replace("set_bg_", "")
        await query.edit_message_reply_markup(reply_markup=build_settings_keyboard(session))

    elif data.startswith("set_qual_"):
        session.quality = data.replace("set_qual_", "")
        await query.edit_message_reply_markup(reply_markup=build_settings_keyboard(session))

    elif data == "cmd_add_photos":
        session.state = "COLLECTING"
        await query.edit_message_text(
            f"📸 Send more photos directly to the chat.\nCurrently stored: <b>{len(session.photos)}</b> photos.",
            parse_mode="HTML"
        )

    elif data == "cmd_generate":
        if not session.photos:
            await query.edit_message_text(
                "⚠️ You haven't sent any photos yet! Send me photos first.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🚀 Start Adding Photos", callback_data="cmd_start_collage")
                ]])
            )
            return

        status_msg = await query.edit_message_text("⏳ <i>Processing your collage... Please wait.</i>", parse_mode="HTML")
        output_file = os.path.join(TEMP_DIR, f"collage_{user_id}_{uuid.uuid4().hex}.jpg")

        try:
            create_collage(
                image_paths=session.photos,
                output_path=output_file,
                grid_size=session.grid_size,
                spacing_name=session.spacing,
                bg_name=session.bg_color,
                quality_name=session.quality
            )

            result_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Create Another", callback_data="cmd_start_collage")],
                [InlineKeyboardButton("❌ Delete Session", callback_data="cmd_cancel")]
            ])

            with open(output_file, "rb") as photo_stream:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo_stream,
                    caption=f"✨ <b>Collage Ready!</b>\nLayout: {session.grid_size} | Quality: {session.quality}",
                    reply_markup=result_keyboard,
                    parse_mode="HTML"
                )

            cleanup_session_files(session)
            session_manager.clear_session(user_id)

            try:
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=status_msg.message_id)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Failed to generate collage for user {user_id}: {e}")
            await query.edit_message_text(
                "❌ An error occurred while generating the collage. Please try again with different images."
            )
        finally:
            safe_remove_file(output_file)
