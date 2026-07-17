import os
import sys
import re
import speech_recognition as sr
import subprocess
import threading
import tempfile

is_speaking = False

def _clean_for_speech(text):
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'\{.*?\}', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('**', '').replace('`', '').replace('#', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _speak_windows(text):
    """Write PowerShell script to temp file and execute — avoids $ escaping issues."""
    safe_text = text.replace("'", "''")
    ps_code = (
        "Add-Type -AssemblyName System.Speech\n"
        "\x24voice = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        "\x24voice.SelectVoice('Microsoft David Desktop')\n"
        "\x24voice.Rate = 2\n"
        f"\x24voice.Speak('{safe_text}')\n"
        "\x24voice.Dispose()\n"
    )
    fd, script_path = tempfile.mkstemp(suffix='.ps1')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(ps_code)
        subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script_path],
            capture_output=True, timeout=30
        )
    except Exception as e:
        print(f"TTS Error: {e}")
    finally:
        try:
            os.remove(script_path)
        except:
            pass

def _speak_mac(text):
    clean = text.replace('"', '\\"').replace("'", "")
    os.system(f'say "{clean}"')

def _speak_linux(text):
    os.system(f'espeak "{text}"')

def speak(text):
    """Non-blocking speech — speaks in a background thread."""
    global is_speaking
    clean = _clean_for_speech(text)
    if not clean or len(clean) < 2:
        clean = "Done."
    if len(clean) > 500:
        clean = clean[:500] + "..."

    print(f"JARVIS: {clean}", flush=True)

    def _do_speak():
        global is_speaking
        is_speaking = True
        try:
            if sys.platform == "win32":
                _speak_windows(clean)
            elif sys.platform == "darwin":
                _speak_mac(clean)
            else:
                _speak_linux(clean)
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            is_speaking = False

    t = threading.Thread(target=_do_speak, daemon=True)
    t.start()

def speak_sync(text):
    """Blocking speech — waits for speech to finish."""
    global is_speaking
    clean = _clean_for_speech(text)
    if not clean or len(clean) < 2:
        clean = "Done."
    if len(clean) > 500:
        clean = clean[:500] + "..."

    print(f"JARVIS: {clean}", flush=True)

    is_speaking = True
    try:
        if sys.platform == "win32":
            _speak_windows(clean)
        elif sys.platform == "darwin":
            _speak_mac(clean)
        else:
            _speak_linux(clean)
    except Exception as e:
        print(f"TTS Error: {e}")
    finally:
        is_speaking = False

def listen():
    """Listen for voice input via microphone."""
    global is_speaking
    if is_speaking:
        return "none"

    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...", flush=True)
        r.pause_threshold = 0.8
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=5)
            print("Recognizing...", flush=True)
            query = r.recognize_google(audio)
            return query.lower()
        except Exception:
            return "none"
