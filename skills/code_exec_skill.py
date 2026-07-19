import json
import os
import sys
import io
import contextlib
import traceback
import threading
from typing import List, Dict, Any, Callable
from core.skill import Skill


class CodeExecSkill(Skill):
    """Safe Python code execution in a sandboxed environment."""

    @property
    def name(self) -> str:
        return "code_exec"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_python",
                    "description": "Execute Python code and return the output. Use for calculations, data processing, text manipulation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute"
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_shell_command",
                    "description": "Execute a Windows shell command and return output.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute (e.g., 'dir', 'ipconfig', 'echo hello')"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "evaluate_math",
                    "description": "Evaluate a complex math expression with full Python math support.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Math expression (e.g., 'math.sqrt(144) + 3**2', 'sum(range(100))')"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "convert_units",
                    "description": "Convert between units (length, weight, temperature, data).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "number", "description": "Value to convert"},
                            "from_unit": {"type": "string", "description": "Source unit (e.g., 'km', 'miles', 'kg', 'celsius', 'gb')"},
                            "to_unit": {"type": "string", "description": "Target unit"}
                        },
                        "required": ["value", "from_unit", "to_unit"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "run_python": self.run_python,
            "run_shell_command": self.run_shell_command,
            "evaluate_math": self.evaluate_math,
            "convert_units": self.convert_units,
        }

    def run_python(self, code: str) -> str:
        try:
            safe_builtins = {
                "print": print, "len": len, "range": range, "int": int,
                "float": float, "str": str, "list": list, "dict": dict,
                "set": set, "tuple": tuple, "bool": bool, "abs": abs,
                "max": max, "min": min, "sum": sum, "sorted": sorted,
                "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
                "round": round, "type": type, "isinstance": isinstance,
                "True": True, "False": False, "None": None,
                "__import__": __import__,
            }
            output_buffer = io.StringIO()
            local_vars = {"__builtins__": safe_builtins}
            with contextlib.redirect_stdout(output_buffer):
                exec(code, local_vars)
            output = output_buffer.getvalue()
            if not output:
                output = "Code executed successfully (no output)."
            return json.dumps({"status": "success", "output": output[:2000]})
        except Exception as e:
            return json.dumps({"status": "error", "output": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()[:500]})

    def run_shell_command(self, command: str) -> str:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            if not output.strip():
                output = "Command executed successfully (no output)."
            return json.dumps({"status": "success", "output": output[:2000], "return_code": result.returncode})
        except subprocess.TimeoutExpired:
            return json.dumps({"status": "error", "output": "Command timed out after 30 seconds"})
        except Exception as e:
            return json.dumps({"status": "error", "output": str(e)})

    def evaluate_math(self, expression: str) -> str:
        try:
            import math
            safe_dict = {
                "math": math, "abs": abs, "round": round,
                "min": min, "max": max, "sum": sum, "pow": pow,
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "pi": math.pi, "e": math.e, "ceil": math.ceil, "floor": math.floor,
                "factorial": math.factorial, "gcd": math.gcd,
            }
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return json.dumps({"status": "success", "expression": expression, "result": result})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Math error: {e}"})

    def convert_units(self, value: float, from_unit: str, to_unit: str) -> str:
        conversions = {
            ("km", "miles"): lambda x: x * 0.621371,
            ("miles", "km"): lambda x: x * 1.60934,
            ("m", "feet"): lambda x: x * 3.28084,
            ("feet", "m"): lambda x: x * 0.3048,
            ("cm", "inches"): lambda x: x * 0.393701,
            ("inches", "cm"): lambda x: x * 2.54,
            ("kg", "lbs"): lambda x: x * 2.20462,
            ("lbs", "kg"): lambda x: x * 0.453592,
            ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
            ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
            ("celsius", "kelvin"): lambda x: x + 273.15,
            ("kelvin", "celsius"): lambda x: x - 273.15,
            ("gb", "mb"): lambda x: x * 1024,
            ("mb", "gb"): lambda x: x / 1024,
            ("gb", "tb"): lambda x: x / 1024,
            ("tb", "gb"): lambda x: x * 1024,
            ("mb", "kb"): lambda x: x * 1024,
            ("kb", "mb"): lambda x: x / 1024,
            ("hours", "minutes"): lambda x: x * 60,
            ("minutes", "hours"): lambda x: x / 60,
            ("minutes", "seconds"): lambda x: x * 60,
            ("seconds", "minutes"): lambda x: x / 60,
        }
        key = (from_unit.lower(), to_unit.lower())
        if key in conversions:
            result = conversions[key](value)
            return json.dumps({"status": "success", "from": f"{value} {from_unit}", "to": f"{round(result, 4)} {to_unit}"})
        return json.dumps({"status": "error", "message": f"Unknown conversion: {from_unit} to {to_unit}"})
