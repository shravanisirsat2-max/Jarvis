import json
import os
import subprocess
from typing import List, Dict, Any, Callable
from core.skill import Skill


class SmartHomeSkill(Skill):
    """Smart home and system automation - WiFi, Bluetooth, display, power management."""

    @property
    def name(self) -> str:
        return "smart_home"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "toggle_wifi",
                    "description": "Turn WiFi on or off.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {"type": "string", "description": "on or off"}
                        },
                        "required": ["state"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "toggle_bluetooth",
                    "description": "Turn Bluetooth on or off.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {"type": "string", "description": "on or off"}
                        },
                        "required": ["state"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_dark_mode",
                    "description": "Toggle Windows dark mode.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean", "description": "True for dark, False for light"}
                        },
                        "required": ["enabled"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_wallpaper",
                    "description": "Change desktop wallpaper to a file or URL.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Image file path or URL"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "toggle_airplane_mode",
                    "description": "Turn airplane mode on or off.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {"type": "string", "description": "on or off"}
                        },
                        "required": ["state"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_battery_health",
                    "description": "Get detailed battery health and charge cycle info.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot_ocr",
                    "description": "Take a screenshot and return file path.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clean_temp_files",
                    "description": "Clean temporary files from Windows temp folder.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "toggle_wifi": self.toggle_wifi,
            "toggle_bluetooth": self.toggle_bluetooth,
            "set_dark_mode": self.set_dark_mode,
            "set_wallpaper": self.set_wallpaper,
            "toggle_airplane_mode": self.toggle_airplane_mode,
            "get_battery_health": self.get_battery_health,
            "take_screenshot_ocr": self.take_screenshot_ocr,
            "clean_temp_files": self.clean_temp_files,
        }

    def _run_ps(self, command: str) -> str:
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True, text=True, timeout=15
            )
            return result.stdout.strip()
        except Exception as e:
            return str(e)

    def toggle_wifi(self, state: str) -> str:
        if state.lower() == "on":
            self._run_ps("netsh interface set interface 'Wi-Fi' admin=enable")
        else:
            self._run_ps("netsh interface set interface 'Wi-Fi' admin=disable")
        return json.dumps({"status": "success", "message": f"WiFi turned {state}"})

    def toggle_bluetooth(self, state: str) -> str:
        if state.lower() == "on":
            self._run_ps("(Get-PnpDevice -FriendlyName '*Bluetooth*').Status | ForEach-Object { Enable-PnpDevice -Confirm:$false }")
        else:
            self._run_ps("Get-PnpDevice -FriendlyName '*Bluetooth*' | Disable-PnpDevice -Confirm:$false")
        return json.dumps({"status": "success", "message": f"Bluetooth turned {state}"})

    def set_dark_mode(self, enabled: bool) -> str:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0 if enabled else 1)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 0 if enabled else 1)
            winreg.CloseKey(key)
            mode = "dark" if enabled else "light"
            return json.dumps({"status": "success", "message": f"Switched to {mode} mode"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def set_wallpaper(self, path: str) -> str:
        try:
            if path.startswith("http"):
                import requests
                from PIL import Image
                resp = requests.get(path, timeout=10)
                wallpaper_path = os.path.join(os.path.expanduser("~"), "Pictures", "jarvis_wallpaper.jpg")
                with open(wallpaper_path, "wb") as f:
                    f.write(resp.content)
                path = wallpaper_path
            import ctypes
            ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
            return json.dumps({"status": "success", "message": f"Wallpaper changed to {os.path.basename(path)}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def toggle_airplane_mode(self, state: str) -> str:
        if state.lower() == "on":
            self._run_ps("Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Disable-NetAdapter -Confirm:$false")
        else:
            self._run_ps("Get-NetAdapter | Where-Object {$_.Status -eq 'Disabled'} | Enable-NetAdapter -Confirm:$false")
        return json.dumps({"status": "success", "message": f"Airplane mode turned {state}"})

    def get_battery_health(self) -> str:
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                return json.dumps({
                    "status": "success",
                    "percent": battery.percent,
                    "plugged": battery.power_plugged,
                    "secs_left": battery.secsleft if battery.secsleft != -1 else "Calculating...",
                    "status_text": "Charging" if battery.power_plugged else "On Battery"
                })
            return json.dumps({"status": "error", "message": "No battery detected"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def take_screenshot_ocr(self) -> str:
        try:
            import pyautogui
            screenshot_path = os.path.join(os.path.expanduser("~"), "Pictures", "jarvis_screenshot.png")
            pyautogui.screenshot(screenshot_path)
            return json.dumps({"status": "success", "path": screenshot_path, "message": f"Screenshot saved to {screenshot_path}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def clean_temp_files(self) -> str:
        try:
            temp_dir = os.environ.get("TEMP", "C:\\Windows\\Temp")
            count = 0
            for item in os.listdir(temp_dir):
                try:
                    path = os.path.join(temp_dir, item)
                    if os.path.isfile(path):
                        os.remove(path)
                        count += 1
                    elif os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path, ignore_errors=True)
                        count += 1
                except:
                    pass
            return json.dumps({"status": "success", "message": f"Cleaned {count} temporary files/folders"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
