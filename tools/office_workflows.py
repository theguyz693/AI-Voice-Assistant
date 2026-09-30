"""
Reliable Microsoft Office workflows (Word, PowerPoint) with window readiness verification.
Replaces static delays with dynamic window detection and blank document creation.
"""

import time
import subprocess
import pyautogui
from typing import Tuple
from tools.window_manager import wait_for_window, set_foreground


def open_word_and_prepare_document() -> Tuple[bool, str]:
    """
    Launch Word, wait for window, and open a blank document ready for typing.
    """
    print("[📄 OFFICE WORKFLOW] Launching Word and preparing blank document...")
    try:
        subprocess.Popen("start winword", shell=True)
        # Wait dynamically for Word window to appear and take focus
        hwnd = wait_for_window("Word", timeout=7.0, ensure_foreground=True)
        if not hwnd:
            return False, "Microsoft Word did not appear to open, so I stopped the task."

        set_foreground(hwnd)
        time.sleep(0.6)

        # On Word startup screen, pressing Enter or Esc creates/opens the default Blank Document
        pyautogui.press("enter")
        time.sleep(0.8)

        # Verify Word is still in foreground and ready
        set_foreground(hwnd)
        return True, "Word is ready with a blank document."

    except Exception as e:
        return False, f"Failed to initialize Word: {e}"


def open_powerpoint_and_prepare_presentation() -> Tuple[bool, str]:
    """
    Launch PowerPoint, wait for window, and select blank presentation ready for editing.
    """
    print("[📊 OFFICE WORKFLOW] Launching PowerPoint and preparing blank presentation...")
    try:
        subprocess.Popen("start powerpnt", shell=True)
        hwnd = wait_for_window("PowerPoint", timeout=7.0, ensure_foreground=True)
        if not hwnd:
            return False, "PowerPoint did not appear to open, so I stopped the task."

        set_foreground(hwnd)
        time.sleep(0.6)

        # Press Enter to select the default Blank Presentation template
        pyautogui.press("enter")
        time.sleep(0.8)

        set_foreground(hwnd)
        return True, "PowerPoint is ready with a blank presentation."

    except Exception as e:
        return False, f"Failed to initialize PowerPoint: {e}"
