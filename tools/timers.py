"""
Timer and stopwatch tool running in background threads with audio/voice alerts.
"""

import time
import threading
import winsound
from typing import Tuple, List, Dict
import tools.feedback as feedback_tool

# List to keep track of running active timers
_ACTIVE_TIMERS: List[Dict] = []
_LOCK = threading.Lock()


def _timer_worker(total_seconds: int, label: str):
    time.sleep(total_seconds)
    
    # Notify user
    alert_msg = f"Timer of {label} is up!"
    print(f"\n⏰ [ALARM] {alert_msg}")
    
    # Play Windows chime / beep
    try:
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        for _ in range(3):
            winsound.Beep(1000, 250)
            time.sleep(0.1)
    except Exception:
        pass

    # Spoken alert
    feedback_tool.provide_feedback(f"⏰ {alert_msg}", f"Your {label} timer is finished.")

    # Remove from active list
    with _LOCK:
        global _ACTIVE_TIMERS
        _ACTIVE_TIMERS = [t for t in _ACTIVE_TIMERS if t["label"] != label]


def set_timer(seconds: int, label: str = None) -> Tuple[bool, str]:
    """Start a background timer for the specified seconds."""
    if seconds <= 0:
        return False, "Timer duration must be greater than 0 seconds."

    if not label:
        if seconds >= 3600:
            label = f"{seconds // 3600} hour{'s' if seconds // 3600 > 1 else ''}"
        elif seconds >= 60:
            label = f"{seconds // 60} minute{'s' if seconds // 60 > 1 else ''}"
        else:
            label = f"{seconds} second{'s' if seconds > 1 else ''}"

    thread = threading.Thread(target=_timer_worker, args=(seconds, label), daemon=True)
    thread.start()

    with _LOCK:
        _ACTIVE_TIMERS.append({"label": label, "seconds": seconds, "start": time.time()})

    msg = f"Timer set for {label}."
    return True, msg


def parse_time_duration(time_str: str) -> int:
    """
    Parses natural language duration string into total seconds.
    e.g. '30 minutes' -> 1800, '5 seconds' -> 5, '1 hour' -> 3600
    """
    clean = time_str.lower().strip()
    total_seconds = 0
    import re

    # Match hours
    h = re.search(r"(\d+)\s*(?:hour|hr|h)", clean)
    if h:
        total_seconds += int(h.group(1)) * 3600

    # Match minutes
    m = re.search(r"(\d+)\s*(?:minute|min|m)", clean)
    if m:
        total_seconds += int(m.group(1)) * 60

    # Match seconds
    s = re.search(r"(\d+)\s*(?:second|sec|s)", clean)
    if s:
        total_seconds += int(s.group(1))

    # Fallback: if only a number was passed (e.g. "30") default to minutes if >= 1, or seconds
    if total_seconds == 0:
        num = re.search(r"(\d+)", clean)
        if num:
            val = int(num.group(1))
            total_seconds = val * 60  # default to minutes

    return total_seconds
