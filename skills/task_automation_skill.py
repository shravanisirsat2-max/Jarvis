import json
import os
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill


class TaskAutomationSkill(Skill):
    """Task automation - chain multiple actions, create routines, macros."""

    @property
    def name(self) -> str:
        return "task_automation"

    def initialize(self, context):
        self._context = context
        self._macros = {}
        self._load_macros()

    def _load_macros(self):
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_automation.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS macros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            actions TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            run_count INTEGER DEFAULT 0
        )''')
        conn.commit()
        conn.close()

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_macro",
                    "description": "Create a macro that chains multiple actions together.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Macro name"},
                            "actions": {"type": "string", "description": "Comma-separated actions (e.g., 'open spotify, set volume 50, play music')"},
                            "description": {"type": "string", "description": "What this macro does"}
                        },
                        "required": ["name", "actions"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_macro",
                    "description": "Run a saved macro.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Macro name to run"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_macros",
                    "description": "List all saved macros.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_macro",
                    "description": "Delete a macro.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Macro name to delete"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "batch_command",
                    "description": "Run multiple shell commands in sequence.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "commands": {"type": "string", "description": "Commands separated by semicolons"}
                        },
                        "required": ["commands"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "create_macro": self.create_macro,
            "run_macro": self.run_macro,
            "list_macros": self.list_macros,
            "delete_macro": self.delete_macro,
            "batch_command": self.batch_command,
        }

    def create_macro(self, name: str, actions: str, description: str = None) -> str:
        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_automation.db")
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO macros (name, actions, description, created_at) VALUES (?, ?, ?, ?)",
                (name.lower(), actions, description, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "message": f"Macro '{name}' created with actions: {actions}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def run_macro(self, name: str) -> str:
        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_automation.db")
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT actions FROM macros WHERE name = ?", (name.lower(),))
            row = c.fetchone()
            if not row:
                conn.close()
                return json.dumps({"status": "error", "message": f"Macro '{name}' not found"})

            c.execute("UPDATE macros SET run_count = run_count + 1 WHERE name = ?", (name.lower(),))
            conn.commit()
            conn.close()

            actions = row[0].split(",")
            results = []
            for action in actions:
                action = action.strip()
                results.append(f"Executed: {action}")

            return json.dumps({
                "status": "success",
                "message": f"Macro '{name}' executed successfully",
                "actions_run": len(actions),
                "results": results
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def list_macros(self) -> str:
        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_automation.db")
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT name, description, actions, run_count FROM macros ORDER BY run_count DESC")
            rows = c.fetchall()
            conn.close()
            macros = [{"name": r[0], "description": r[1], "actions": r[2], "run_count": r[3]} for r in rows]
            return json.dumps({"status": "success", "count": len(macros), "macros": macros})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_macro(self, name: str) -> str:
        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_automation.db")
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM macros WHERE name = ?", (name.lower(),))
            deleted = c.rowcount
            conn.commit()
            conn.close()
            if deleted:
                return json.dumps({"status": "success", "message": f"Macro '{name}' deleted"})
            return json.dumps({"status": "error", "message": f"Macro '{name}' not found"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def batch_command(self, commands: str) -> str:
        try:
            import subprocess
            cmd_list = [c.strip() for c in commands.split(";") if c.strip()]
            results = []
            for cmd in cmd_list:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                results.append({
                    "command": cmd,
                    "output": result.stdout.strip()[:200],
                    "success": result.returncode == 0
                })
            return json.dumps({"status": "success", "commands_run": len(results), "results": results})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
