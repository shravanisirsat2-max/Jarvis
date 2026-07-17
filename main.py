import os
import sys
import argparse
import threading
import time
from dotenv import load_dotenv
from core.voice import speak, speak_sync, listen
from core.registry import SkillRegistry
from core.engine import JarvisEngine
from gui.app import run_gui as run_gui_app

load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    print("Error: GROQ_API_KEY not found.")
    sys.exit(1)


def jarvis_loop(pause_event, registry, args):
    jarvis = JarvisEngine(registry)

    if args.text:
        print("JARVIS: Jarvis Online. Ready for command (Text Mode).")
    else:
        speak("Jarvis Online. Ready for command.")

    wake_word_active = args.no_wake_word

    while True:
        if pause_event.is_set():
            time.sleep(0.5)
            continue

        if args.text:
            try:
                user_query = input("YOU: ").lower()
            except EOFError:
                break
        else:
            if not wake_word_active:
                user_query = listen()
            else:
                user_query = listen()

        if pause_event.is_set():
            continue

        if user_query == "none" or not user_query:
            continue

        if "quit" in user_query:
            print("Shutting down JARVIS loop...")
            speak("Shutting down.")
            break

        if not wake_word_active:
            direct_commands = [
                "open", "volume", "search", "create", "write", "read", "make",
                "who", "what", "when", "where", "how", "why", "thank", "hello",
                "play", "pause", "stop", "next", "previous", "mute",
                "screenshot", "photo", "capture", "detect", "lock", "shutdown",
                "restart", "sleep", "brightness", "battery", "cpu", "ram",
                "memory", "remember", "forget", "calculate", "note", "timer",
                "email", "weather", "time", "date", "clipboard", "copy", "paste",
                "close", "switch", "setting", "settings", "display",
                "process", "running", "apps", "application", "list",
                "sorry", "thanks", "thank you", "hi", "hey", "help",
                "yes", "no", "ok", "okay", "sure", "please",
                "music", "song", "track", "video", "camera",
                "file", "folder", "desktop", "document",
                "type", "mode", "text", "voice",
                "exit", "quit", "bye", "goodbye",
                "current", "which", "are", "you", "doing",
                "start", "launch", "run", "execute",
                "system", "info", "status", "check",
                "send", "message", "call", "whatsapp",
                "note", "notes", "save", "delete", "remove",
                "clear", "empty", "clean", "refresh",
                "update", "install", "download",
                "screen", "display", "monitor",
                "power", "charge", "charging",
                "connect", "disconnect", "wifi", "bluetooth",
                "hotspot", "airplane", "dark", "light",
                "theme", "wallpaper", "background",
                "browser", "website", "page", "browse",
                "network", "internet", "ping", "ip",
                "process", "kill", "task", "software",
                "install", "uninstall",
                "reminder", "alarm", "remind", "pomodoro",
                "disk", "drive", "space",
                "find", "locate", "where is", "search for",
                "directory", "ls", "dir",
                "info", "details", "specs", "specification",
            ]

            is_direct = any(cmd in user_query for cmd in direct_commands)

            if "jarvis" not in user_query and not is_direct:
                print(f"Ignored: {user_query}")
                continue

        clean_query = user_query.replace("jarvis", "").replace("hey jarvis", "").replace("ok jarvis", "").strip()

        try:
            print(f"Thinking: {clean_query}")
            if not args.text:
                speak_sync("Let me check that for you.")
            response = jarvis.run_conversation(clean_query)

            if pause_event.is_set():
                continue

            if response:
                if args.text:
                    print(f"JARVIS: {response}")
                else:
                    speak_sync(response)
        except Exception as e:
            print(f"Main Loop Error: {e}")
            if args.text:
                print("JARVIS: System error.")
            else:
                speak_sync("Sorry, I encountered an error.")


def main():
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument("--text", action="store_true", help="Run in text mode (no voice I/O)")
    parser.add_argument("--no-wake-word", action="store_true", help="Disable wake word requirement (listen always)")
    args = parser.parse_args()

    pause_event = threading.Event()
    context = {"pause_event": pause_event}

    registry = SkillRegistry()
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")
    registry.load_skills(skills_dir, context=context)

    t = threading.Thread(target=jarvis_loop, args=(pause_event, registry, args), daemon=True)
    t.start()

    run_gui_app(pause_event)


if __name__ == "__main__":
    main()
