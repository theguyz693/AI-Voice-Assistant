"""
Keyboard simulation tools for typing text and executing safe key combinations.
"""

import time
import pyautogui
import pyperclip
from typing import Tuple

# Set PyAutoGUI fail-safe to True (moving mouse to corner stops it)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

# Mapping of spoken key phrases to PyAutoGUI key names or hotkeys
SAFE_KEY_MAP = {
    "enter": ["enter"],
    "return": ["enter"],
    "press enter": ["enter"],
    "escape": ["esc"],
    "esc": ["esc"],
    "press escape": ["esc"],
    "tab": ["tab"],
    "press tab": ["tab"],
    "space": ["space"],
    "backspace": ["backspace"],
    "copy": ["ctrl", "c"],
    "paste": ["ctrl", "v"],
    "cut": ["ctrl", "x"],
    "undo": ["ctrl", "z"],
    "redo": ["ctrl", "y"],
    "select all": ["ctrl", "a"],
    "save": ["ctrl", "s"],
    "control shift p": ["ctrl", "shift", "p"],
    "ctrl shift p": ["ctrl", "shift", "p"],
    "press control shift p": ["ctrl", "shift", "p"],
}


def type_text(text: str) -> Tuple[bool, str]:
    """
    Type text into whichever window currently has focus.
    Uses clipboard paste for 100% accurate Unicode, punctuation, and speed.
    """
    if not text:
        return False, "No text provided to type."

    try:
        # Give a micro delay to ensure target window focus
        time.sleep(0.15)
        # Preserve existing clipboard content if possible
        try:
            prev_clipboard = pyperclip.paste()
        except Exception:
            prev_clipboard = ""

        # Paste text
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.05)

        # Restore previous clipboard
        try:
            if prev_clipboard:
                pyperclip.copy(prev_clipboard)
        except Exception:
            pass

        return True, f"Typed: '{text}'"
    except Exception as e:
        return False, f"Failed to type text: {e}"


def press_key(key_phrase: str) -> Tuple[bool, str]:
    """
    Simulate a constrained, explicitly recognized keypress or combination.
    """
    clean_key = key_phrase.strip().lower()

    # Look up in safe key map
    combo = SAFE_KEY_MAP.get(clean_key)

    if not combo:
        # Normalize: strip leading "press " if present
        if clean_key.startswith("press "):
            clean_key = clean_key[6:].strip()
            combo = SAFE_KEY_MAP.get(clean_key)

    if not combo:
        # Check single alphanumeric key
        if len(clean_key) == 1 and clean_key.isalnum():
            combo = [clean_key]

    if not combo:
        return False, f"Keypress '{key_phrase}' is not in the safe allowed list."

    try:
        time.sleep(0.1)
        if len(combo) == 1:
            pyautogui.press(combo[0])
        else:
            pyautogui.hotkey(*combo)
        return True, f"Pressed {' + '.join(combo)}"
    except Exception as e:
        return False, f"Failed to press key '{key_phrase}': {e}"
