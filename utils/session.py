import time
from typing import Dict, List, Any, Optional
from config import SESSION_TIMEOUT_MINUTES, MAX_PHOTOS_PER_SESSION

class UserSession:
    def __init__(self, user_id: int):
        self.user_id: int = user_id
        self.photos: List[str] = []  # Paths to local temp photos
        self.grid_size: str = "2x2"   # Options: "2x2", "3x3", "4x4"
        self.spacing: str = "Medium"   # Options: "Small", "Medium", "Large"
        self.bg_color: str = "White"  # Options: "White", "Black"
        self.quality: str = "High"     # Options: "Standard", "High"
        self.state: str = "IDLE"      # Options: "IDLE", "COLLECTING", "SETTINGS"
        self.last_activity: float = time.time()

    def update_activity(self) -> None:
        self.last_activity = time.time()

    def is_expired(self) -> bool:
        timeout_seconds = SESSION_TIMEOUT_MINUTES * 60
        return (time.time() - self.last_activity) > timeout_seconds

class SessionManager:
    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}

    def get_session(self, user_id: int) -> UserSession:
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id)
        session = self._sessions[user_id]
        session.update_activity()
        return session

    def clear_session(self, user_id: int) -> Optional[UserSession]:
        return self._sessions.pop(user_id, None)

    def cleanup_inactive_sessions(self) -> List[UserSession]:
        expired = []
        for user_id, session in list(self._sessions.items()):
            if session.is_expired():
                expired.append(session)
                del self._sessions[user_id]
        return expired

session_manager = SessionManager()
