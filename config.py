"""
Configuration settings for the Voice Assistant.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).parent.resolve()

# Audio & Recording Settings
SAMPLE_RATE = 16000          # 16kHz sample rate optimal for Whisper
CHANNELS = 1                 # Mono channel
CHUNK_SIZE = 1024            # Buffer size for reading audio frames
SILENCE_THRESHOLD = 0.015    # RMS energy threshold below which audio is considered silence
SILENCE_DURATION = 1.3       # Seconds of silence after speech before stopping recording
MIN_SPEECH_DURATION = 0.4    # Minimum seconds of detected speech to consider valid
MAX_RECORD_SECONDS = 12.0    # Maximum recording duration safety cap

# Speech to Text Settings
STT_MODEL_SIZE = "tiny.en"   # Options: "tiny.en", "base.en", "small.en"
STT_DEVICE = "cpu"           # "cpu" or "cuda"
STT_COMPUTE_TYPE = "int8"    # "int8" for CPU efficiency

# Hotkey Settings
HOTKEY = "ctrl+space"

# Wake Word Settings
WAKE_WORD_ENABLED   = True        # Continuous local wake-word detection
WAKE_WORD           = "novi"      # Wake word (case-insensitive)
WAKE_WORD_CHUNK_S   = 1.2        # Seconds of audio per wake-word check window
WAKE_WORD_RMS_GATE  = 0.008      # Minimum RMS to bother running STT (silence skip)

# Orb UI Settings
ORB_SNAP_MARGIN     = 20          # px — how close to edge the orb snaps
ORB_POSITION_FILE   = "orb_position.txt"  # Saved relative to BASE_DIR
ORB_ICON_FILE       = "ui/assets/pngegg.png"  # Avatar emoji icon (relative to BASE_DIR)


# Feedback & TTS Settings
ENABLE_TTS_FEEDBACK = True   # Spoken confirmation for completed actions

# UI Overlay Settings
ENABLE_UI_OVERLAY = True     # Floating desktop visual status overlay

# Local LLM (Ollama) Settings
USE_LOCAL_LLM = True         # Enabled: Uses local models via Ollama
COMMAND_MODEL = "llama3.2:1b"       # Fast intent extraction & structured action chains
CHAT_MODEL = "qwen2.5:7b"           # Conversational AI for casual chat & explanations
VISION_MODEL = "moondream:latest"   # Lightweight on-demand screen awareness
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"

# Action Chaining Timing (seconds)
APP_LAUNCH_WAIT = 2.0        # Max fallback timeout after launching an app before next action
URL_OPEN_WAIT = 0.8          # Time to wait after opening a URL
ACTION_STEP_WAIT = 0.3       # Inter-action transition delay for sequential chains

# Conversational AI Settings
MAX_CONVERSATION_HISTORY = 6 # Bounded short-term memory (number of message turns)
CONVERSATION_SYSTEM_PROMPT = """You are a chill, friendly, and helpful personal voice assistant running locally on Windows 11.
Keep responses concise, conversational, and natural (1 to 4 sentences typically).
Never output markdown code blocks, bulleted essays, or robotic greetings unless explicitly asked.
Speak directly and naturally like a knowledgeable friend."""




# Configurable Application Mapping (Windows shortcuts / commands)
APPS = {
    # Browsers
    "chrome": "start chrome",
    "google chrome": "start chrome",
    "edge": "start msedge",
    "microsoft edge": "start msedge",
    "brave": "start brave",
    "firefox": "start firefox",

    # Productivity & Office
    "powerpoint": "start powerpnt",
    "power point": "start powerpnt",
    "ppt": "start powerpnt",
    "word": "start winword",
    "microsoft word": "start winword",
    "excel": "start excel",
    "microsoft excel": "start excel",
    "outlook": "start outlook",
    "onenote": "start onenote",
    "notepad": "notepad",
    "calculator": "calc",
    "clock": "start ms-clock:",

    # Development
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "terminal": "wt",
    "windows terminal": "wt",
    "powershell": "powershell",
    "cmd": "cmd",

    # Utilities & Windows System
    "task manager": "taskmgr",
    "settings": "start ms-settings:",
    "file explorer": "explorer",
    "explorer": "explorer",
    "paint": "mspaint",
    "camera": "start microsoft.windows.camera:",
    "snipping tool": "start snippingtool",
    "recycle bin": "start shell:RecycleBinFolder",
    "downloads": "start shell:Downloads",
    "documents": "start shell:Personal",

    # Media & Social
    "spotify": "spotify",
    "whatsapp": "start whatsapp:",
    "discord": "start discord",
    "steam": "start steam",
}

# Configurable Shortcut Websites
WEBSITES = {
    "neetcode": "https://neetcode.io",
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "chatgpt": "https://chatgpt.com",
    "claude": "https://claude.ai",
    "stackoverflow": "https://stackoverflow.com",
    "gmail": "https://mail.google.com",
    "netflix": "https://netflix.com",
    "amazon": "https://amazon.com",
}
