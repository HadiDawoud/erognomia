import json
import logging
import os
import sqlite3
from functools import lru_cache
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class ChatHistory:
    def __init__(self, db_path: str = "./data/chat_history.db", retention_days: Optional[int] = None):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()
        if retention_days is not None:
            self.cleanup_old_sessions(retention_days)

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_summarized_at TIMESTAMP,
                    user_edited INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    sources TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            self._migrate_sessions(conn)
            conn.commit()

    def _migrate_sessions(self, conn: sqlite3.Connection):
        """Add columns introduced after the initial schema to pre-existing databases."""
        existing = {row[1] for row in conn.execute("PRAGMA table_info(sessions)")}
        if "updated_at" not in existing:
            conn.execute("ALTER TABLE sessions ADD COLUMN updated_at TIMESTAMP")
            conn.execute("UPDATE sessions SET updated_at = created_at WHERE updated_at IS NULL")
        if "last_summarized_at" not in existing:
            conn.execute("ALTER TABLE sessions ADD COLUMN last_summarized_at TIMESTAMP")
        if "user_edited" not in existing:
            conn.execute("ALTER TABLE sessions ADD COLUMN user_edited INTEGER DEFAULT 0")

    def create_session(self, session_id: str, title: str = "New Chat"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sessions (id, title, created_at, updated_at) "
                "VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (session_id, title),
            )
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str, sources: Optional[List[Dict]] = None):
        with sqlite3.connect(self.db_path) as conn:
            # Ensure the session exists so messages are never orphaned.
            conn.execute(
                "INSERT OR IGNORE INTO sessions (id, created_at, updated_at) "
                "VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (session_id,),
            )
            conn.execute(
                "INSERT INTO messages (session_id, role, content, sources) VALUES (?, ?, ?, ?)",
                (session_id, role, content, json.dumps(sources) if sources else None)
            )
            conn.execute(
                "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,),
            )
            conn.commit()

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT role, content, sources, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp", (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_sessions(self) -> List[Dict[str, Any]]:
        """List sessions that have at least one message, newest activity first.

        Empty sessions (created but never used) are hidden so they never clutter
        the sidebar.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT s.id, s.title, s.created_at, s.updated_at, s.last_summarized_at, s.user_edited "
                "FROM sessions s "
                "WHERE EXISTS (SELECT 1 FROM messages m WHERE m.session_id = s.id) "
                "ORDER BY s.updated_at DESC, s.created_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, title, created_at, updated_at, last_summarized_at, user_edited "
                "FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_title(self, session_id: str, title: str, user_edited: bool = False):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, user_edited = ? WHERE id = ?",
                (title, 1 if user_edited else 0, session_id),
            )
            conn.commit()

    def mark_summarized(self, session_id: str, title: str):
        """Store an auto-generated title and record when it was produced.

        Never touches user-edited sessions and leaves updated_at untouched so a
        message arriving during summarization still triggers a future refresh.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, last_summarized_at = CURRENT_TIMESTAMP "
                "WHERE id = ? AND user_edited = 0",
                (title, session_id),
            )
            conn.commit()

    def get_sessions_needing_summary(self) -> List[Dict[str, Any]]:
        """Sessions with at least one message and new activity since last summary."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT s.id, s.title, s.updated_at, s.last_summarized_at
                FROM sessions s
                WHERE s.user_edited = 0
                  AND EXISTS (SELECT 1 FROM messages m WHERE m.session_id = s.id)
                  AND (s.last_summarized_at IS NULL OR s.updated_at > s.last_summarized_at)
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_session(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()

    def cleanup_old_sessions(self, max_age_days: int = 90):
        """Remove sessions older than max_age_days and their messages (via CASCADE)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE created_at < datetime('now', ?)",
                (f"-{max_age_days} days",),
            )
            deleted = cursor.rowcount
            conn.commit()
        if deleted:
            logger.info("Cleaned up %d old session(s) (age > %d days)", deleted, max_age_days)

@lru_cache(maxsize=1)
def get_chat_history() -> ChatHistory:
    from src.config import settings
    return ChatHistory(
        retention_days=settings.chat_history_retention_days,
    )
