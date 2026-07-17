import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any, Callable
from core.skill import Skill

class ScreenshotSkill(Skill):
    """Skill for taking screenshots (cross-platform)."""
    
    def __init__(self):
        self.screenshot_dir = os.path.expanduser("~/Desktop/JARVIC_Screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    @property
    def name(self) -> str:
        return "screenshot_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot",
                    "description": "Take a screenshot of the entire screen and save it to a file. Returns the path to the saved screenshot.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Optional custom filename for the screenshot (without extension). If not provided, uses timestamp."
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "take_screenshot": self.take_screenshot
        }

    def take_screenshot(self, filename: str = None) -> str:
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}"
            
            if not filename.endswith('.png'):
                filename += '.png'
            
            filepath = os.path.join(self.screenshot_dir, filename)
            
            if sys.platform == "win32":
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(filepath)
            elif sys.platform == "darwin":
                result = os.system(f"screencapture -x '{filepath}'")
                if result != 0:
                    return json.dumps({"status": "error", "message": "Failed to capture screenshot"})
            else:
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(filepath)
            
            if os.path.exists(filepath):
                return json.dumps({
                    "status": "success",
                    "message": "Screenshot saved successfully",
                    "path": filepath
                })
            else:
                return json.dumps({"status": "error", "message": "Failed to capture screenshot"})
                
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Screenshot error: {str(e)}"})
