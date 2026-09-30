"""
Desktop Orb Overlay — lightweight always-visible floating companion.

Features:
- Visual Identity: Uses uploaded pngegg.png (😎 emoji with transparent background).
- IDLE: Compact circular bubble (64px) near screen edge, draggable, click-to-activate.
- ACTIVE: Orb subtly animates with reactive glows, spinner arcs, and a companion status pill.
- Suggested States:
    IDLE:             Small dark circle with the uploaded 😎 emoji.
    LISTENING:        Subtle sky-blue pulse/glow around the emoji.
    THINKING:         Warm amber dual-sweep radar pulse.
    EXECUTING:        Neon-green rotating activity indicator arc around the emoji.
    TALKING:          Vibrant purple soundwave pulse while TTS is playing.
    SCREEN ANALYZING: Teal scanning beam sweep.
    ERROR:            Brief red alert indication & micro-shake, then returns to idle.
"""

import math
import queue
import threading
import tkinter as tk
from pathlib import Path
from typing import Optional, Callable
from PIL import Image, ImageTk
import config

# ── palette & styling ─────────────────────────────────────────────────────────
_PALETTES = {
    "IDLE": {
        "bubble_bg": "#18181b",
        "border":    "#3f3f46",
        "glow":      "",
        "pill_bg":   "#18181b",
        "fg":        "#a1a1aa",
        "dot":       "#52525b",
        "label":     "Ready",
    },
    "LISTENING": {
        "bubble_bg": "#0f172a",
        "border":    "#0284c7",
        "glow":      "#38bdf8",
        "pill_bg":   "#0f172a",
        "fg":        "#38bdf8",
        "dot":       "#38bdf8",
        "label":     "Listening…",
    },
    "PROCESSING": {
        "bubble_bg": "#1c1917",
        "border":    "#d97706",
        "glow":      "#fbbf24",
        "pill_bg":   "#1c1917",
        "fg":        "#fbbf24",
        "dot":       "#fbbf24",
        "label":     "Transcribing…",
    },
    "THINKING": {
        "bubble_bg": "#1c1917",
        "border":    "#d97706",
        "glow":      "#fbbf24",
        "pill_bg":   "#1c1917",
        "fg":        "#fbbf24",
        "dot":       "#fbbf24",
        "label":     "Thinking…",
    },
    "EXECUTING": {
        "bubble_bg": "#052e16",
        "border":    "#16a34a",
        "glow":      "#4ade80",
        "pill_bg":   "#052e16",
        "fg":        "#4ade80",
        "dot":       "#4ade80",
        "label":     "Executing…",
    },
    "TALKING": {
        "bubble_bg": "#1e1b4b",
        "border":    "#9333ea",
        "glow":      "#c084fc",
        "pill_bg":   "#1e1b4b",
        "fg":        "#c084fc",
        "dot":       "#c084fc",
        "label":     "Speaking…",
    },
    "SCREEN ANALYZING": {
        "bubble_bg": "#042f2e",
        "border":    "#0d9488",
        "glow":      "#2dd4bf",
        "pill_bg":   "#042f2e",
        "fg":        "#2dd4bf",
        "dot":       "#2dd4bf",
        "label":     "Analyzing…",
    },
    "ERROR": {
        "bubble_bg": "#2a0808",
        "border":    "#dc2626",
        "glow":      "#f87171",
        "pill_bg":   "#2a0808",
        "fg":        "#f87171",
        "dot":       "#f87171",
        "label":     "Error",
    },
}

ORB_SIZE    = 64   # Compact diameter of the orb window in px
PILL_W      = 260  # Width of the companion status pill
PILL_H      = 52   # Height of the companion status pill
ANIM_MS     = 16   # ~60 fps animation tick
HIDE_DELAY  = 2800 # ms after returning to IDLE before pill collapses
ERROR_RESET = 2300 # ms after ERROR before returning to IDLE


