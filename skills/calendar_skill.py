import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable
from core.skill import Skill


class CalendarSkill(Skill):
    """Calendar and event management with local database."""

    @property
    def name(self) -> str:
        return "calendar"

    def initialize(self, context):
        self._db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jarvis_calendar.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_date TEXT NOT NULL,
            event_time TEXT,
            duration_minutes INTEGER DEFAULT 60,
            location TEXT,
            reminder_minutes INTEGER DEFAULT 15,
            recurring TEXT,
            created_at TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )''')
        conn.commit()
        conn.close()

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_event",
                    "description": "Create a calendar event.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Event title"},
                            "date": {"type": "string", "description": "Date (YYYY-MM-DD or 'tomorrow', 'next monday')"},
                            "time": {"type": "string", "description": "Time (HH:MM or '10 AM')"},
                            "duration": {"type": "number", "description": "Duration in minutes (default: 60)"},
                            "location": {"type": "string", "description": "Event location"},
                            "description": {"type": "string", "description": "Event description"}
                        },
                        "required": ["title", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "view_events",
                    "description": "View events for a specific date or date range.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "Date to view (YYYY-MM-DD, 'today', 'tomorrow', 'this week')"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_event",
                    "description": "Delete a calendar event by title.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Event title to delete"}
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a to-do task.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Task title"},
                            "description": {"type": "string", "description": "Task description"},
                            "priority": {"type": "string", "description": "Priority: low, medium, high"},
                            "due_date": {"type": "string", "description": "Due date (YYYY-MM-DD)"}
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "view_tasks",
                    "description": "View pending tasks.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter": {"type": "string", "description": "Filter: all, pending, completed"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_task",
                    "description": "Mark a task as completed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "number", "description": "Task ID to complete"}
                        },
                        "required": ["task_id"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "create_event": self.create_event,
            "view_events": self.view_events,
            "delete_event": self.delete_event,
            "create_task": self.create_task,
            "view_tasks": self.view_tasks,
            "complete_task": self.complete_task,
        }

    def _parse_date(self, date_str: str) -> str:
        today = datetime.now()
        date_str = date_str.lower().strip()
        if date_str == "today":
            return today.strftime("%Y-%m-%d")
        elif date_str == "tomorrow":
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif date_str == "next week":
            return (today + timedelta(weeks=1)).strftime("%Y-%m-%d")
        elif date_str.startswith("next "):
            days = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
            for day_name, day_num in days.items():
                if day_name in date_str:
                    current_day = today.weekday()
                    days_ahead = (day_num - current_day) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        return date_str

    def _parse_time(self, time_str: str) -> str:
        time_str = time_str.strip().upper()
        for fmt in ["%H:%M", "%I:%M %p", "%I:%M%p"]:
            try:
                t = datetime.strptime(time_str, fmt)
                return t.strftime("%H:%M")
            except ValueError:
                continue
        return time_str

    def create_event(self, title: str, date: str, time: str = "09:00", duration: int = 60, location: str = None, description: str = None) -> str:
        try:
            event_date = self._parse_date(date)
            event_time = self._parse_time(time) if time else "09:00"
            now = datetime.now().isoformat()
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute(
                "INSERT INTO events (title, description, event_date, event_time, duration_minutes, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title, description, event_date, event_time, duration, location, now)
            )
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "message": f"Event '{title}' created on {date} at {time}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def view_events(self, date: str = "today") -> str:
        try:
            target_date = self._parse_date(date)
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            if date.lower() == "this week":
                today = datetime.now()
                week_end = (today + timedelta(days=7)).strftime("%Y-%m-%d")
                c.execute("SELECT id, title, event_date, event_time, location, description FROM events WHERE event_date BETWEEN ? AND ? ORDER BY event_date, event_time",
                         (today.strftime("%Y-%m-%d"), week_end))
            else:
                c.execute("SELECT id, title, event_date, event_time, location, description FROM events WHERE event_date = ? ORDER BY event_time",
                         (target_date,))
            rows = c.fetchall()
            conn.close()
            events = [{"id": r[0], "title": r[1], "date": r[2], "time": r[3], "location": r[4], "description": r[5]} for r in rows]
            return json.dumps({"status": "success", "date": target_date, "count": len(events), "events": events})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_event(self, title: str) -> str:
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute("DELETE FROM events WHERE title LIKE ?", (f"%{title}%",))
            deleted = c.rowcount
            conn.commit()
            conn.close()
            if deleted:
                return json.dumps({"status": "success", "message": f"Deleted {deleted} event(s) matching '{title}'"})
            return json.dumps({"status": "error", "message": f"No event found with title: {title}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def create_task(self, title: str, description: str = None, priority: str = "medium", due_date: str = None) -> str:
        try:
            now = datetime.now().isoformat()
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute(
                "INSERT INTO tasks (title, description, priority, due_date, created_at) VALUES (?, ?, ?, ?, ?)",
                (title, description, priority, due_date, now)
            )
            conn.commit()
            conn.close()
            return json.dumps({"status": "success", "message": f"Task '{title}' created with {priority} priority"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def view_tasks(self, filter: str = "pending") -> str:
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            if filter == "completed":
                c.execute("SELECT id, title, priority, due_date FROM tasks WHERE completed = 1 ORDER BY due_date")
            elif filter == "all":
                c.execute("SELECT id, title, priority, due_date FROM tasks ORDER BY completed, due_date")
            else:
                c.execute("SELECT id, title, priority, due_date FROM tasks WHERE completed = 0 ORDER BY due_date")
            rows = c.fetchall()
            conn.close()
            tasks = [{"id": r[0], "title": r[1], "priority": r[2], "due_date": r[3]} for r in rows]
            return json.dumps({"status": "success", "count": len(tasks), "tasks": tasks})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def complete_task(self, task_id: int) -> str:
        try:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
            updated = c.rowcount
            conn.commit()
            conn.close()
            if updated:
                return json.dumps({"status": "success", "message": f"Task {task_id} marked as completed!"})
            return json.dumps({"status": "error", "message": f"Task {task_id} not found"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
