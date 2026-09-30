"""
Reliable Spotify automation for desktop Windows.
Uses the spotify:search URI to open the search, then navigates to and plays the top result.

Instrumented with step-by-step diagnostic logging so failures are always visible.
"""

import time
import subprocess
import ctypes
import urllib.parse
import pyautogui
from typing import Tuple, Optional
from tools.window_manager import wait_for_window, set_foreground, find_window_by_title, is_foreground_window

# ── helpers ──────────────────────────────────────────────────────────────────

def _spotify_hwnd() -> Optional[int]:
    """Return Spotify window handle, or None."""
    return find_window_by_title("Spotify")


def _ensure_foreground(hwnd: int, label: str) -> bool:
    """Bring window to foreground; return True if it is now the active window."""
    set_foreground(hwnd)
    time.sleep(0.25)
    if is_foreground_window(hwnd):
        print(f"[Spotify] {label} focused ✓")
        return True
    # One retry via Alt+Tab trick: attach thread focus then set foreground
    try:
        hwnd_fg = ctypes.windll.user32.GetForegroundWindow()
        tid_fg  = ctypes.windll.user32.GetWindowThreadProcessId(hwnd_fg, None)
        tid_self = ctypes.windll.kernel32.GetCurrentThreadId()
        ctypes.windll.user32.AttachThreadInput(tid_fg, tid_self, True)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        ctypes.windll.user32.AttachThreadInput(tid_fg, tid_self, False)
        time.sleep(0.2)
    except Exception:
        pass
    ok = is_foreground_window(hwnd)
    print(f"[Spotify] {label} focused {'✓' if ok else '✗ (best-effort, continuing)'}")
    return ok


def _send_play_media_key() -> None:
    """Send the VK_MEDIA_PLAY_PAUSE key via Windows API."""
    VK_MEDIA_PLAY_PAUSE = 0xB3
    KEYEVENTF_KEYUP = 0x0002
    try:
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
    except Exception:
        pass


# ── main function ─────────────────────────────────────────────────────────────

def play_spotify_track(query: str) -> Tuple[bool, str]:
    """
    Search for and play a track on the Spotify desktop app.

    Strategy
    --------
    1.  Launch via spotify:search: URI (positions cursor in search results).
    2.  Wait for Spotify window.
    3.  Ensure Spotify is the foreground window.
    4.  Give the search results time to load.
    5.  Navigate to the first result with Tab (Spotify's keyboard model puts the
        first song result in focus after one Tab from the search bar).
    6.  Press Enter to play the focused result.
    7.  Send media Play key as a fallback if Enter alone isn't enough.
    8.  Wait briefly and verify whether the window title changed (Spotify shows
        "Song – Artist" in its title bar during playback on most builds).
    """
    clean_query = query.strip()
    if not clean_query:
        return False, "No song or artist specified for Spotify."

    print(f"\n[Spotify] Preparing to play: '{clean_query}'")

    try:
        # ── Step 1: Launch via URI ────────────────────────────────────────────
        print("[Spotify] Launching via spotify:search URI...")
        encoded = urllib.parse.quote(clean_query)
        subprocess.Popen(f'start "" "spotify:search:{encoded}"', shell=True)

        # ── Step 2: Wait for window ───────────────────────────────────────────
        print("[Spotify] Waiting for window...")
        hwnd = wait_for_window("Spotify", timeout=8.0, ensure_foreground=False)

        if not hwnd:
            print("[Spotify] URI launch failed — trying plain 'start spotify'...")
            subprocess.Popen("start spotify", shell=True)
            hwnd = wait_for_window("Spotify", timeout=6.0, ensure_foreground=False)

        if not hwnd:
            return False, "Spotify did not open — cannot play track."

        print(f"[Spotify] Window detected (hwnd={hwnd}) ✓")

        # ── Step 3: Focus window ──────────────────────────────────────────────
        print("[Spotify] Focusing window...")
        _ensure_foreground(hwnd, "Window")

        # ── Step 4: Wait for search results to render ─────────────────────────
        # The spotify:search URI lands us on the search results page.
        # Spotify needs a moment to populate the results list.
        print("[Spotify] Waiting for search results to render...")
        time.sleep(2.2)

        # Re-focus in case another window grabbed attention during load
        hwnd = _spotify_hwnd() or hwnd
        _ensure_foreground(hwnd, "Window (post-load)")

        # ── Step 5: Navigate to the first song result ─────────────────────────
        # In Spotify desktop the search results page structure (as of recent builds):
        #   - Search box has focus initially.
        #   - Tab once moves into the results grid.
        #   - The first cell in "Songs" section is selected.
        #   - Enter on a song row starts playback.
        print("[Spotify] Navigating to first song result (Tab)...")
        pyautogui.press("tab")
        time.sleep(0.35)

        # ── Step 6: Play via Enter ────────────────────────────────────────────
        print("[Spotify] Sending Enter to play top result...")
        pyautogui.press("enter")
        time.sleep(0.8)

        # ── Step 7: Fallback — media Play key ────────────────────────────────
        # Some Spotify builds require an explicit play command after selection.
        print("[Spotify] Sending media Play/Pause key (fallback)...")
        _send_play_media_key()
        time.sleep(0.5)

        # ── Step 8: Verify playback ───────────────────────────────────────────
        # Spotify desktop shows "Track – Artist – Spotify" in its title bar
        # during active playback on most Windows builds.
        print("[Spotify] Checking playback via window title...")
        hwnd = _spotify_hwnd() or hwnd
        import win32gui
        title_after = win32gui.GetWindowText(hwnd) if hwnd else ""
        print(f"[Spotify] Window title now: '{title_after}'")

        # Heuristic: if the title is no longer just "Spotify" it usually means
        # something is playing (title becomes "Song – Artist" or similar).
        playing = bool(
            title_after
            and title_after.strip().lower() not in ("spotify", "spotify premium", "")
        )

        if playing:
            print(f"[Spotify] Playback confirmed ✓  (title: '{title_after}')")
            return True, f"Playing '{clean_query}' on Spotify — {title_after}."
        else:
            # One more retry: Space bar (play/pause toggle)
            print("[Spotify] Title unchanged — retrying with Space bar...")
            _ensure_foreground(hwnd, "Window (Space retry)")
            pyautogui.press("space")
            time.sleep(1.0)

            hwnd = _spotify_hwnd() or hwnd
            title_retry = win32gui.GetWindowText(hwnd) if hwnd else ""
            print(f"[Spotify] Window title after Space: '{title_retry}'")

            playing_retry = bool(
                title_retry
                and title_retry.strip().lower() not in ("spotify", "spotify premium", "")
            )

            if playing_retry:
                print(f"[Spotify] Playback confirmed after Space ✓  (title: '{title_retry}')")
                return True, f"Playing '{clean_query}' on Spotify — {title_retry}."
            else:
                # Spotify opened and search results appeared, but we could not
                # confirm that playback actually started.
                print("[Spotify] ✗ Could not confirm playback. Search results are visible but playback state unknown.")
                return False, (
                    f"Spotify opened and showed search results for '{clean_query}', "
                    "but I could not confirm that playback started. "
                    "Try pressing Enter or Space in the Spotify window."
                )

    except Exception as e:
        return False, f"Spotify automation failed: {e}"
