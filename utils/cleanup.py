import os
import logging
from utils.session import UserSession

logger = logging.getLogger(__name__)

def cleanup_session_files(session: UserSession) -> None:
    """Deletes all photo files associated with a user session."""
    for photo_path in session.photos:
        try:
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception as e:
            logger.error(f"Failed to delete session file {photo_path}: {e}")
    session.photos.clear()

def safe_remove_file(file_path: str) -> None:
    """Safely removes a single file without throwing unhandled exceptions."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Failed to remove file {file_path}: {e}")
