import os
import sys
import json
import psutil
from typing import List, Dict, Any, Callable
from core.skill import Skill

class SystemInfoSkill(Skill):
    """Skill for getting system information (battery, CPU, RAM, disk)."""

    @property
    def name(self) -> str:
        return "system_info_skill"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_battery_status",
                    "description": "Get battery percentage and charging status",
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
                    "name": "get_cpu_usage",
                    "description": "Get current CPU usage percentage",
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
                    "name": "get_ram_usage",
                    "description": "Get RAM usage (total, used, available)",
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
                    "name": "get_disk_info",
                    "description": "Get disk space information for all drives",
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
                    "name": "get_system_summary",
                    "description": "Get a complete system summary (battery, CPU, RAM, disk)",
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
            "get_battery_status": self.get_battery_status,
            "get_cpu_usage": self.get_cpu_usage,
            "get_ram_usage": self.get_ram_usage,
            "get_disk_info": self.get_disk_info,
            "get_system_summary": self.get_system_summary
        }

    def get_battery_status(self) -> str:
        try:
            battery = psutil.sensors_battery()
            if battery:
                return json.dumps({
                    "status": "success",
                    "percent": battery.percent,
                    "plugged": battery.power_plugged,
                    "status": "Charging" if battery.power_plugged else "On Battery"
                })
            else:
                return json.dumps({"status": "error", "message": "No battery detected"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_cpu_usage(self) -> str:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            return json.dumps({
                "status": "success",
                "usage_percent": cpu_percent,
                "cores": cpu_count,
                "frequency_mhz": f"{cpu_freq.current:.0f}" if cpu_freq else "N/A"
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_ram_usage(self) -> str:
        try:
            ram = psutil.virtual_memory()
            return json.dumps({
                "status": "success",
                "total_gb": f"{ram.total / (1024**3):.1f}",
                "used_gb": f"{ram.used / (1024**3):.1f}",
                "available_gb": f"{ram.available / (1024**3):.1f}",
                "percent_used": ram.percent
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_disk_info(self) -> str:
        try:
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "total_gb": f"{usage.total / (1024**3):.1f}",
                        "used_gb": f"{usage.used / (1024**3):.1f}",
                        "free_gb": f"{usage.free / (1024**3):.1f}",
                        "percent_used": usage.percent
                    })
                except PermissionError:
                    continue
            return json.dumps({"status": "success", "disks": disks})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_system_summary(self) -> str:
        try:
            battery = psutil.sensors_battery()
            ram = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.5)

            summary = {
                "status": "success",
                "battery": f"{battery.percent}% ({'Charging' if battery.power_plugged else 'On Battery'})" if battery else "No battery",
                "cpu_usage": f"{cpu}%",
                "ram_usage": f"{ram.percent}% ({ram.used / (1024**3):.1f}GB / {ram.total / (1024**3):.1f}GB)",
                "platform": sys.platform
            }
            return json.dumps(summary)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
