# Desktop Voice Assistant — Orb Edition

A local desktop voice assistant for Windows featuring an interactive floating orb, real-time speech-to-text, local LLM-powered command routing, screen awareness, and desktop automation.

---

## Features

- **Interactive Floating Orb UI**: Draggable overlay that snaps to screen edges, displays assistant status (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`), and supports click activation.
- **Hands-Free Wake Word & Hotkey**: Trigger assistant by saying **"Novi"** or pressing **`Ctrl + Space`**.
- **Local Speech-to-Text**: Fast offline transcription powered by [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) (`tiny.en` on CPU/int8).
- **Local LLM Intelligence (Ollama)**:
  - **Command Routing & Action Chains**: Fast multi-step task execution via `llama3.2:1b`.
  - **Conversational Chat**: Casual conversation with short-term context memory via `qwen2.5:7b`.
  - **Screen Vision**: On-demand screen understanding and visual Q&A via `moondream`.
- **Desktop Automation**:
  - Launch applications and open web URLs/searches.
  - Spotify playback control (play, pause, next, volume).
  - Window management (minimize, maximize, focus, close).
  - Timers, alarms, keyboard simulation, and system volume control.
- **Offline TTS Feedback**: Spoken feedback via `pyttsx3`.

---

## Prerequisites

1. **Python 3.10+** on Windows.
2. **Working Microphone & Audio Output**.
3. **[Ollama](https://ollama.com/)** installed and running locally:
   ```bash
   ollama pull llama3.2:1b
   ollama pull qwen2.5:7b
   ollama pull moondream:latest
   ```

---

## Installation

1. Clone or navigate to the repository directory:
   ```bash
   cd c:\va
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

Start the assistant:
```bash
python main.py
```

### Interacting with the Assistant
- **Wake Word**: Say **"Novi"** followed by your command (e.g., *"Novi, open Spotify and play music"*).
- **Hotkey**: Press `Ctrl + Space` to start recording.
- **Orb UI**: Click the floating duck orb on your desktop.
- **Exit**: Close the console window or press `Ctrl + C` in the terminal.

---

## Configuration

Customizable parameters can be found in `config.py`:
- `HOTKEY`: Activation hotkey (default: `ctrl+space`).
- `WAKE_WORD`: Continuous wake word (default: `novi`).
- `STT_MODEL_SIZE`: Whisper model size (`tiny.en`, `base.en`, `small.en`).
- `COMMAND_MODEL` / `CHAT_MODEL` / `VISION_MODEL`: Ollama model tags.
- `ENABLE_UI_OVERLAY`: Toggle the floating desktop orb.
- `ENABLE_TTS_FEEDBACK`: Enable/disable voice response audio.
