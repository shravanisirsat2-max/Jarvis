import os
import sys
import json
import subprocess
from typing import List, Dict, Any, Callable
from core.skill import Skill

class AppControlSkill(Skill):
    """Skill for opening, closing, and switching between applications on Windows."""

    @property
    def name(self) -> str:
        return "app_control_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description": "Open an application by name (e.g., 'notepad', 'chrome', 'calculator', 'spotify')",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Name of the application to open"
                            }
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "close_application",
                    "description": "Close a running application by name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Name of the application to close"
                            }
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "switch_window",
                    "description": "Switch to the next window of a specific application",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Name of the application to switch to"
                            }
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_running_apps",
                    "description": "List all currently running applications",
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
            "open_application": self.open_application,
            "close_application": self.close_application,
            "switch_window": self.switch_window,
            "list_running_apps": self.list_running_apps
        }

    def open_application(self, app_name: str) -> str:
        try:
            common_apps = {
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "paint": "mspaint.exe",
                "wordpad": "write.exe",
                "task manager": "taskmgr.exe",
                "file explorer": "explorer.exe",
                "command prompt": "cmd.exe",
                "powershell": "powershell.exe",
                "settings": "ms-settings:",
                "snipping tool": "snippingtool.exe",
                "camera": "microsoft.windows.camera:",
                "edge": "msedge",
                "chrome": "chrome",
                "firefox": "firefox",
                "vscode": "code",
                "spotify": "spotify",
                "discord": "discord",
                "slack": "slack",
                "zoom": "zoom",
                "teams": "teams",
            }

            app_lower = app_name.lower().strip()

            if app_lower in common_apps:
                cmd = common_apps[app_lower]
            else:
                cmd = app_name

            if sys.platform == "win32":
                os.system(f'start "" "{cmd}"')
            else:
                os.system(f"{cmd} &")

            return json.dumps({"status": "success", "message": f"Opened {app_name}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Failed to open {app_name}: {str(e)}"})

    def close_application(self, app_name: str) -> str:
        try:
            process_names = {
                "notepad": "notepad",
                "calculator": "Calculator",
                "chrome": "chrome",
                "firefox": "firefox",
                "edge": "msedge",
                "vscode": "Code",
                "spotify": "Spotify",
                "discord": "Discord",
                "word": "WINWORD",
                "excel": "EXCEL",
                "powerpoint": "POWERPNT",
                "teams": "Teams",
                "zoom": "Zoom",
            }

            app_lower = app_name.lower().strip()
            process_name = process_names.get(app_lower, app_name)

            if sys.platform == "win32":
                os.system(f'taskkill /IM {process_name}.exe /F')
            else:
                os.system(f"pkill -f {app_name}")

            return json.dumps({"status": "success", "message": f"Closed {app_name}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Failed to close {app_name}: {str(e)}"})

    def switch_window(self, app_name: str) -> str:
        try:
            if sys.platform == "win32":
                import pygetwindow as gw
                windows = gw.getWindowsWithTitle(app_name)
                if windows:
                    win = windows[0]
                    if win.isMinimized:
                        win.restore()
                    win.activate()
                    return json.dumps({"status": "success", "message": f"Switched to {app_name}"})
                else:
                    return json.dumps({"status": "error", "message": f"No window found for {app_name}"})
            else:
                return json.dumps({"status": "error", "message": "Window switching not supported on this platform"})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Failed to switch: {str(e)}"})

    def list_running_apps(self) -> str:
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ['tasklist', '/FO', 'CSV', '/NH'],
                    capture_output=True, text=True, timeout=10
                )
                lines = result.stdout.strip().split('\n')
                apps = set()
                for line in lines:
                    parts = line.strip().split('","')
                    if len(parts) > 0:
                        name = parts[0].strip('"').replace('.exe', '')
                        apps.add(name)

                app_list = sorted(list(apps))
                return json.dumps({
                    "status": "success",
                    "count": len(app_list),
                    "apps": app_list[:30]
                })
            else:
                return json.dumps({"status": "error", "message": "Not supported on this platform"})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Failed to list apps: {str(e)}"})
