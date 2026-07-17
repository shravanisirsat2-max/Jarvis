import json
import os
import glob as globmod
from typing import List, Dict, Any, Callable
from core.skill import Skill


class FileSearchSkill(Skill):
    """Advanced file search and management across the system."""

    @property
    def name(self) -> str:
        return "file_search"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_files",
                    "description": "Search for files by name pattern across common directories.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "File name pattern (e.g., '*.pdf', 'report*', '*.mp4')"
                            },
                            "location": {
                                "type": "string",
                                "description": "Directory to search in (default: home directory). Use 'desktop', 'documents', 'downloads', or full path."
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_disk_usage",
                    "description": "Check disk space usage for all drives.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "List contents of a directory with file sizes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path. Use 'desktop', 'documents', 'downloads', or full path."
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_folder",
                    "description": "Create a new folder.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Folder name or full path"
                            }
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "Delete a file or empty folder. Moves to recycle bin on Windows.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Full path to the file or folder to delete"
                            }
                        },
                        "required": ["path"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "search_files": self.search_files,
            "get_disk_usage": self.get_disk_usage,
            "list_directory": self.list_directory,
            "create_folder": self.create_folder,
            "delete_file": self.delete_file,
        }

    def _resolve_path(self, location: str) -> str:
        home = os.path.expanduser("~")
        shortcuts = {
            "desktop": os.path.join(home, "Desktop"),
            "documents": os.path.join(home, "Documents"),
            "downloads": os.path.join(home, "Downloads"),
            "home": home,
            "pictures": os.path.join(home, "Pictures"),
            "music": os.path.join(home, "Music"),
            "videos": os.path.join(home, "Videos"),
        }
        return shortcuts.get(location.lower(), location)

    def search_files(self, pattern: str, location: str = "home") -> str:
        try:
            search_dir = self._resolve_path(location)
            if not os.path.exists(search_dir):
                return json.dumps({"status": "error", "message": f"Directory not found: {search_dir}"})
            matches = []
            for root, dirs, files in os.walk(search_dir):
                dirs[:] = [d for d in dirs if d not in ["AppData", ".git", "__pycache__", "node_modules", ".cache"]]
                import fnmatch
                for fname in files:
                    if fnmatch.fnmatch(fname.lower(), pattern.lower()):
                        fpath = os.path.join(root, fname)
                        size = os.path.getsize(fpath)
                        matches.append({"name": fname, "path": fpath, "size_mb": round(size / (1024*1024), 2)})
                        if len(matches) >= 20:
                            break
                if len(matches) >= 20:
                    break
            return json.dumps({"status": "success", "count": len(matches), "files": matches})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_disk_usage(self) -> str:
        try:
            import string
            drives = []
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    total, used, free = os.statvfs(drive) if sys.platform != "win32" else (0, 0, 0)
                    if sys.platform == "win32":
                        import ctypes
                        free_bytes = ctypes.c_ulonglong(0)
                        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(drive), None, None, ctypes.pointer(free_bytes))
                        total_bytes = ctypes.c_ulonglong(0)
                        sectors = ctypes.c_ulonglong(0)
                        ctypes.windll.kernel32.GetDiskSpaceExW(ctypes.c_wchar_p(drive), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes))
                        drives.append({
                            "drive": drive,
                            "total_gb": round(total_bytes.value / (1024**3), 2),
                            "free_gb": round(free_bytes.value / (1024**3), 2)
                        })
            return json.dumps({"status": "success", "drives": drives})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def list_directory(self, path: str) -> str:
        try:
            resolved = self._resolve_path(path)
            if not os.path.exists(resolved):
                return json.dumps({"status": "error", "message": f"Directory not found: {resolved}"})
            items = []
            for item in sorted(os.listdir(resolved)):
                item_path = os.path.join(resolved, item)
                is_dir = os.path.isdir(item_path)
                size = 0 if is_dir else os.path.getsize(item_path)
                items.append({
                    "name": item,
                    "type": "folder" if is_dir else "file",
                    "size_mb": round(size / (1024*1024), 2)
                })
            return json.dumps({"status": "success", "path": resolved, "count": len(items), "items": items[:50]})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def create_folder(self, name: str) -> str:
        try:
            if not os.path.isabs(name):
                name = os.path.join(os.path.expanduser("~"), "Desktop", name)
            os.makedirs(name, exist_ok=True)
            return json.dumps({"status": "success", "message": f"Created folder: {name}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def delete_file(self, path: str) -> str:
        try:
            if sys.platform == "win32":
                import send2trash
                send2trash.send2trash(path)
            else:
                if os.path.isdir(path):
                    os.rmdir(path)
                else:
                    os.remove(path)
            return json.dumps({"status": "success", "message": f"Deleted: {path}"})
        except ImportError:
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)
            return json.dumps({"status": "success", "message": f"Deleted: {path}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})


import sys
