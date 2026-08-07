import logging
from aiohttp import web
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import BOT_TOKEN, PORT
from utils.session import session_manager
from utils.cleanup import cleanup_session_files
from handlers.start import start_command, start_callback_handler
from handlers.commands import help_command, about_command, cancel_command
from handlers.collage import photo_handler, collage_callback_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def session_cleanup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periodic job to clean up inactive user sessions and temporary files."""
    expired_sessions = session_manager.cleanup_inactive_sessions()
    for session in expired_sessions:
        logger.info(f"Cleaning up inactive session for user {session.user_id}")
        cleanup_session_files(session)

async def health_check(request: web.Request) -> web.Response:
    """HTTP Health Check endpoint for Render Web Services."""
    return web.Response(text="Bot is running!", status=200)

async def start_health_server() -> None:
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Health check HTTP server started on port {PORT}")

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Register Callback Query Handlers
    app.add_handler(CallbackQueryHandler(start_callback_handler, pattern="^cmd_(start_collage|help|about)$"))
    app.add_handler(CallbackQueryHandler(collage_callback_handler))

    # Register Photo Handler
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    # Periodic background job for cleaning up stale sessions
    if app.job_queue:
        app.job_queue.run_repeating(session_cleanup_job, interval=300, first=60)

    # Start light HTTP server for Render deployment compatibility
    app.post_init = lambda application: start_health_server()

    logger.info("Starting Photo Collage Grid Bot...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
