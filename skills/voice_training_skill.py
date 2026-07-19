import json
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill


class VoiceTrainingSkill(Skill):
    """Voice pattern learning - adapts to user habits over time."""

    @property
    def name(self) -> str:
        return "voice_training"

    def initialize(self, context):
        self._db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_training.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS command_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            tool_used TEXT,
            frequency INTEGER DEFAULT 1,
            last_used TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_phrases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phrase TEXT UNIQUE NOT NULL,
            meaning TEXT NOT NULL,
            created_at TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS response_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            rating INTEGER,
            feedback TEXT,
            created_at TEXT NOT NULL
        )''')
        conn.commit()
        conn.close()

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "log_command_usage",
                    "description": "Log what command was used and what tool was called (internal).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The user's command"},
                            "tool": {"type": "string", "description": "The tool that was used"}
                        },
                        "required": ["command", "tool"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "teach_phrase",
                    "description": "Teach Jarvis a custom phrase or shortcut.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phrase": {"type": "string", "description": "The custom phrase (e.g., 'morning routine')"},
                            "meaning": {"type": "string", "description": "What it means (e.g., 'open spotify, set volume 40, check weather')"}
                        },
                        "required": ["phrase", "meaning"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_learned_phrases",
                    "description": "Get all custom phrases you've learned.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_usage_stats",
                    "description": "Get statistics on how you've been using Jarvis.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rate_response",
                    "description": "Rate the last response to help Jarvis learn.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "rating": {"type": "number", "description": "Rating from 1-5"},
                            "feedback": {"type": "string", "description": "Optional feedback text"}
                        },
                        "required": ["rating"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_frequent_commands",
                    "description": "Get your most used commands.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "number", "description": "Number of top commands to return (default: 5)"}
                        }
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "log_command_usage": self.log_command_usage,
            "teach_phrase": self.teach_phrase,
            "get_learned_phrases": self.get_learned_phrases,
            "get_usage_stats": self.get_usage_stats,
            "rate_response": self.rate_response,
            "get_frequent_commands": self.get_frequent_commands,
        }

    def log_command_usage(self, command: str, tool: str) -> str:
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute("SELECT id, frequency FROM command_patterns WHERE command = ?", (command,))
            row = c.fetchone()
            if row:
                c.execute("UPDATE command_patterns SET frequency = frequency + 1, last_used = ? WHERE id = ?",
                         (datetime.now().isoformat(), row[0]))
            else:
                c.execute("INSERT INTO command_patterns (command, tool_used, last_used) VALUES (?, ?, ?)",
                         (command, tool, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "message": "Command pattern logged"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def teach_phrase(self, phrase: str, meaning: str) -> str:
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO user_phrases (phrase, meaning, created_at) VALUES (?, ?, ?)",
                (phrase.lower(), meaning, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "message": f"Learned: '{phrase}' means '{meaning}'"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_learned_phrases(self) -> str:
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute("SELECT phrase, meaning FROM user_phrases ORDER BY created_at DESC")
            rows = c.fetchall()
            conn.close()
            phrases = [{"phrase": r[0], "meaning": r[1]} for r in rows]
            return json.dumps({"status": "success", "count": len(phrases), "phrases": phrases})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_usage_stats(self) -> str:
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM command_patterns")
            total_commands = c.fetchone()[0]
            c.execute("SELECT COUNT(DISTINCT command) FROM command_patterns")
            unique_commands = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM user_phrases")
            learned_phrases = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM response_feedback")
            feedback_count = c.fetchone()[0]
            c.execute("SELECT AVG(rating) FROM response_feedback WHERE rating IS NOT NULL")
            avg_rating = c.fetchone()[0]
            conn.close()
            return json.dumps({
                "status": "success",
                "stats": {
                    "total_commands_used": total_commands,
                    "unique_commands": unique_commands,
                    "learned_phrases": learned_phrases,
                    "feedback_given": feedback_count,
                    "avg_satisfaction": round(avg_rating, 1) if avg_rating else "N/A"
                }
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def rate_response(self, rating: int, feedback: str = None) -> str:
        try:
            rating = max(1, min(5, rating))
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute(
                "INSERT INTO response_feedback (query, response, rating, feedback, created_at) VALUES (?, ?, ?, ?, ?)",
                ("last_query", "last_response", rating, feedback, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "message": f"Thanks for the {rating}-star feedback! I'll improve."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_frequent_commands(self, limit: int = 5) -> str:
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute("SELECT command, tool_used, frequency FROM command_patterns ORDER BY frequency DESC LIMIT ?", (limit,))
            rows = c.fetchall()
            conn.close()
            commands = [{"command": r[0], "tool": r[1], "times_used": r[2]} for r in rows]
            return json.dumps({"status": "success", "commands": commands})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
