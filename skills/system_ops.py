import os
import sys
import json
import subprocess
from typing import List, Dict, Any, Callable
from core.skill import Skill

class SystemSkill(Skill):
    @property
    def name(self) -> str:
        return "system_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "set_volume",
                    "description": "Set system volume (0-100)",
                    "parameters": {"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_app",
                    "description": "Open an application on the computer",
                    "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_brightness",
                    "description": "Set screen brightness (0-100)",
                    "parameters": {"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "lock_screen",
                    "description": "Lock the computer screen",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "shutdown_pc",
                    "description": "Shutdown the computer",
                    "parameters": {"type": "object", "properties": {"delay": {"type": "integer", "description": "Seconds to wait before shutdown (default 0)"}}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "restart_pc",
                    "description": "Restart the computer",
                    "parameters": {"type": "object", "properties": {"delay": {"type": "integer", "description": "Seconds to wait before restart (default 0)"}}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "sleep_pc",
                    "description": "Put the computer to sleep",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "empty_recycle_bin",
                    "description": "Empty the recycle bin",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot",
                    "description": "Take a screenshot and save it",
                    "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": []}
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "set_volume": self.set_volume,
            "open_app": self.open_app,
            "set_brightness": self.set_brightness,
            "lock_screen": self.lock_screen,
            "shutdown_pc": self.shutdown_pc,
            "restart_pc": self.restart_pc,
            "sleep_pc": self.sleep_pc,
            "empty_recycle_bin": self.empty_recycle_bin,
            "take_screenshot": self.take_screenshot
        }

    def set_volume(self, level: int) -> str:
        try:
            if sys.platform == "win32":
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            elif sys.platform == "darwin":
                os.system(f"osascript -e 'set volume output volume {level}'")
            else:
                os.system(f"amixer sset 'Master' {level}%")
            return json.dumps({"status": "success", "level": level})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def open_app(self, app_name: str) -> str:
        try:
            if sys.platform == "win32":
                os.system(f'start "" "{app_name}"')
            elif sys.platform == "darwin":
                os.system(f"open -a '{app_name}'")
            else:
                os.system(f"{app_name} &")
            return json.dumps({"status": "success", "app": app_name})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def set_brightness(self, level: int) -> str:
        try:
            if sys.platform == "win32":
                powershell_cmd = f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})'
                subprocess.run(['powershell', '-Command', powershell_cmd], capture_output=True, timeout=10)
            elif sys.platform == "darwin":
                os.system(f"brightness {level / 100}")
            return json.dumps({"status": "success", "brightness": level})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def lock_screen(self) -> str:
        try:
            if sys.platform == "win32":
                os.system("rundll32.exe user32.dll,LockWorkStation")
            elif sys.platform == "darwin":
                os.system("pmset displaysleepnow")
            return json.dumps({"status": "success", "message": "Screen locked"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def shutdown_pc(self, delay: int = 0) -> str:
        try:
            if sys.platform == "win32":
                os.system(f"shutdown /s /t {delay}")
            elif sys.platform == "darwin":
                os.system(f"sudo shutdown -h +{delay // 60 if delay else 0}")
            return json.dumps({"status": "success", "message": f"Shutting down in {delay} seconds"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def restart_pc(self, delay: int = 0) -> str:
        try:
            if sys.platform == "win32":
                os.system(f"shutdown /r /t {delay}")
            elif sys.platform == "darwin":
                os.system(f"sudo shutdown -r +{delay // 60 if delay else 0}")
            return json.dumps({"status": "success", "message": f"Restarting in {delay} seconds"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def sleep_pc(self) -> str:
        try:
            if sys.platform == "win32":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif sys.platform == "darwin":
                os.system("pmset sleepnow")
            return json.dumps({"status": "success", "message": "Computer going to sleep"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def empty_recycle_bin(self) -> str:
        try:
            if sys.platform == "win32":
                os.system('Clear-RecycleBin -Force -ErrorAction SilentlyContinue')
            return json.dumps({"status": "success", "message": "Recycle bin emptied"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def take_screenshot(self, filename: str = None) -> str:
        try:
            from datetime import datetime
            screenshot_dir = os.path.expanduser("~/Desktop/JARVIC_Screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)

            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}"

            if not filename.endswith('.png'):
                filename += '.png'

            filepath = os.path.join(screenshot_dir, filename)

            if sys.platform == "win32":
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(filepath)
            elif sys.platform == "darwin":
                os.system(f"screencapture -x '{filepath}'")

            if os.path.exists(filepath):
                return json.dumps({"status": "success", "message": "Screenshot saved", "path": filepath})
            else:
                return json.dumps({"status": "error", "message": "Failed to capture screenshot"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
