"""
System utilities: volume, media playback, window management, screenshots, and time/date.
"""

import os
import time
import datetime
import pyautogui
from typing import Tuple
from pathlib import Path


def adjust_volume(action: str) -> Tuple[bool, str]:
    """Adjust system master volume."""
    action = action.lower().strip()
    try:
        if "up" in action:
            for _ in range(5):
                pyautogui.press("volumeup")
            return True, "Volume increased"
        elif "down" in action:
            for _ in range(5):
                pyautogui.press("volumedown")
            return True, "Volume decreased"
        elif "mute" in action or "unmute" in action:
            pyautogui.press("volumemute")
            return True, "Toggled volume mute"
        return False, f"Unknown volume action: {action}"
    except Exception as e:
        return False, f"Failed to adjust volume: {e}"


def control_media(action: str) -> Tuple[bool, str]:
    """Control media playback (play/pause, next, previous)."""
    action = action.lower().strip()
    try:
        if "next" in action:
            pyautogui.press("nexttrack")
            return True, "Skipped to next track"
        elif "prev" in action or "back" in action:
            pyautogui.press("prevtrack")
            return True, "Returned to previous track"
        elif "pause" in action or "play" in action or "stop" in action:
            pyautogui.press("playpause")
            return True, "Toggled media playback"
        return False, f"Unknown media action: {action}"
    except Exception as e:
        return False, f"Failed media control: {e}"


def control_window(action: str) -> Tuple[bool, str]:
    """Manage active window (minimize, maximize, close)."""
    action = action.lower().strip()
    try:
        if "minimize" in action:
            pyautogui.hotkey("win", "down")
            return True, "Minimized window"
        elif "maximize" in action:
            pyautogui.hotkey("win", "up")
            return True, "Maximized window"
        elif "close" in action:
            pyautogui.hotkey("alt", "f4")
            return True, "Closed active window"
        return False, f"Unknown window action: {action}"
    except Exception as e:
        return False, f"Failed window action: {e}"


def take_screenshot() -> Tuple[bool, str]:
    """Take a desktop screenshot and save to a screenshots directory."""
    try:
        ss_dir = Path("screenshots")
        ss_dir.mkdir(exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = ss_dir / f"screenshot_{timestamp}.png"
        
        screenshot = pyautogui.screenshot()
        screenshot.save(str(filepath))
        return True, f"Screenshot saved to {filepath.name}"
    except Exception as e:
        return False, f"Failed to take screenshot: {e}"


def get_current_time_date(info_type: str = "time") -> Tuple[bool, str]:
    """Report current time or date."""
    now = datetime.datetime.now()
    if "date" in info_type.lower():
        msg = f"Today is {now.strftime('%A, %B %d, %Y')}"
    else:
        msg = f"The time is {now.strftime('%I:%M %p')}"
    return True, msg
