import json
import re
from typing import List, Dict, Any, Callable
from core.skill import Skill


class MultiLanguageSkill(Skill):
    """Multi-language support - translate, detect language, multilingual chat."""

    @property
    def name(self) -> str:
        return "multi_language"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "translate_text",
                    "description": "Translate text between languages using Google Translate.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to translate"},
                            "target_lang": {"type": "string", "description": "Target language code (e.g., 'hi' for Hindi, 'mr' for Marathi, 'es' for Spanish, 'fr' for French)"},
                            "source_lang": {"type": "string", "description": "Source language code (auto-detect if not provided)"}
                        },
                        "required": ["text", "target_lang"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_language",
                    "description": "Detect the language of given text.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to detect language for"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "multilingual_search",
                    "description": "Search Google in a specific language.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "language": {"type": "string", "description": "Language code for search results (e.g., 'hi', 'en', 'es')"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_language_list",
                    "description": "Get list of supported languages.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable]:
        return {
            "translate_text": self.translate_text,
            "detect_language": self.detect_language,
            "multilingual_search": self.multilingual_search,
            "get_language_list": self.get_language_list,
        }

    LANGUAGES = {
        "hi": "Hindi", "mr": "Marathi", "en": "English", "es": "Spanish",
        "fr": "French", "de": "German", "it": "Italian", "pt": "Portuguese",
        "ru": "Russian", "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
        "ar": "Arabic", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
        "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi",
        "ur": "Urdu", "th": "Thai", "vi": "Vietnamese", "tr": "Turkish",
        "nl": "Dutch", "sv": "Swedish", "pl": "Polish", "cs": "Czech",
        "el": "Greek", "he": "Hebrew", "id": "Indonesian", "ms": "Malay",
        "tl": "Filipino", "sw": "Swahili", "uk": "Ukrainian", "ro": "Romanian",
        "hu": "Hungarian", "fi": "Finnish", "no": "Norwegian", "da": "Danish",
    }

    def translate_text(self, text: str, target_lang: str, source_lang: str = None) -> str:
        try:
            import requests
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": source_lang or "auto",
                "tl": target_lang,
                "dt": "t",
                "q": text
            }
            resp = requests.get(url, params=params, timeout=10)
            result = resp.json()
            translated = "".join([sentence[0] for sentence in result[0] if sentence[0]])
            detected_lang = result[2] if len(result) > 2 else "unknown"
            lang_name = self.LANGUAGES.get(detected_lang, detected_lang)
            target_name = self.LANGUAGES.get(target_lang, target_lang)
            return json.dumps({
                "status": "success",
                "original": text,
                "translated": translated,
                "source_lang": lang_name,
                "target_lang": target_name
            })
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def detect_language(self, text: str) -> str:
        try:
            import requests
            url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text}
            resp = requests.get(url, params=params, timeout=10)
            result = resp.json()
            detected = result[2] if len(result) > 2 else "unknown"
            lang_name = self.LANGUAGES.get(detected, detected)
            return json.dumps({"status": "success", "detected_language": lang_name, "language_code": detected})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def multilingual_search(self, query: str, language: str = "en") -> str:
        try:
            import webbrowser
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&hl={language}"
            webbrowser.open(search_url)
            lang_name = self.LANGUAGES.get(language, language)
            return json.dumps({"status": "success", "message": f"Searching in {lang_name}: {query}"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def get_language_list(self) -> str:
        langs = [{"code": k, "name": v} for k, v in self.LANGUAGES.items()]
        return json.dumps({"status": "success", "count": len(langs), "languages": langs})
