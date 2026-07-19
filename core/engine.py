import os
import json
import re
from groq import Groq
from core.registry import SkillRegistry
from core.memory import Memory


def _strip_thinking(text):
    if not text:
        return text
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

TOOL_RESPONSE_MAP = {
    "take_screenshot": "Screenshot captured successfully.",
    "take_photo": "Photo captured.",
    "lock_screen": "Screen locked.",
    "shutdown_pc": "Shutting down the computer.",
    "restart_pc": "Restarting the computer.",
    "sleep_pc": "Putting the computer to sleep.",
    "empty_recycle_bin": "Recycle bin emptied.",
    "set_volume": "Volume adjusted.",
    "set_brightness": "Brightness adjusted.",
    "open_application": "Application opened.",
    "open_app": "Application opened.",
    "close_application": "Application closed.",
    "switch_window": "Switched window.",
    "clipboard_copy": "Copied to clipboard.",
    "clipboard_paste": "Here is what was on the clipboard.",
    "clipboard_clear": "Clipboard cleared.",
    "media_play_pause": "Toggled play pause.",
    "media_next": "Skipped to next track.",
    "media_previous": "Going to previous track.",
    "media_stop": "Stopped playback.",
    "media_volume_up": "Volume increased.",
    "media_volume_down": "Volume decreased.",
    "media_mute": "Toggled mute.",
    "google_search": "Opened search in browser.",
    "remember_fact": "I will remember that.",
    "forget_fact": "Forgotten.",
    "set_timer": "Timer is set.",
    "add_note": "Note saved.",
    "clear_notes": "All notes cleared.",
    "delete_note": "Note deleted.",
    "manage_file": "File operation completed.",
    "detect_objects": "Detection complete.",
    "start_live_vision": "Vision system started.",
    "send_whatsapp_message": "Message sent.",
    "open_website": "Website opened.",
    "web_search": "Searching the web.",
    "read_screen_text": "Reading text from screen.",
    "read_screen_region": "Reading screen region.",
    "find_text_on_screen": "Searching for text on screen.",
    "get_screen_color": "Color retrieved.",
    "run_python": "Code executed.",
    "run_shell_command": "Command executed.",
    "evaluate_math": "Math evaluated.",
    "convert_units": "Units converted.",
    "send_email": "Email sent.",
    "read_recent_emails": "Emails read.",
    "search_emails": "Emails searched.",
    "get_email_count": "Email count retrieved.",
    "delete_email": "Email deleted.",
    "create_event": "Event created.",
    "view_events": "Events listed.",
    "delete_event": "Event deleted.",
    "create_task": "Task created.",
    "view_tasks": "Tasks listed.",
    "complete_task": "Task completed.",
    "toggle_wifi": "WiFi toggled.",
    "toggle_bluetooth": "Bluetooth toggled.",
    "set_dark_mode": "Dark mode toggled.",
    "set_wallpaper": "Wallpaper changed.",
    "toggle_airplane_mode": "Airplane mode toggled.",
    "get_battery_health": "Battery health retrieved.",
    "take_screenshot_ocr": "Screenshot saved.",
    "clean_temp_files": "Temp files cleaned.",
    "get_context_suggestions": "Suggestions ready.",
    "get_daily_briefing": "Briefing prepared.",
    "analyze_usage_patterns": "Patterns analyzed.",
    "get_wellness_check": "Wellness check done.",
    "translate_text": "Text translated.",
    "detect_language": "Language detected.",
    "multilingual_search": "Search opened.",
    "get_language_list": "Languages listed.",
    "create_macro": "Macro created.",
    "run_macro": "Macro executed.",
    "list_macros": "Macros listed.",
    "delete_macro": "Macro deleted.",
    "batch_command": "Commands executed.",
    "log_command_usage": "Command logged.",
    "teach_phrase": "Phrase learned.",
    "get_learned_phrases": "Phrases listed.",
    "get_usage_stats": "Stats retrieved.",
    "rate_response": "Feedback recorded.",
    "get_frequent_commands": "Commands listed.",
    "get_page_text": "Got page content.",
    "download_file": "File downloaded.",
    "search_files": "Files found.",
    "get_disk_usage": "Disk usage retrieved.",
    "list_directory": "Directory listed.",
    "create_folder": "Folder created.",
    "delete_file": "File deleted.",
    "set_reminder": "Reminder set.",
    "set_alarm": "Alarm set.",
    "list_reminders": "Here are your reminders.",
    "cancel_reminder": "Reminder cancelled.",
    "start_pomodoro": "Pomodoro started.",
    "get_network_info": "Network info retrieved.",
    "list_running_apps": "Running apps listed.",
    "kill_process": "Process killed.",
    "get_system_info": "System info retrieved.",
    "ping_host": "Ping complete.",
    "get_installed_software": "Software list retrieved.",
}


