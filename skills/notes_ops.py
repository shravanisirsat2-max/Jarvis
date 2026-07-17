import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable
from core.skill import Skill

class NotesSkill(Skill):
    """Skill for quick notes, timers, and alarms."""

    def __init__(self):
        self.notes_file = os.path.expanduser("~/.jarvis_notes.json")
        self._ensure_notes_file()
        self.timers = {}

    def _ensure_notes_file(self):
        if not os.path.exists(self.notes_file):
            with open(self.notes_file, 'w') as f:
                json.dump([], f)

    def _load_notes(self) -> list:
        try:
            with open(self.notes_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def _save_notes(self, notes: list):
        with open(self.notes_file, 'w') as f:
            json.dump(notes, f, indent=2)

    @property
    def name(self) -> str:
        return "notes_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_note",
                    "description": "Add a quick note",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note": {
                                "type": "string",
                                "description": "The note content"
                            }
                        },
                        "required": ["note"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_notes",
                    "description": "List all saved notes",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_note",
                    "description": "Delete a note by its index number",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "index": {
                                "type": "integer",
                                "description": "Index of the note to delete (1-based)"
                            }
                        },
                        "required": ["index"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clear_notes",
                    "description": "Delete all notes",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_timer",
                    "description": "Set a timer for N minutes. I will notify you when it's done.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "minutes": {
                                "type": "integer",
                                "description": "Number of minutes for the timer"
                            },
                            "label": {
                                "type": "string",
                                "description": "Optional label for the timer"
                            }
                        },
                        "required": ["minutes"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "add_note": self.add_note,
            "list_notes": self.list_notes,
            "delete_note": self.delete_note,
            "clear_notes": self.clear_notes,
            "set_timer": self.set_timer
        }

    def add_note(self, note: str) -> str:
        try:
            notes = self._load_notes()
            notes.append({
                "content": note,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self._save_notes(notes)
            return json.dumps({"status": "success", "message": f"Note saved: {note}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def list_notes(self) -> str:
        try:
            notes = self._load_notes()
            if not notes:
                return json.dumps({"status": "success", "message": "No notes saved yet", "notes": []})
            return json.dumps({"status": "success", "count": len(notes), "notes": notes})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_note(self, index: int) -> str:
        try:
            notes = self._load_notes()
            if 1 <= index <= len(notes):
                deleted = notes.pop(index - 1)
                self._save_notes(notes)
                return json.dumps({"status": "success", "message": f"Deleted note: {deleted['content']}"})
            else:
                return json.dumps({"status": "error", "message": "Invalid note index"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def clear_notes(self) -> str:
        try:
            self._save_notes([])
            return json.dumps({"status": "success", "message": "All notes cleared"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def set_timer(self, minutes: int, label: str = "Timer") -> str:
        try:
            timer_id = len(self.timers) + 1
            end_time = datetime.now() + timedelta(minutes=minutes)

            def timer_callback():
                time.sleep(minutes * 60)
                from core.voice import speak
                speak(f"Timer complete! {label} has finished.")

            thread = threading.Thread(target=timer_callback, daemon=True)
            thread.start()

            self.timers[timer_id] = {
                "label": label,
                "minutes": minutes,
                "end_time": end_time.strftime("%H:%M:%S")
            }

            return json.dumps({
                "status": "success",
                "message": f"Timer set for {minutes} minute(s): {label}",
                "timer_id": timer_id,
                "ends_at": end_time.strftime("%H:%M:%S")
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
