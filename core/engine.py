import os
import json
import re
from groq import Groq
from core.registry import SkillRegistry

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
}

class JarvisEngine:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model_name = "qwen/qwen3-32b"

        self.system_instruction = (
            "You are Jarvis, an intelligent, polite, and helpful AI assistant. "
            "You speak concisely and naturally, like a human assistant. "
            "When you use a tool to complete a task, give a short spoken confirmation "
            "of what you did. For example: 'Done, I have opened Spotify for you.' or "
            "'Screenshot saved to your Desktop.' or 'Volume is now at 50 percent.' "
            "Keep responses under 2 sentences. Be conversational but brief."
        )

    def _get_tool_speak(self, function_name, args, result):
        base_msg = TOOL_RESPONSE_MAP.get(function_name, "Task completed.")

        if function_name == "set_volume":
            level = args.get("level", "?")
            return f"Volume set to {level} percent."
        elif function_name == "set_brightness":
            level = args.get("level", "?")
            return f"Brightness set to {level} percent."
        elif function_name == "open_application" or function_name == "open_app":
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

        return base_msg

    def run_conversation(self, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": self.system_instruction},
            {"role": "user", "content": user_prompt}
        ]

        try:
            tools_schema = self.registry.get_tools_schema()

            completion_kwargs = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 300
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
                max_tokens=300
            )
            return _strip_thinking(second_response.choices[0].message.content)

        else:
            return _strip_thinking(response_message.content)
