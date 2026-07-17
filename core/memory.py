import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class Memory:
    """Persistent memory system using SQLite. Stores conversations, facts, and preferences."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_memory.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_used TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            remind_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )''')

        conn.commit()
        conn.close()

    def save_message(self, role: str, content: str, tool_used: str = None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO conversations (timestamp, role, content, tool_used) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), role, content, tool_used)
        )
        conn.commit()
        conn.close()

    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT role, content, timestamp FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = c.fetchall()
        conn.close()
        messages = []
        for row in reversed(rows):
            messages.append({"role": row[0], "content": row[1], "timestamp": row[2]})
        return messages

    def remember_fact(self, key: str, value: str):
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO facts (key, value, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (key.lower(), value, now, now)
        )
        conn.commit()
        conn.close()

    def recall_fact(self, key: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT value FROM facts WHERE key = ?", (key.lower(),))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

    def forget_fact(self, key: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM facts WHERE key = ?", (key.lower(),))
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def get_all_facts(self) -> Dict[str, str]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT key, value FROM facts")
        rows = c.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def set_preference(self, key: str, value: str):
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, ?)",
            (key.lower(), value, now)
        )
        conn.commit()
        conn.close()

    def get_preference(self, key: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT value FROM preferences WHERE key = ?", (key.lower(),))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

    def add_reminder(self, message: str, remind_at: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO reminders (message, remind_at, created_at) VALUES (?, ?, ?)",
            (message, remind_at, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def get_pending_reminders(self) -> List[Dict]:
        now = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT id, message, remind_at FROM reminders WHERE completed = 0 AND remind_at <= ?",
            (now,)
        )
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "message": r[1], "remind_at": r[2]} for r in rows]

    def complete_reminder(self, reminder_id: int):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE reminders SET completed = 1 WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()

    def get_conversation_summary(self, limit: int = 5) -> str:
        messages = self.get_recent_messages(limit)
        if not messages:
            return "No conversation history."
        summary = "Recent conversation:\n"
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Jarvis"
            summary += f"{role}: {msg['content'][:100]}\n"
        return summary
