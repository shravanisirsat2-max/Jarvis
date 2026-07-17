import os
import sys
import json
from typing import List, Dict, Any, Callable
from core.skill import Skill

class ClipboardSkill(Skill):
    """Skill for clipboard operations (copy, paste, clear)."""

    @property
    def name(self) -> str:
        return "clipboard_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "clipboard_copy",
                    "description": "Copy text to clipboard",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to copy to clipboard"
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clipboard_paste",
                    "description": "Get the current clipboard content",
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
                    "name": "clipboard_clear",
                    "description": "Clear the clipboard",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "clipboard_copy": self.clipboard_copy,
            "clipboard_paste": self.clipboard_paste,
            "clipboard_clear": self.clipboard_clear
        }

    def clipboard_copy(self, text: str) -> str:
        try:
            if sys.platform == "win32":
                import subprocess
                process = subprocess.Popen('clip', stdin=subprocess.PIPE, shell=True)
                process.communicate(text.encode('utf-16le'))
            else:
                import pyperclip
                pyperclip.copy(text)
            return json.dumps({"status": "success", "message": "Copied to clipboard"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def clipboard_paste(self) -> str:
        try:
            if sys.platform == "win32":
                import subprocess
                result = subprocess.run(
                    ['powershell', '-command', 'Get-Clipboard'],
                    capture_output=True, text=True, timeout=5
                )
                content = result.stdout.strip()
            else:
                import pyperclip
                content = pyperclip.paste()
            return json.dumps({"status": "success", "content": content})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def clipboard_clear(self) -> str:
        try:
            if sys.platform == "win32":
                import subprocess
                subprocess.run(
                    ['powershell', '-command', 'Set-Clipboard -Value $null'],
                    capture_output=True, timeout=5
                )
            else:
                import pyperclip
                pyperclip.copy('')
            return json.dumps({"status": "success", "message": "Clipboard cleared"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
