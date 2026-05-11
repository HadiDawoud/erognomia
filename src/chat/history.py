import json
import os
import sqlite3
from functools import lru_cache
from typing import Any, Dict, List, Optional

class ChatHistory:
    def __init__(self, db_path: str = "./data/chat_history.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            conn.commit()

    def create_session(self, session_id: str, title: str = "New Chat"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO sessions (id, title) VALUES (?, ?)", (session_id, title))
            conn.commit()

    def add_message(self, session_id: str, role: str, content: str, sources: Optional[List[Dict]] = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, sources) VALUES (?, ?, ?, ?)",
                (session_id, role, content, json.dumps(sources) if sources else None)
            )
            conn.commit()

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT role, content, sources, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp", (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_sessions(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_session(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

@lru_cache(maxsize=1)
def get_chat_history() -> ChatHistory:
    return ChatHistory()