# ── image locator ─────────────────────────────────────────────────────────────
def _find_avatar_image() -> Optional[Path]:
    """Find the pngegg.png emoji asset."""
    candidates = [
        config.BASE_DIR / getattr(config, "ORB_ICON_FILE", "ui/assets/pngegg.png"),
        config.BASE_DIR / "ui" / "assets" / "pngegg.png",
        config.BASE_DIR / "pngegg.png",
        Path(r"C:\sem7\pngegg.png"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


# ── position persistence ──────────────────────────────────────────────────────
def _load_pos(screen_w: int, screen_h: int) -> tuple[int, int]:
    pos_file = config.BASE_DIR / config.ORB_POSITION_FILE
    try:
        x, y = pos_file.read_text().strip().split(",")
        x, y = int(x), int(y)
        # Clamp to screen
        x = max(0, min(x, screen_w - ORB_SIZE))
        y = max(0, min(y, screen_h - ORB_SIZE))
        return x, y
    except Exception:
        # Default: right edge, vertically centered
        return screen_w - ORB_SIZE - 12, (screen_h - ORB_SIZE) // 2


def _save_pos(x: int, y: int) -> None:
    try:
        (config.BASE_DIR / config.ORB_POSITION_FILE).write_text(f"{x},{y}")
    except Exception:
        pass


def _snap_to_edge(x: int, y: int, screen_w: int, screen_h: int, margin: int) -> tuple[int, int]:
    """Snap the orb to whichever screen edge it is closest to."""
    dist_left  = x
    dist_right = screen_w - ORB_SIZE - x
    dist_top   = y
    dist_bot   = screen_h - ORB_SIZE - y
    min_dist   = min(dist_left, dist_right, dist_top, dist_bot)

    if min_dist == dist_left:
        x = margin
    elif min_dist == dist_right:
        x = screen_w - ORB_SIZE - margin
    elif min_dist == dist_top:
        y = margin
    else:
        y = screen_h - ORB_SIZE - margin
    return x, y


# ── main class ────────────────────────────────────────────────────────────────
class DesktopOverlay:
    """
    Floating orb companion overlay with 😎 emoji identity.
    Public API (thread-safe):
        overlay.set_state(state, primary_text, sub_text)
        overlay.set_activate_callback(fn)   # called when orb is clicked
        overlay.start()
    """

    def __init__(self):
        self._msg_queue: queue.Queue = queue.Queue()
        self.root: Optional[tk.Tk] = None
        self._is_ready = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._activate_cb: Optional[Callable] = None

        # Animation states
        self._current_state = "IDLE"
        self._current_pal   = _PALETTES["IDLE"]
        self._pulse_phase   = 0.0
        self._spinner_angle = 0.0
        self._pill_visible  = False
        self._hide_after_id = None
        self._error_reset_id = None

        # Drag state
        self._drag_x = 0
        self._drag_y = 0
        self._dragging = False

        # Shake animation state
        self._shake_frames: list[int] = []
        self._base_x = 0

        # Load raw avatar PIL image
        self._raw_avatar: Optional[Image.Image] = None
        img_path = _find_avatar_image()
        if img_path:
            try:
                self._raw_avatar = Image.open(img_path).convert("RGBA")
            except Exception as e:
                print(f"[⚠️ Overlay] Could not load avatar image {img_path}: {e}")

    # ── public ────────────────────────────────────────────────────────────────

    def set_activate_callback(self, fn: Callable) -> None:
        self._activate_cb = fn

    def start(self) -> None:
        """Start the orb GUI in a background daemon thread."""
        self._thread = threading.Thread(target=self._run_gui, daemon=True)
        self._thread.start()
        self._is_ready.wait(timeout=4.0)

    def set_state(self, state: str, primary_text: str = "", sub_text: str = "") -> None:
        """Thread-safe state update — callable from any thread."""
        self._msg_queue.put((state.upper(), primary_text, sub_text))

    # ── GUI bootstrap ─────────────────────────────────────────────────────────

    def _run_gui(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()  # start hidden; geometry set before deiconify

        self.root.overrideredirect(True)          # frameless
        self.root.wm_attributes("-topmost", True) # always on top
        # Transparent background — Windows color keying
        self.root.wm_attributes("-transparentcolor", "#010101")
        self.root.configure(bg="#010101")

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ox, oy = _load_pos(sw, sh)
        self.root.geometry(f"{ORB_SIZE}x{ORB_SIZE}+{ox}+{oy}")

        # Canvas for the orb
        self._canvas = tk.Canvas(
            self.root,
            width=ORB_SIZE,
            height=ORB_SIZE,
            bg="#010101",
            highlightthickness=0,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        cx, cy = ORB_SIZE // 2, ORB_SIZE // 2

        # 1. Outer dynamic glow / pulse ring
        self._glow_ring_id = self._canvas.create_oval(
            cx - 27, cy - 27, cx + 27, cy + 27,
            outline="", width=2,
        )

        # 2. Activity indicator spinner arcs
        self._arc_spinner_id = self._canvas.create_arc(
            3.5, 3.5, ORB_SIZE - 3.5, ORB_SIZE - 3.5,
            start=0, extent=0, style=tk.ARC,
            outline="", width=2.5,
        )
        self._arc_pulse2_id = self._canvas.create_arc(
            3.5, 3.5, ORB_SIZE - 3.5, ORB_SIZE - 3.5,
            start=0, extent=0, style=tk.ARC,
            outline="", width=2.0,
        )

        # 3. Central circular bubble background
        # Diameter 52px (radius 26), leaving outer perimeter for glow / indicator
        self._bubble_id = self._canvas.create_oval(
            6, 6, ORB_SIZE - 6, ORB_SIZE - 6,
            fill="#18181b", outline="#3f3f46", width=1.5,
        )

        # 4. Avatar emoji inside bubble (preserve aspect ratio, transparent bg)
        self._photo_avatar: Optional[ImageTk.PhotoImage] = None
        if self._raw_avatar:
            # Fit cleanly inside 52px circle: width 44, height ~33
            target_w = 44
            aspect_h = int(self._raw_avatar.height * (target_w / self._raw_avatar.width))
            resized = self._raw_avatar.resize((target_w, aspect_h), Image.Resampling.LANCZOS)
            self._photo_avatar = ImageTk.PhotoImage(resized)
            self._avatar_id = self._canvas.create_image(
                cx, cy, image=self._photo_avatar, anchor=tk.CENTER
            )
        else:
            # Fallback text emoji if image missing
            self._avatar_id = self._canvas.create_text(
                cx, cy, text="😎", font=("Segoe UI Emoji", 20),
            )

        # Pill window (separate transparent Toplevel docked next to orb)
        self._pill_win = tk.Toplevel(self.root)
        self._pill_win.overrideredirect(True)
        self._pill_win.wm_attributes("-topmost", True)
        self._pill_win.wm_attributes("-transparentcolor", "#010101")
        self._pill_win.configure(bg="#010101")
        self._pill_win.withdraw()

        self._pill_frame = tk.Frame(
            self._pill_win, bg="#18181b",
            highlightthickness=1, highlightbackground="#27272a",
        )
        self._pill_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self._pill_dot = tk.Label(
            self._pill_frame, text="◉", font=("Segoe UI", 11, "bold"),
            bg="#18181b", fg="#52525b",
        )
        self._pill_dot.pack(side=tk.LEFT, padx=(10, 4), pady=10)

        self._pill_label = tk.Label(
            self._pill_frame, text="Novi",
            font=("Segoe UI", 10, "bold"),
            bg="#18181b", fg="#a1a1aa", anchor="w",
        )
        self._pill_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self._pill_sub_label = tk.Label(
            self._pill_frame, text="",
            font=("Segoe UI", 8),
            bg="#18181b", fg="#52525b", anchor="w",
        )
        self._pill_sub_label.pack(side=tk.LEFT, fill=tk.X, padx=(0, 10))

        # Bind mouse drag and click on orb canvas
        self._canvas.bind("<Button-1>",        self._on_click)
        self._canvas.bind("<ButtonPress-1>",   self._drag_start)
        self._canvas.bind("<B1-Motion>",       self._drag_motion)
        self._canvas.bind("<ButtonRelease-1>", self._drag_end)

        self.root.deiconify()
        self.root.after(ANIM_MS, self._tick)
        self._is_ready.set()
        self.root.mainloop()

    # ── drag logic ────────────────────────────────────────────────────────────

    def _drag_start(self, event: tk.Event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y
        self._dragging = False

    def _drag_motion(self, event: tk.Event) -> None:
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        if abs(dx) > 3 or abs(dy) > 3:
            self._dragging = True
        if self._dragging:
            x = self.root.winfo_x() + dx
            y = self.root.winfo_y() + dy
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x = max(0, min(x, sw - ORB_SIZE))
            y = max(0, min(y, sh - ORB_SIZE))
            self.root.geometry(f"+{x}+{y}")
            self._reposition_pill()

    def _drag_end(self, event: tk.Event) -> None:
        if self._dragging:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x  = self.root.winfo_x()
            y  = self.root.winfo_y()
            nx, ny = _snap_to_edge(x, y, sw, sh, config.ORB_SNAP_MARGIN)
            self.root.geometry(f"+{nx}+{ny}")
            _save_pos(nx, ny)
            self._reposition_pill()
        self._dragging = False

    def _on_click(self, event: tk.Event) -> None:
        if not self._dragging:
            if self._activate_cb:
                threading.Thread(target=self._activate_cb, daemon=True).start()

    # ── pill positioning ──────────────────────────────────────────────────────

    def _reposition_pill(self) -> None:
        """Place the pill intelligently: docked to screen edge beside the orb."""
        if not self._pill_visible:
            return
        sw  = self.root.winfo_screenwidth()
        sh  = self.root.winfo_screenheight()
        ox  = self.root.winfo_x()
        oy  = self.root.winfo_y()
        gap = 8

        # Prefer left of orb, else right
        if ox - PILL_W - gap >= 0:
            px = ox - PILL_W - gap
        elif ox + ORB_SIZE + gap + PILL_W <= sw:
            px = ox + ORB_SIZE + gap
        else:
            px = max(4, ox - (PILL_W - ORB_SIZE) // 2)

        py = oy + (ORB_SIZE - PILL_H) // 2
        py = max(4, min(py, sh - PILL_H - 4))
        self._pill_win.geometry(f"{PILL_W}x{PILL_H}+{px}+{py}")

    # ── animation tick ────────────────────────────────────────────────────────

    def _tick(self) -> None:
        if not self.root:
            return

        # 1. Process pending state messages
        try:
            while not self._msg_queue.empty():
                state, primary, sub = self._msg_queue.get_nowait()
                self._apply_state(state, primary, sub)
        except Exception:
            pass

        # 2. Perform shake frame if active
        if self._shake_frames:
            dx = self._shake_frames.pop(0)
            cur_y = self.root.winfo_y()
            self.root.geometry(f"+{self._base_x + dx}+{cur_y}")

        # 3. Dynamic animation per state
        pal = self._current_pal
        state = self._current_state
        cx, cy = ORB_SIZE // 2, ORB_SIZE // 2

        try:
            if state == "IDLE":
                # Clean unobtrusive circular bubble with 😎 emoji
                self._canvas.itemconfigure(self._bubble_id, fill=pal["bubble_bg"], outline=pal["border"], width=1.5)
                self._canvas.itemconfigure(self._glow_ring_id, outline="")
                self._canvas.itemconfigure(self._arc_spinner_id, extent=0)
                self._canvas.itemconfigure(self._arc_pulse2_id, extent=0)

            elif state == "LISTENING":
                # Subtle sky-blue breathing pulse ring around the emoji
                self._pulse_phase = (self._pulse_phase + 0.08) % (2 * math.pi)
                t = (math.sin(self._pulse_phase) + 1.0) / 2.0  # 0..1
                r = 27.0 + 2.5 * t
                ring_w = 1.5 + 1.0 * t

                self._canvas.coords(self._glow_ring_id, cx - r, cy - r, cx + r, cy + r)
                self._canvas.itemconfigure(self._glow_ring_id, outline=pal["glow"], width=ring_w)
                self._canvas.itemconfigure(self._bubble_id, fill=pal["bubble_bg"], outline=pal["border"], width=1.5)
                self._canvas.itemconfigure(self._arc_spinner_id, extent=0)
                self._canvas.itemconfigure(self._arc_pulse2_id, extent=0)

            elif state in ("THINKING", "PROCESSING"):
                # Warm amber dual-sweep radar pulse
                self._spinner_angle = (self._spinner_angle + 6.0) % 360
                self._canvas.coords(self._glow_ring_id, cx - 28, cy - 28, cx + 28, cy + 28)
                self._canvas.itemconfigure(self._glow_ring_id, outline="#78350f", width=1.0)
                self._canvas.itemconfigure(self._bubble_id, fill=pal["bubble_bg"], outline=pal["border"], width=1.5)

                self._canvas.itemconfigure(
                    self._arc_spinner_id,
                    start=self._spinner_angle, extent=75,
                    outline=pal["glow"], width=2.0,
                )
                self._canvas.itemconfigure(
                    self._arc_pulse2_id,
                    start=(self._spinner_angle + 180) % 360, extent=75,
                    outline=pal["glow"], width=2.0,
                )

            elif state == "EXECUTING":
                # Small rotating green activity indicator arc around the emoji
                self._spinner_angle = (self._spinner_angle + 8.5) % 360
                self._canvas.coords(self._glow_ring_id, cx - 28.5, cy - 28.5, cx + 28.5, cy + 28.5)
                self._canvas.itemconfigure(self._glow_ring_id, outline="#14532d", width=1.0)
                self._canvas.itemconfigure(self._bubble_id, fill=pal["bubble_bg"], outline=pal["border"], width=1.5)

                self._canvas.itemconfigure(
                    self._arc_spinner_id,
                    start=self._spinner_angle, extent=95,
                    outline=pal["glow"], width=2.5,
                )
                self._canvas.itemconfigure(self._arc_pulse2_id, extent=0)

            elif state == "TALKING":
                # Purple soundwave pulse reacting with harmonic voice ripple
                self._pulse_phase = (self._pulse_phase + 0.12) % (2 * math.pi)
                wave = 0.65 * math.sin(self._pulse_phase * 1.5) + 0.35 * math.sin(self._pulse_phase * 3.2)
                t = (wave + 1.0) / 2.0
                r = 27.0 + 3.0 * t
                ring_w = 1.5 + 1.5 * t

                self._canvas.coords(self._glow_ring_id, cx - r, cy - r, cx + r, cy + r)
                self._canvas.itemconfigure(self._glow_ring_id, outline=pal["glow"], width=ring_w)
                self._canvas.itemconfigure(self._bubble_id, fill=pal["bubble_bg"], outline=pal["border"], width=1.5)
                self._canvas.itemconfigure(self._arc_spinner_id, extent=0)
                self._canvas.itemconfigure(self._arc_pulse2_id, extent=0)

            elif state == "SCREEN ANALYZING":
                # Scanning beam sweep
                self._spinner_angle = (self._spinner_angle + 5.0) % 360
                self._canvas.coords(self._glow_ring_id, cx - 28, cy - 28, cx + 28, cy + 28)
                self._canvas.itemconfigure(self._glow_ring_id, outline="#134e4a", width=1.0)
                self._canvas.itemconfigure(self._bubble_id, fill=pal["bubble_bg"], outline=pal["border"], width=1.5)
                self._canvas.itemconfigure(
                    self._arc_spinner_id,
                    start=self._spinner_angle, extent=120,
                    outline=pal["glow"], width=2.0,
                )
                self._canvas.itemconfigure(self._arc_pulse2_id, extent=0)

            elif state == "ERROR":
                # Brief visual red error ring
                self._canvas.coords(self._glow_ring_id, cx - 29, cy - 29, cx + 29, cy + 29)
                self._canvas.itemconfigure(self._glow_ring_id, outline=pal["glow"], width=2.5)
                self._canvas.itemconfigure(self._bubble_id, fill=pal["bubble_bg"], outline=pal["border"], width=2.0)
                self._canvas.itemconfigure(self._arc_spinner_id, extent=0)
                self._canvas.itemconfigure(self._arc_pulse2_id, extent=0)

        except Exception:
            pass

        try:
            self.root.after(ANIM_MS, self._tick)
        except Exception:
            pass

    # ── state application ─────────────────────────────────────────────────────

    def _apply_state(self, state: str, primary: str, sub: str) -> None:
        # Match palette
        pal = None
        for key in _PALETTES:
            if state.startswith(key):
                pal = _PALETTES[key]
                matched_state = key
                break
        if pal is None:
            pal = _PALETTES["IDLE"]
            matched_state = "IDLE"

        self._current_pal   = pal
        self._current_state = matched_state

        is_idle  = matched_state == "IDLE"
        is_error = matched_state == "ERROR"

        # Cancel any pending auto-revert timers
        if self._error_reset_id:
            try:
                self.root.after_cancel(self._error_reset_id)
            except Exception:
                pass
            self._error_reset_id = None

        if is_idle:
            # Cancel any pending hide
            if self._hide_after_id:
                try:
                    self.root.after_cancel(self._hide_after_id)
                except Exception:
                    pass
            # Schedule pill collapse after brief delay so status is readable
            self._hide_after_id = self.root.after(HIDE_DELAY, self._collapse_to_orb)
            # Update pill content while still visible
            self._pill_label.configure(
                text=primary or "Ready",
                bg=pal["pill_bg"], fg=pal["fg"],
            )
            self._pill_sub_label.configure(
                text=sub or "Say Novi or press Ctrl+Space",
                bg=pal["pill_bg"], fg="#64748b",
            )
            self._pill_dot.configure(bg=pal["pill_bg"], fg=pal["dot"])
            self._pill_frame.configure(
                bg=pal["pill_bg"], highlightbackground="#27272a"
            )
        elif is_error:
            # Cancel pending collapse
            if self._hide_after_id:
                try:
                    self.root.after_cancel(self._hide_after_id)
                except Exception:
                    pass
                self._hide_after_id = None

            # Show pill & trigger shake
            self._show_pill(pal, primary or "Error", sub)
            self._trigger_error_shake()

            # Brief error indication: automatically return to IDLE after timeout
            self._error_reset_id = self.root.after(
                ERROR_RESET,
                lambda: self._apply_state("IDLE", "Ready", "Say Novi or press Ctrl+Space"),
            )
        else:
            # Cancel pending collapse
            if self._hide_after_id:
                try:
                    self.root.after_cancel(self._hide_after_id)
                except Exception:
                    pass
                self._hide_after_id = None

            # Show pill
            self._show_pill(pal, primary or pal["label"], sub)

    def _trigger_error_shake(self) -> None:
        """Brief visual horizontal shake for error alert."""
        if not self.root:
            return
        self._base_x = self.root.winfo_x()
        self._shake_frames = [-5, 5, -4, 4, -2, 2, 0]

    def _show_pill(self, pal: dict, primary: str, sub: str) -> None:
        # Update pill content
        display = primary if len(primary) <= 28 else primary[:25] + "…"
        sub_disp = sub[:32] + "…" if len(sub) > 32 else sub

        self._pill_label.configure(
            text=display, bg=pal["pill_bg"], fg=pal["fg"],
        )
        self._pill_sub_label.configure(
            text=sub_disp, bg=pal["pill_bg"], fg="#94a3b8",
        )
        self._pill_dot.configure(bg=pal["pill_bg"], fg=pal["dot"])
        self._pill_frame.configure(
            bg=pal["pill_bg"], highlightbackground=pal["border"]
        )

        if not self._pill_visible:
            self._pill_visible = True
            self._pill_win.deiconify()

        self._reposition_pill()

    def _collapse_to_orb(self) -> None:
        """Hide the pill and restore the orb to its quiet idle state."""
        self._pill_visible   = False
        if self._pill_win:
            self._pill_win.withdraw()
        self._current_pal    = _PALETTES["IDLE"]
        self._current_state  = "IDLE"
        self._hide_after_id  = None


# Singleton
overlay = DesktopOverlay()
