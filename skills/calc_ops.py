import json
import math
from typing import List, Dict, Any, Callable
from core.skill import Skill

class CalculatorSkill(Skill):
    """Skill for performing mathematical calculations."""

    @property
    def name(self) -> str:
        return "calculator_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Perform a mathematical calculation (e.g., '2+2', 'sqrt(16)', 'sin(3.14)', '10**3')",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Mathematical expression to evaluate"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "calculate": self.calculate
        }

    def calculate(self, expression: str) -> str:
        try:
            allowed_names = {
                'abs': abs, 'round': round, 'min': min, 'max': max,
                'sum': sum, 'pow': pow, 'int': int, 'float': float,
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
                'pi': math.pi, 'e': math.e, 'ceil': math.ceil, 'floor': math.floor,
                'factorial': math.factorial, 'gcd': math.gcd,
            }

            result = eval(expression, {"__builtins__": {}}, allowed_names)

            if isinstance(result, float) and result == int(result):
                result = int(result)

            return json.dumps({
                "status": "success",
                "expression": expression,
                "result": result
            })
        except ZeroDivisionError:
            return json.dumps({"status": "error", "message": "Division by zero"})
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Calculation error: {str(e)}"})
