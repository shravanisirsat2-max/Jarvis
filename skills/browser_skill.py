import json
import os
import sys
from typing import List, Dict, Any, Callable
from core.skill import Skill


class BrowserSkill(Skill):
    """Browser automation using Selenium for web control."""

    @property
    def name(self) -> str:
        return "browser"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "open_website",
                    "description": "Open a website in the browser. Handles URLs with or without http prefix.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The website URL or domain to open (e.g., 'google.com', 'https://youtube.com')"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web using Google and return top results.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_page_text",
                    "description": "Get the text content of a webpage.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to fetch text from"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "download_file",
                    "description": "Download a file from a URL.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "Direct download URL"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Save as filename (optional)"
                            }
                        },
                        "required": ["url"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "open_website": self.open_website,
            "web_search": self.web_search,
            "get_page_text": self.get_page_text,
            "download_file": self.download_file,
        }

    def open_website(self, url: str) -> str:
        try:
            import webbrowser
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return json.dumps({"status": "success", "message": f"Opened {url}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def web_search(self, query: str) -> str:
        try:
            import webbrowser
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            return json.dumps({"status": "success", "message": f"Searching for '{query}' in browser"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_page_text(self, url: str) -> str:
        try:
            import requests
            from bs4 import BeautifulSoup
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator="\n", strip=True)
            text = text[:2000]
            return json.dumps({"status": "success", "content": text, "url": url})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def download_file(self, url: str, filename: str = None) -> str:
        try:
            import requests
            if filename is None:
                filename = url.split("/")[-1].split("?")[0]
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            filepath = os.path.join(downloads, filename)
            resp = requests.get(url, stream=True, timeout=30)
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return json.dumps({"status": "success", "message": f"Downloaded to {filepath}", "path": filepath})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