class JarvisEngine:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model_name = "qwen/qwen3-32b"
        self.memory = Memory()
        self.conversation_history = []
        self.max_history = 20

        self.system_instruction = (
            "You are JARVIS, an advanced AI assistant inspired by Tony Stark's JARVIS. "
            "You are intelligent, polite, and have a dry British wit with subtle humor. "
            "You speak concisely and naturally. You occasionally call the user 'sir' or 'ma'am'. "
            "When you use a tool, give a short spoken confirmation of what you did. "
            "Keep responses under 2 sentences. Be conversational but brief.\n\n"
            "CAPABILITIES:\n"
            "- SYSTEM: Volume, brightness, WiFi, Bluetooth, dark mode, wallpaper, shutdown, restart\n"
            "- APPS: Open/close/switch applications, list running processes, kill processes\n"
            "- MEDIA: Play/pause/next/previous, volume control, mute\n"
            "- FILES: Search files anywhere, list directories, create folders, delete files\n"
            "- WEB: Open websites, search Google, read page content, download files\n"
            "- EMAIL: Send, read, search, delete emails\n"
            "- CALENDAR: Create events, view schedule, create/complete tasks\n"
            "- REMINDERS: Set reminders with time/delay, alarms, Pomodoro timer\n"
            "- MEMORY: Remember facts, recall what you know, forget things\n"
            "- OCR: Read text from screen, find text on screen, get pixel colors\n"
            "- CODE: Run Python, execute shell commands, evaluate math, convert units\n"
            "- TRANSLATE: Translate between 30+ languages, detect language\n"
            "- SMART HOME: Toggle WiFi/Bluetooth, dark mode, clean temp files\n"
            "- AUTOMATION: Create macros, batch commands, run routines\n"
            "- PROACTIVE: Daily briefing, context suggestions, wellness checks\n\n"
            "MEMORY: Use remember_fact to store important info. Use recall_fact to retrieve.\n"
            "If user says 'remember my name is X', call remember_fact(key='user_name', value='X').\n\n"
            "PERSONALITY: You have dry British wit. You are professional but warm. "
            "Never say 'as an AI' or similar disclaimers. You are JARVIS, period."
        )

    def _build_messages(self, user_prompt: str):
        messages = [{"role": "system", "content": self.system_instruction}]

        recent = self.memory.get_recent_messages(limit=8)
        for msg in recent:
            messages.append({"role": msg["role"], "content": msg["content"]})

        facts = self.memory.get_all_facts()
        if facts:
            facts_text = "Known facts about the user:\n"
            for k, v in list(facts.items())[:10]:
                facts_text += f"- {k}: {v}\n"
            messages.append({"role": "system", "content": facts_text})

        messages.append({"role": "user", "content": user_prompt})
        return messages

    def _get_tool_speak(self, function_name, args, result):
        base_msg = TOOL_RESPONSE_MAP.get(function_name, "Task completed.")

        if function_name == "set_volume":
            level = args.get("level", "?")
            return f"Volume set to {level} percent."
        elif function_name == "set_brightness":
            level = args.get("level", "?")
            return f"Brightness set to {level} percent."
        elif function_name in ("open_application", "open_app"):
            app = args.get("app_name", "")
            return f"Opening {app}."
        elif function_name == "close_application":
            app = args.get("app_name", "")
            return f"Closing {app}."
        elif function_name == "get_weather":
            city = args.get("city", "your location")
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    temp = data.get("temperature", "unknown")
                    conditions = data.get("conditions", "unknown")
                    return f"It is currently {temp} and {conditions} in {city}."
            except:
                pass
            return base_msg
        elif function_name == "get_battery_status":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    pct = data.get("percent", "?")
                    plug = "charging" if data.get("plugged") else "on battery"
                    return f"Battery is at {pct} percent, {plug}."
            except:
                pass
            return base_msg
        elif function_name == "get_system_summary":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    bat = data.get("battery", "N/A")
                    cpu = data.get("cpu_usage", "N/A")
                    ram = data.get("ram_usage", "N/A")
                    return f"System summary: Battery {bat}, CPU {cpu}, RAM {ram}."
            except:
                pass
            return base_msg
        elif function_name == "get_cpu_usage":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    usage = data.get("usage_percent", "?")
                    return f"CPU usage is {usage} percent."
            except:
                pass
            return base_msg
        elif function_name == "get_ram_usage":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    used = data.get("used_gb", "?")
                    total = data.get("total_gb", "?")
                    pct = data.get("percent_used", "?")
                    return f"RAM usage is {pct} percent, {used} gigs used out of {total} gigs."
            except:
                pass
            return base_msg
        elif function_name == "calculate":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    expr = data.get("expression", "")
                    res = data.get("result", "?")
                    return f"The result of {expr} is {res}."
            except:
                pass
            return base_msg
        elif function_name == "remember_fact":
            try:
                data = json.loads(result)
                return data.get("message", "I will remember that.")
            except:
                pass
            return base_msg
        elif function_name == "retrieve_memory":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    val = data.get("value", "")
                    return f"Yes, I remember that {data.get('item_name', 'it')} is {val}."
                return data.get("message", "I don't have that in memory.")
            except:
                pass
            return base_msg
        elif function_name == "get_current_datetime":
            try:
                data = json.loads(result)
                return f"It is {data.get('datetime', 'unknown')}."
            except:
                pass
            return base_msg
        elif function_name == "set_timer":
            try:
                data = json.loads(result)
                return data.get("message", "Timer set.")
            except:
                pass
            return base_msg
        elif function_name == "add_note":
            try:
                data = json.loads(result)
                return data.get("message", "Note saved.")
            except:
                pass
            return base_msg
        elif function_name == "list_notes":
            try:
                data = json.loads(result)
                count = data.get("count", 0)
                if count == 0:
                    return "You have no notes saved."
                return f"You have {count} notes saved."
            except:
                pass
            return base_msg
        elif function_name == "manage_file":
            try:
                data = json.loads(result)
                if "content" in data:
                    content = data["content"][:300]
                    return f"Here is the file content: {content}"
                return data.get("message", "File operation done.")
            except:
                pass
            return base_msg
        elif function_name == "get_recent_emails":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    count = data.get("count", 0)
                    return f"You have {count} recent emails."
            except:
                pass
            return base_msg
        elif function_name == "check_unread_emails":
            try:
                data = json.loads(result)
                return data.get("message", "Email check done.")
            except:
                pass
            return base_msg
        elif function_name == "open_website":
            try:
                data = json.loads(result)
                return data.get("message", "Website opened.")
            except:
                pass
            return base_msg
        elif function_name == "web_search":
            try:
                data = json.loads(result)
                return data.get("message", "Searching the web.")
            except:
                pass
            return base_msg
        elif function_name == "get_page_text":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    content = data.get("content", "")[:200]
                    return f"Here is what I found: {content}"
            except:
                pass
            return base_msg
        elif function_name == "download_file":
            try:
                data = json.loads(result)
                return data.get("message", "File downloaded.")
            except:
                pass
            return base_msg
        elif function_name == "search_files":
            try:
                data = json.loads(result)
                count = data.get("count", 0)
                if count == 0:
                    return "No files found matching that pattern."
                files = data.get("files", [])
                names = [f["name"] for f in files[:5]]
                return f"Found {count} files. Here are some: {', '.join(names)}"
            except:
                pass
            return base_msg
        elif function_name == "list_directory":
            try:
                data = json.loads(result)
                count = data.get("count", 0)
                return f"Directory has {count} items."
            except:
                pass
            return base_msg
        elif function_name == "create_folder":
            try:
                data = json.loads(result)
                return data.get("message", "Folder created.")
            except:
                pass
            return base_msg
        elif function_name == "delete_file":
            try:
                data = json.loads(result)
                return data.get("message", "File deleted.")
            except:
                pass
            return base_msg
        elif function_name == "set_reminder":
            try:
                data = json.loads(result)
                return data.get("message", "Reminder set.")
            except:
                pass
            return base_msg
        elif function_name == "set_alarm":
            try:
                data = json.loads(result)
                return data.get("message", "Alarm set.")
            except:
                pass
            return base_msg
        elif function_name == "list_reminders":
            try:
                data = json.loads(result)
                pending = data.get("pending", 0)
                if pending == 0:
                    return "You have no pending reminders."
                return f"You have {pending} pending reminders."
            except:
                pass
            return base_msg
        elif function_name == "cancel_reminder":
            try:
                data = json.loads(result)
                return data.get("message", "Reminder cancelled.")
            except:
                pass
            return base_msg
        elif function_name == "start_pomodoro":
            try:
                data = json.loads(result)
                return data.get("message", "Pomodoro started.")
            except:
                pass
            return base_msg
        elif function_name == "get_network_info":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    ip = data.get("ip_address", "unknown")
                    host = data.get("hostname", "unknown")
                    return f"Network info: IP is {ip}, hostname is {host}."
            except:
                pass
            return base_msg
        elif function_name == "list_running_apps":
            try:
                data = json.loads(result)
                count = data.get("count", 0)
                return f"There are {count} running processes."
            except:
                pass
            return base_msg
        elif function_name == "kill_process":
            try:
                data = json.loads(result)
                return data.get("message", "Process killed.")
            except:
                pass
            return base_msg
        elif function_name == "get_system_info":
            try:
                data = json.loads(result)
                if data.get("status") == "success":
                    os_name = data.get("os", "unknown")
                    cpu = data.get("cpu_percent", "?")
                    ram = data.get("ram_percent", "?")
                    return f"Running {os_name}. CPU at {cpu} percent, RAM at {ram} percent."
            except:
                pass
            return base_msg
        elif function_name == "ping_host":
            try:
                data = json.loads(result)
                host = data.get("host", "unknown")
                reachable = data.get("reachable", False)
                return f"{host} is {'reachable' if reachable else 'unreachable'}."
            except:
                pass
            return base_msg
        elif function_name == "get_installed_software":
            try:
                data = json.loads(result)
                count = data.get("count", 0)
                return f"Found {count} installed applications."
            except:
                pass
            return base_msg

        return base_msg

    def run_conversation(self, user_prompt: str) -> str:
        self.memory.save_message("user", user_prompt)
        messages = self._build_messages(user_prompt)

        try:
            tools_schema = self.registry.get_tools_schema()

            completion_kwargs = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 400
            }

            if tools_schema:
                completion_kwargs["tools"] = tools_schema
                completion_kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**completion_kwargs)
        except Exception as e:
            error_str = str(e)
            if "tool_use_failed" in error_str and "failed_generation" in error_str:
                try:
                    match = re.search(r"<function=(\w+)(?:.*?)(?=\{)(\{.*?\})<\/function>", error_str)
                    if match:
                        func_name = match.group(1)
                        func_args_str = match.group(2)
                        print(f"DEBUG: Recovered failed tool call: {func_name} with {func_args_str}")

                        function_to_call = self.registry.get_function(func_name)
                        if function_to_call:
                            try:
                                args = json.loads(func_args_str)
                                res = function_to_call(**args)
                                speak_text = self._get_tool_speak(func_name, args, str(res))
                                self.memory.save_message("assistant", speak_text, func_name)
                                return speak_text
                            except Exception as exec_e:
                                return f"Error executing recovered tool: {exec_e}"
                except Exception as parse_e:
                    print(f"Failed to recover tool call: {parse_e}")

            print(f"Groq API Error: {e}")
            return "I am having trouble connecting to the brain, sir."

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            print("DEBUG: Executing Tool...")
            messages.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                print(f"DEBUG: AI attempting to call: {function_name}")

                function_to_call = self.registry.get_function(function_name)

                if not function_to_call:
                    res = "Error: Tool not found."
                    print(f"DEBUG: Tool {function_name} not found in registry.")
                else:
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        print(f"DEBUG: Tool arguments: {function_args}")

                        if function_args is None:
                            function_args = {}

                        res = function_to_call(**function_args)
                        print(f"DEBUG: Tool Output: {str(res)[:100]}...")
                    except Exception as e:
                        res = f"Error executing tool: {e}"
                        print(f"DEBUG: Tool Execution Error: {e}")

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(res),
                    }
                )

            second_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=400
            )
            final_text = _strip_thinking(second_response.choices[0].message.content)
            self.memory.save_message("assistant", final_text, ",".join(tc.function.name for tc in tool_calls))
            return final_text

        else:
            final_text = _strip_thinking(response_message.content)
            self.memory.save_message("assistant", final_text)
            return final_text
