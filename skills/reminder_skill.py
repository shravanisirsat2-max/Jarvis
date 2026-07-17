import json
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable
from core.skill import Skill


class ReminderSkill(Skill):
    """Smart reminder and scheduling system with background monitoring."""

    @property
    def name(self) -> str:
        return "reminders"

    def initialize(self, context):
        self._context = context
        self._reminder_thread = None
        self._running = False

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "set_reminder",
                    "description": "Set a reminder with a specific time or delay.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "What to remind about"
                            },
                            "minutes": {
                                "type": "number",
                                "description": "Remind in X minutes from now"
                            },
                            "time_str": {
                                "type": "string",
                                "description": "Specific time to remind (e.g., '14:30', '2:30 PM')"
                            }
                        },
                        "required": ["message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_alarm",
                    "description": "Set an alarm for a specific time.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time_str": {
                                "type": "string",
                                "description": "Alarm time (e.g., '07:00', '7 AM')"
                            },
                            "label": {
                                "type": "string",
                                "description": "Alarm label (e.g., 'Wake up', 'Meeting')"
                            }
                        },
                        "required": ["time_str"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_reminders",
                    "description": "List all pending reminders.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_reminder",
                    "description": "Cancel a pending reminder by its ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reminder_id": {
                                "type": "number",
                                "description": "The reminder ID to cancel"
                            }
                        },
                        "required": ["reminder_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "start_pomodoro",
                    "description": "Start a Pomodoro timer (25 min work, 5 min break).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "work_minutes": {
                                "type": "number",
                                "description": "Work duration in minutes (default: 25)"
                            }
                        }
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "set_reminder": self.set_reminder,
            "set_alarm": self.set_alarm,
            "list_reminders": self.list_reminders,
            "cancel_reminder": self.cancel_reminder,
            "start_pomodoro": self.start_pomodoro,
        }

    def _parse_time(self, time_str: str) -> datetime:
        time_str = time_str.strip().upper()
        now = datetime.now()
        for fmt in ["%H:%M", "%I:%M %p", "%I:%M%p"]:
            try:
                t = datetime.strptime(time_str, fmt)
                result = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
                if result <= now:
                    result += timedelta(days=1)
                return result
            except ValueError:
                continue
        raise ValueError(f"Cannot parse time: {time_str}")

    def set_reminder(self, message: str, minutes: float = None, time_str: str = None) -> str:
        try:
            if minutes:
                remind_at = datetime.now() + timedelta(minutes=minutes)
            elif time_str:
                remind_at = self._parse_time(time_str)
            else:
                return json.dumps({"status": "error", "message": "Specify minutes or time_str"})

            from core.memory import Memory
            memory = Memory()
            memory.add_reminder(message, remind_at.isoformat())

            self._start_monitoring()

            return json.dumps({
                "status": "success",
                "message": f"Reminder set for {remind_at.strftime('%I:%M %p')}: {message}",
                "remind_at": remind_at.isoformat()
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def set_alarm(self, time_str: str, label: str = "Alarm") -> str:
        try:
            alarm_time = self._parse_time(time_str)
            from core.memory import Memory
            memory = Memory()
            memory.add_reminder(f"ALARM: {label}", alarm_time.isoformat())
            self._start_monitoring()
            return json.dumps({
                "status": "success",
                "message": f"Alarm set for {alarm_time.strftime('%I:%M %p')} - {label}"
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def list_reminders(self) -> str:
        try:
            from core.memory import Memory
            memory = Memory()
            pending = memory.get_pending_reminders()
            all_reminders = []
            import sqlite3
            conn = sqlite3.connect(memory.db_path)
            c = conn.cursor()
            c.execute("SELECT id, message, remind_at, completed FROM reminders ORDER BY remind_at DESC LIMIT 10")
            for row in c.fetchall():
                all_reminders.append({
                    "id": row[0], "message": row[1],
                    "remind_at": row[2], "completed": bool(row[3])
                })
            conn.close()
            return json.dumps({"status": "success", "pending": len(pending), "reminders": all_reminders})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def cancel_reminder(self, reminder_id: int) -> str:
        try:
            from core.memory import Memory
            memory = Memory()
            memory.complete_reminder(reminder_id)
            return json.dumps({"status": "success", "message": f"Reminder {reminder_id} cancelled."})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def start_pomodoro(self, work_minutes: int = 25) -> str:
        def pomodoro_timer():
            try:
                from core.voice import speak
                speak(f"Pomodoro started. Work for {work_minutes} minutes.")
                time.sleep(work_minutes * 60)
                speak("Work session complete! Take a 5 minute break.")
                time.sleep(5 * 60)
                speak("Break over! Ready for another round?")
            except Exception:
                pass

        t = threading.Thread(target=pomodoro_timer, daemon=True)
        t.start()
        return json.dumps({"status": "success", "message": f"Pomodoro started: {work_minutes} min work, 5 min break"})

    def _start_monitoring(self):
        if self._running:
            return
        self._running = True
        self._reminder_thread = threading.Thread(target=self._monitor_reminders, daemon=True)
        self._reminder_thread.start()

    def _monitor_reminders(self):
        from core.memory import Memory
        from core.voice import speak
        while self._running:
            try:
                memory = Memory()
                pending = memory.get_pending_reminders()
                for reminder in pending:
                    speak(f"Reminder: {reminder['message']}")
                    memory.complete_reminder(reminder['id'])
            except Exception:
                pass
            time.sleep(30)
