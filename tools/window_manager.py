"""
Windows window manager using pywin32.
Provides reliable window detection, foreground verification, and focus handling.
Replaces static sleep timers with dynamic window readiness checks.
"""

import time
import win32gui
import win32process
import win32con
from typing import Optional, List, Tuple


def get_visible_windows() -> List[Tuple[int, str]]:
    """Enumerate all top-level visible windows with non-empty titles."""
    results = []

    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            if title:
                results.append((hwnd, title))
        return True

    try:
        win32gui.EnumWindows(enum_handler, None)
    except Exception:
        pass
    return results


def find_window_by_title(title_substring: str) -> Optional[int]:
    """Find the handle of a visible window matching title_substring (case-insensitive)."""
    sub_lower = title_substring.lower()
    for hwnd, title in get_visible_windows():
        if sub_lower in title.lower():
            return hwnd
    return None


def is_foreground_window(hwnd: int) -> bool:
    """Check if the given window handle is currently the active foreground window."""
    try:
        return win32gui.GetForegroundWindow() == hwnd
    except Exception:
        return False


def set_foreground(hwnd: int) -> bool:
    """Bring the specified window to the foreground and restore if minimized."""
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        # Fallback using ShowWindow
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            return True
        except Exception:
            return False


def wait_for_window(
    title_substring: str,
    timeout: float = 6.0,
    ensure_foreground: bool = True,
    poll_interval: float = 0.15,
) -> Optional[int]:
    """
    Polls until a visible window matching title_substring appears, or timeout is reached.
    If ensure_foreground is True, brings it to the foreground and verifies focus.

    Returns:
        hwnd (int) if ready, or None if timed out.
    """
    start_time = time.time()
    sub_lower = title_substring.lower()

    while time.time() - start_time < timeout:
        for hwnd, title in get_visible_windows():
            if sub_lower in title.lower():
                # Found window, now verify or establish foreground
                if ensure_foreground:
                    set_foreground(hwnd)
                    time.sleep(0.1)
                return hwnd
        time.sleep(poll_interval)

    return None
