import os
import sys
import json
import time
from typing import List, Dict, Any, Callable
from core.skill import Skill

class MediaControlSkill(Skill):
    """Skill for controlling media playback (play, pause, next, previous, volume)."""

    @property
    def name(self) -> str:
        return "media_control_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "media_play_pause",
                    "description": "Toggle play/pause for the current media",
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
                    "name": "media_next",
                    "description": "Skip to the next track",
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
                    "name": "media_previous",
                    "description": "Go to the previous track",
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
                    "name": "media_stop",
                    "description": "Stop media playback",
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
                    "name": "media_volume_up",
                    "description": "Increase system volume",
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
                    "name": "media_volume_down",
                    "description": "Decrease system volume",
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
                    "name": "media_mute",
                    "description": "Toggle mute/unmute",
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
            "media_play_pause": self.media_play_pause,
            "media_next": self.media_next,
            "media_previous": self.media_previous,
            "media_stop": self.media_stop,
            "media_volume_up": self.media_volume_up,
            "media_volume_down": self.media_volume_down,
            "media_mute": self.media_mute
        }

    def _send_key(self, key_code: int):
        if sys.platform == "win32":
            import ctypes
            SendInput = ctypes.windll.user32.SendInput
            PUL = ctypes.POINTER(ctypes.c_ulong)

            class KeyBdInput(ctypes.Structure):
                _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

            class HardwareInput(ctypes.Structure):
                _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short), ("wParamH", ctypes.c_ushort)]

            class MouseInput(ctypes.Structure):
                _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

            class Input_I(ctypes.Union):
                _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

            class Input(ctypes.Structure):
                _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

            extra = ctypes.c_ulong(0)
            ii_ = Input_I()
            ii_.ki = KeyBdInput(0, key_code, 0x0008, 0, ctypes.pointer(extra))
            x = Input(ctypes.c_ulong(1), ii_)
            SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

            time.sleep(0.05)

            ii_.ki = KeyBdInput(0, key_code, 0x0008 | 0x0002, 0, ctypes.pointer(extra))
            x = Input(ctypes.c_ulong(1), ii_)
            SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def media_play_pause(self) -> str:
        try:
            self._send_key(0xB3)
            return json.dumps({"status": "success", "message": "Toggled play/pause"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def media_next(self) -> str:
        try:
            self._send_key(0xB0)
            return json.dumps({"status": "success", "message": "Skipped to next track"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def media_previous(self) -> str:
        try:
            self._send_key(0xB1)
            return json.dumps({"status": "success", "message": "Went to previous track"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def media_stop(self) -> str:
        try:
            self._send_key(0xB2)
            return json.dumps({"status": "success", "message": "Stopped playback"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def media_volume_up(self) -> str:
        try:
            self._send_key(0xAF)
            return json.dumps({"status": "success", "message": "Volume up"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def media_volume_down(self) -> str:
        try:
            self._send_key(0xAE)
            return json.dumps({"status": "success", "message": "Volume down"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def media_mute(self) -> str:
        try:
            self._send_key(0xAD)
            return json.dumps({"status": "success", "message": "Toggled mute"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
