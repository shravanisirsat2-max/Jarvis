import json
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill


class ProactiveSkill(Skill):
    """Proactive suggestions based on time, context, and user patterns."""

    @property
    def name(self) -> str:
        return "proactive"

    def initialize(self, context):
        self._context = context

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_context_suggestions",
                    "description": "Get proactive suggestions based on current time and context.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_daily_briefing",
                    "description": "Get a morning briefing with weather, calendar, tasks, and reminders.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_usage_patterns",
                    "description": "Analyze what apps and commands the user uses most.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_wellness_check",
                    "description": "Check battery, screen time, and suggest breaks.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "get_context_suggestions": self.get_context_suggestions,
            "get_daily_briefing": self.get_daily_briefing,
            "analyze_usage_patterns": self.analyze_usage_patterns,
            "get_wellness_check": self.get_wellness_check,
        }

    def get_context_suggestions(self) -> str:
        now = datetime.now()
        hour = now.hour
        suggestions = []
        if 6 <= hour < 9:
            suggestions = ["Check today's weather", "Review calendar for the day", "Set focus music", "Check traffic to work"]
        elif 9 <= hour < 12:
            suggestions = ["Start a Pomodoro session", "Check emails for urgent items", "Review pending tasks"]
        elif 12 <= hour < 14:
            suggestions = ["Lunch reminder", "Quick stretch break", "Check afternoon schedule"]
        elif 14 <= hour < 17:
            suggestions = ["Afternoon productivity check", "Review task completion", "Plan tomorrow's schedule"]
        elif 17 <= hour < 20:
            suggestions = ["Review what you accomplished today", "Set reminders for tomorrow", "Evening wind-down"]
        elif 20 <= hour < 23:
            suggestions = ["Review tomorrow's calendar", "Set morning alarm", "Clean temp files", "Check battery and charge"]
        else:
            suggestions = ["You should be sleeping! Set a sleep timer?", "Enable Do Not Disturb mode"]

        return json.dumps({
            "status": "success",
            "time": now.strftime("%I:%M %p"),
            "suggestions": suggestions
        })

    def get_daily_briefing(self) -> str:
        now = datetime.now()
        briefing = {
            "greeting": f"Good {'morning' if now.hour < 12 else 'afternoon' if now.hour < 17 else 'evening'}, sir.",
            "date": now.strftime("%A, %B %d, %Y"),
            "time": now.strftime("%I:%M %p"),
        }

        try:
            from core.memory import Memory
            memory = Memory()
            reminders = memory.get_pending_reminders()
            briefing["pending_reminders"] = len(reminders)
            briefing["reminder_details"] = [r["message"] for r in reminders[:3]]
        except:
            briefing["pending_reminders"] = 0

        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                briefing["battery"] = f"{battery.percent}%"
                briefing["charging"] = battery.power_plugged
        except:
            pass

        briefing["suggestions"] = ["Check your schedule", "Review emails", "Plan your day"]

        return json.dumps({"status": "success", "briefing": briefing})

    def analyze_usage_patterns(self) -> str:
        try:
            from core.memory import Memory
            memory = Memory()
            messages = memory.get_recent_messages(limit=50)

            commands = {}
            for msg in messages:
                if msg["role"] == "user":
                    words = msg["content"].lower().split()
                    for word in words:
                        if len(word) > 3:
                            commands[word] = commands.get(word, 0) + 1

            top_commands = sorted(commands.items(), key=lambda x: x[1], reverse=True)[:10]

            return json.dumps({
                "status": "success",
                "total_interactions": len(messages),
                "top_words": top_commands,
                "suggestion": "I notice you use certain commands frequently. Would you like me to create shortcuts?"
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_wellness_check(self) -> str:
        import psutil
        battery = psutil.sensors_battery()
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)

        suggestions = []
        if battery and battery.percent < 20 and not battery.power_plugged:
            suggestions.append("Battery is low! Consider plugging in the charger.")
        if battery and battery.percent > 90 and battery.power_plugged:
            suggestions.append("Battery is fully charged. You can unplug the charger.")
        if cpu > 80:
            suggestions.append("CPU usage is high. Consider closing some applications.")
        if ram.percent > 85:
            suggestions.append("RAM usage is high. Consider restarting memory-heavy apps.")

        now = datetime.now()
        if now.hour >= 22:
            suggestions.append("It's late. Consider wrapping up and getting some rest.")

        return json.dumps({
            "status": "success",
            "battery": f"{battery.percent}% {'(charging)' if battery.power_plugged else '(on battery)'}" if battery else "N/A",
            "cpu": f"{cpu}%",
            "ram": f"{ram.percent}% ({round(ram.used/(1024**3), 1)}GB / {round(ram.total/(1024**3), 1)}GB)",
            "suggestions": suggestions if suggestions else ["Everything looks good!"]
        })
