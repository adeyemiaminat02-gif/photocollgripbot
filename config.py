import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

PORT: int = int(os.getenv("PORT", "10000"))
SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "15"))
MAX_PHOTOS_PER_SESSION: int = int(os.getenv("MAX_PHOTOS_PER_SESSION", "16"))

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp_collages"
TEMP_DIR.mkdir(exist_ok=True)
