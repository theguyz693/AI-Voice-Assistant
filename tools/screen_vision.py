"""
On-demand screen awareness module.
Captures the screen ONLY when explicitly asked and interprets it using a local vision model if available.
"""

import io
import base64
import json
import urllib.request
import urllib.error
from typing import Tuple, Optional
import config


def _get_installed_vision_models() -> list[str]:
    """Check running Ollama instance for models with vision capability."""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("models", [])
            vision_models = []
            for m in models:
                name = m.get("name", "").lower()
                # Common vision models in Ollama: llama3.2-vision, moondream, minicpm-v, llava, bakllava
                if any(v in name for v in ["vision", "moondream", "minicpm", "llava"]):
                    vision_models.append(m.get("name"))
            return vision_models
    except Exception:
        return []


def _capture_screen_bytes() -> Optional[str]:
    """Capture screen and return JPEG base64 string, with multiple fallbacks."""
    # Attempt 1: PyAutoGUI / PIL ImageGrab
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        max_width = 1280
        if screenshot.width > max_width:
            ratio = max_width / float(screenshot.width)
            new_height = int(float(screenshot.height) * float(ratio))
            screenshot = screenshot.resize((max_width, new_height))

        buffered = io.BytesIO()
        screenshot.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception:
        pass

    # Attempt 2: mss fallback
    try:
        import mss
        import PIL.Image
        with mss.MSS() as sct:
            mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(mon)
            img = PIL.Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception:
        pass

    return None


def analyze_screen(query: str = "What is on my screen?") -> Tuple[bool, str, str]:
    """
    On-demand screen capture and visual analysis.
    Returns: (success, display_text, spoken_text)
    """
    print(f"\n[SCREEN AWARENESS] Explicit request: '{query}'")

    # 1. Check for installed local vision model FIRST
    vision_models = _get_installed_vision_models()

    if not vision_models:
        # No vision model currently installed in Ollama
        display_msg = (
            "[!] Screen awareness requires a local vision model.\n"
            "Your current installed Ollama model ('llama3.2:1b') is text-only.\n"
            "To enable visual screen reading, open PowerShell and run:\n"
            "  -> ollama run moondream  (Lightweight ~1.8GB, very fast on CPU)\n"
            "  OR\n"
            "  -> ollama run llama3.2-vision  (Meta's 11B vision model)"
        )
        spoken_msg = (
            "Screen reading requires a local vision model like Moondream or LLaMA Vision. "
            "You can enable it anytime by running 'ollama run moondream' in your terminal."
        )
        print(f"\n{display_msg}")
        return False, display_msg, spoken_msg

    # 2. Capture screen locally in-memory
    img_b64 = _capture_screen_bytes()
    if not img_b64:
        msg = "Screen capture is unavailable (display may be locked or inaccessible)."
        return False, msg, "Sorry, I could not capture your screen right now."

    # 3. Use the first available vision model
    model_name = vision_models[0]
    print(f"[SCREEN AWARENESS] Analyzing with local vision model: '{model_name}'...")

    prompt = "What does this image show?"




    payload = {
        "model": model_name,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 150,
        },
    }

    try:
        req = urllib.request.Request(
            config.OLLAMA_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_vision = data.get("response", "").strip()

            if not raw_vision:
                raw_vision = "I examined your screen but could not discern the details."

            # Pass visual analysis through conversational model (qwen2.5:7b) for a chill, natural spoken voice response
            spoken_text = raw_vision
            try:
                synth_prompt = (
                    f"The user asked: '{query}'.\n"
                    f"Visual analysis of their screen: '{raw_vision}'.\n"
                    "Provide a direct, natural, conversational 1-2 sentence response explaining what they are looking at. "
                    "Do not use markdown."
                )
                synth_payload = {
                    "model": config.CHAT_MODEL,
                    "prompt": synth_prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 80},
                }
                synth_req = urllib.request.Request(
                    config.OLLAMA_API_URL,
                    data=json.dumps(synth_payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(synth_req, timeout=8.0) as s_resp:
                    s_data = json.loads(s_resp.read().decode("utf-8"))
                    cand = s_data.get("response", "").strip()
                    if cand:
                        spoken_text = cand
            except Exception:
                pass

            return True, raw_vision, spoken_text
    except Exception as e:
        msg = f"Vision model inference failed: {e}"
        print(f"[X] {msg}")
        return False, msg, "Sorry, I encountered an error analyzing your screen."

