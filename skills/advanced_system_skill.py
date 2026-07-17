import json
import os
import platform
import socket
from typing import List, Dict, Any, Callable
from core.skill import Skill


class AdvancedSystemSkill(Skill):
    """Advanced system info: network, processes, running apps, and detailed diagnostics."""

    @property
    def name(self) -> str:
        return "advanced_system"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_network_info",
                    "description": "Get network status: IP, hostname, connection info.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_running_apps",
                    "description": "List currently running applications/processes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "Optional filter for process name (e.g., 'chrome', 'code')"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "kill_process",
                    "description": "Kill a running process by name or PID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Process name (e.g., 'notepad') or PID"
                            }
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_info",
                    "description": "Get detailed system information: OS, CPU, RAM, Python version.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ping_host",
                    "description": "Ping a host to check connectivity.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "host": {
                                "type": "string",
                                "description": "Host to ping (e.g., 'google.com', '8.8.8.8')"
                            }
                        },
                        "required": ["host"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_installed_software",
                    "description": "List installed software on Windows.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "Optional filter to search software names"
                            }
                        }
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "get_network_info": self.get_network_info,
            "list_running_apps": self.list_running_apps,
            "kill_process": self.kill_process,
            "get_system_info": self.get_system_info,
            "ping_host": self.ping_host,
            "get_installed_software": self.get_installed_software,
        }

    def get_network_info(self) -> str:
        try:
            hostname = socket.gethostname()
            try:
                ip = socket.gethostbyname(hostname)
            except:
                ip = "Unable to determine"
            return json.dumps({
                "status": "success",
                "hostname": hostname,
                "ip_address": ip,
                "platform": platform.system(),
                "platform_version": platform.version()
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def list_running_apps(self, filter: str = None) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=10
            )
            processes = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.strip('"').split('","')
                if len(parts) >= 5:
                    name = parts[0]
                    pid = parts[1]
                    mem = parts[4]
                    if filter and filter.lower() not in name.lower():
                        continue
                    processes.append({"name": name, "pid": pid, "memory": mem})
            return json.dumps({"status": "success", "count": len(processes), "processes": processes[:30]})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def kill_process(self, name: str) -> str:
        try:
            import subprocess
            if name.isdigit():
                subprocess.run(["taskkill", "/PID", name, "/F"], capture_output=True, timeout=5)
            else:
                subprocess.run(["taskkill", "/IM", f"{name}.exe", "/F"], capture_output=True, timeout=5)
            return json.dumps({"status": "success", "message": f"Killed process: {name}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_system_info(self) -> str:
        try:
            import psutil
            info = {
                "status": "success",
                "os": platform.system(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "ram_percent": psutil.virtual_memory().percent,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M"),
            }
            return json.dumps(info)
        except ImportError:
            info = {
                "status": "success",
                "os": platform.system(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
            }
            return json.dumps(info)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def ping_host(self, host: str) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["ping", "-n", "4", host],
                capture_output=True, text=True, timeout=15
            )
            success = result.returncode == 0
            return json.dumps({
                "status": "success",
                "host": host,
                "reachable": success,
                "output": result.stdout[:500] if success else "Host unreachable"
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_installed_software(self, filter: str = None) -> str:
        try:
            import winreg
            software = []
            paths = [
                winreg.HKEY_LOCAL_MACHINE,
                winreg.HKEY_CURRENT_USER
            ]
            for root_key in paths:
                for subkey_path in [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                                     r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]:
                    try:
                        key = winreg.OpenKey(root_key, subkey_path)
                        i = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if filter and filter.lower() not in display_name.lower():
                                        i += 1
                                        continue
                                    software.append(display_name)
                                except:
                                    pass
                                winreg.CloseKey(subkey)
                            except OSError:
                                break
                            i += 1
                        winreg.CloseKey(key)
                    except:
                        pass
            software = sorted(set(software))
            return json.dumps({"status": "success", "count": len(software), "software": software[:50]})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})


from datetime import datetime
