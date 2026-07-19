import json
import os
import sys
import subprocess
import tempfile
import pyautogui
from typing import List, Dict, Any, Callable
from core.skill import Skill


class ScreenOCRSkill(Skill):
    """Screen OCR - read text from any screenshot using Tesseract."""

    @property
    def name(self) -> str:
        return "screen_ocr"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_screen_text",
                    "description": "Capture screenshot and read all visible text from it using OCR.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "region": {
                                "type": "string",
                                "description": "Optional region: 'full' (default), 'center', 'top', 'bottom', or coordinates 'x,y,w,h'"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_screen_region",
                    "description": "Read text from a specific region of the screen.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number", "description": "X coordinate"},
                            "y": {"type": "number", "description": "Y coordinate"},
                            "width": {"type": "number", "description": "Width"},
                            "height": {"type": "number", "description": "Height"}
                        },
                        "required": ["x", "y", "width", "height"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_text_on_screen",
                    "description": "Find if specific text is visible on screen and where it is.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to search for on screen"
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_screen_color",
                    "description": "Get the color of a pixel at specific screen coordinates.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number", "description": "X coordinate"},
                            "y": {"type": "number", "description": "Y coordinate"}
                        },
                        "required": ["x", "y"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "read_screen_text": self.read_screen_text,
            "read_screen_region": self.read_screen_region,
            "find_text_on_screen": self.find_text_on_screen,
            "get_screen_color": self.get_screen_color,
        }

    def _check_tesseract(self):
        try:
            import pytesseract
            if os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
                pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            elif os.path.exists(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
                pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
            return True
        except ImportError:
            return False

    def _screenshot_to_text(self, region=None):
        import pytesseract
        from PIL import Image
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        text = pytesseract.image_to_string(screenshot)
        return text.strip()

    def read_screen_text(self, region: str = "full") -> str:
        try:
            if not self._check_tesseract():
                return json.dumps({"status": "error", "message": "Tesseract OCR not installed. Install from https://github.com/UB-Mannheim/tesseract/wiki"})
            r = None
            if region == "center":
                w, h = pyautogui.size()
                r = (w//4, h//4, w//2, h//2)
            elif region == "top":
                w, h = pyautogui.size()
                r = (0, 0, w, h//3)
            elif region == "bottom":
                w, h = pyautogui.size()
                r = (0, h*2//3, w, h//3)
            elif "," in region:
                parts = [int(x.strip()) for x in region.split(",")]
                r = tuple(parts)
            text = self._screenshot_to_text(region=r)
            if not text:
                return json.dumps({"status": "success", "message": "No text detected on screen", "text": ""})
            return json.dumps({"status": "success", "text": text[:3000], "length": len(text)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def read_screen_region(self, x: int, y: int, width: int, height: int) -> str:
        try:
            if not self._check_tesseract():
                return json.dumps({"status": "error", "message": "Tesseract OCR not installed"})
            text = self._screenshot_to_text(region=(x, y, width, height))
            return json.dumps({"status": "success", "text": text[:3000], "length": len(text)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def find_text_on_screen(self, text: str) -> str:
        try:
            if not self._check_tesseract():
                return json.dumps({"status": "error", "message": "Tesseract OCR not installed"})
            import pytesseract
            from PIL import Image
            screenshot = pyautogui.screenshot()
            data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
            found_positions = []
            for i, word in enumerate(data["text"]):
                if text.lower() in word.lower():
                    found_positions.append({
                        "text": word,
                        "x": data["left"][i],
                        "y": data["top"][i],
                        "width": data["width"][i],
                        "height": data["height"][i]
                    })
            if found_positions:
                return json.dumps({"status": "success", "found": True, "positions": found_positions[:5]})
            return json.dumps({"status": "success", "found": False, "message": f"Text '{text}' not found on screen"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_screen_color(self, x: int, y: int) -> str:
        try:
            screenshot = pyautogui.screenshot()
            pixel = screenshot.getpixel((x, y))
            hex_color = "#{:02x}{:02x}{:02x}".format(pixel[0], pixel[1], pixel[2])
            return json.dumps({"status": "success", "rgb": list(pixel), "hex": hex_color, "x": x, "y": y})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
