"""
Main entry point for Voice Assistant.
Pipeline:
  - Floating orb UI (click / Ctrl+Space / "Novi" wake word)
  - Microphone capture with RMS voice activity detection
  - faster-whisper local STT
  - Intent Routing:
      -> Conversational AI mode with bounded context memory
      -> Sequential multi-step Action Chains with safety validation & timing
      -> On-demand Screen Awareness
  - Dynamic Orb UI overlay & Offline TTS voice feedback
"""

import sys
import time
import json
import threading

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import keyboard
import config
from audio.microphone import MicrophoneRecorder
from audio.speech_to_text import SpeechToText
from audio.wake_word import WakeWordListener
from ai.command_interpreter import CommandInterpreter
from commands.router import CommandRouter
from commands.schema import Command, ActionChain, IntentResult
import tools.feedback as feedback_tool
import tools.screen_vision as screen_tool
from ui.overlay import overlay


class VoiceAssistant:
    def __init__(self):
        print("=" * 68)
        print("  Local Desktop Voice Assistant — Orb Edition")
        print("=" * 68)

        # 1. Start UI Orb overlay
        if config.ENABLE_UI_OVERLAY:
            overlay.start()
            overlay.set_activate_callback(self._on_orb_click)
            overlay.set_state("IDLE", "Ready", "Say Novi or press Ctrl+Space")

        # 2. Initialize STT and load local model
        self.stt = SpeechToText()
        self.stt.load_model()

        # 3. Audio recorder & wake-word listener
        self.recorder = MicrophoneRecorder()

        # 4. Command interpreter and execution router
        self.interpreter = CommandInterpreter()
        self.router = CommandRouter()

        # 5. Wake-word listener (shares the STT model)
        self._wake_listener: WakeWordListener | None = None
        if config.WAKE_WORD_ENABLED:
            self._wake_listener = WakeWordListener(
                stt_model=self.stt,
                activate_callback=self._on_wake_word,
            )

        self.is_busy = False
        self._lock = threading.Lock()

    # ── activation callbacks ──────────────────────────────────────────────────

    def _on_orb_click(self) -> None:
        """Called when the user clicks the orb bubble."""
        print("\n[Orb Click] Activating...")
        self.trigger_recording_session()

    def _on_wake_word(self, post_wake_audio=None) -> None:
        """
        Called by WakeWordListener when 'Novi' is detected.
        If post_wake_audio contains a command, run it directly;
        otherwise trigger a fresh recording session.
        """
        print("\n[Wake Word] 'Novi' detected — activating pipeline...")
        self.trigger_recording_session(prefetched_audio=post_wake_audio)

    # ── UI helpers ────────────────────────────────────────────────────────────

    def _on_start_listening(self):
        print("\n[🎙️  LISTENING...] Speak now...")
        if config.ENABLE_UI_OVERLAY:
            overlay.set_state("LISTENING", "Listening…", "Speak now")

    def _on_speech_started(self):
        print("[🗣️  SPEECH DETECTED] Recording...")
        if config.ENABLE_UI_OVERLAY:
            overlay.set_state("LISTENING", "Recording…", "Keep speaking")

    # ── core pipeline ─────────────────────────────────────────────────────────

    def trigger_recording_session(self, prefetched_audio=None) -> None:
        """
        Run a single recording → STT → intent → execution cycle.
        If prefetched_audio is provided (from wake-word same-breath detection),
        skip re-recording and transcribe it directly.
        """
        with self._lock:
            if self.is_busy:
                if self.recorder.is_recording:
                    print("\n[🛑] Stop requested.")
                    self.recorder.stop()
                return
            self.is_busy = True

        # Pause wake-word while pipeline runs
        if self._wake_listener:
            self._wake_listener.pause()

        def worker():
            try:
                # ── 1. Audio Capture ──────────────────────────────────────────
                if prefetched_audio is not None and len(prefetched_audio) > 0:
                    audio = prefetched_audio
                    print("[Wake] Using same-breath audio from wake-word window.")
                    self._on_start_listening()
                else:
                    audio = self.recorder.record_phrase(
                        on_start_listening=self._on_start_listening,
                        on_speech_started=self._on_speech_started,
                    )

                if audio is None or len(audio) == 0:
                    print("[⚠️] No speech detected.")
                    if config.ENABLE_UI_OVERLAY:
                        overlay.set_state("IDLE", "Ready", "No speech detected")
                    return

                # ── 2. STT ────────────────────────────────────────────────────
                print("[⚙️  TRANSCRIBING...] Processing voice...")
                if config.ENABLE_UI_OVERLAY:
                    overlay.set_state("PROCESSING", "Transcribing…", "")

                start_t    = time.time()
                transcript = self.stt.transcribe(audio)
                dur        = time.time() - start_t

                if not transcript:
                    print("[⚠️] No recognizable words.")
                    if config.ENABLE_UI_OVERLAY:
                        overlay.set_state("ERROR", "No words recognized", "Try again")
                    return

                # Strip leading wake word if it slipped through
                ww = config.WAKE_WORD.lower()
                stripped = transcript.strip()
                stripped_lower = stripped.lower().lstrip(" ,.")
                if stripped_lower.startswith(ww):
                    stripped = stripped[len(ww):].lstrip(" ,.")
                    if stripped:
                        transcript = stripped

                print("\n" + "=" * 52)
                print(f'[📝 TRANSCRIPT] ({dur:.2f}s): "{transcript}"')
                print("=" * 52)

                # ── 3. Intent Interpretation ──────────────────────────────────
                if config.ENABLE_UI_OVERLAY:
                    overlay.set_state("THINKING", "Analyzing…", f'"{transcript[:40]}"')

                intent_res: IntentResult = self.interpreter.interpret_intent(transcript)

                if not intent_res:
                    msg = f"Could not interpret: '{transcript}'"
                    print(f"[❓] {msg}")
                    if config.ENABLE_UI_OVERLAY:
                        overlay.set_state("ERROR", "Not recognized", f'"{transcript[:30]}"')
                    feedback_tool.provide_feedback("I didn't catch that. Could you repeat?")
                    time.sleep(2.0)
                    return

                # ── 4. Route by Intent ────────────────────────────────────────

                if intent_res.intent_type == "conversation":
                    reply = intent_res.response_text
                    print(f"\n[💬 CHAT]: {reply}")
                    if config.ENABLE_UI_OVERLAY:
                        overlay.set_state("TALKING", "Speaking…", reply[:40])
                    feedback_tool.provide_feedback(reply)
                    time.sleep(2.5)

                elif intent_res.intent_type == "screen_query":
                    question = intent_res.response_text or transcript
                    if config.ENABLE_UI_OVERLAY:
                        overlay.set_state("SCREEN ANALYZING", "Inspecting…", question[:40])
                    success, display_text, spoken_text = screen_tool.analyze_screen(question)
                    if config.ENABLE_UI_OVERLAY:
                        overlay.set_state(
                            "TALKING" if success else "ERROR",
                            "Screen Analysis",
                            spoken_text[:40],
                        )
                    feedback_tool.provide_feedback(display_text, spoken_text)
                    time.sleep(3.0)

                elif intent_res.intent_type == "action" and intent_res.chain:
                    chain: ActionChain = intent_res.chain
                    total = len(chain.actions)

                    print(f"\n[🧠 ACTION CHAIN ({total} step{'s' if total > 1 else ''}):]")
                    print(json.dumps(chain.to_dict(), indent=2))

                    def on_step_progress(step_num, total_steps, cmd: Command, desc: str):
                        if config.ENABLE_UI_OVERLAY:
                            overlay.set_state(
                                f"EXECUTING {step_num}/{total_steps}",
                                cmd.action,
                                f"Step {step_num}: {desc}",
                            )

                    success, result_msg = self.router.execute_chain(
                        chain, progress_callback=on_step_progress
                    )
                    if config.ENABLE_UI_OVERLAY:
                        overlay.set_state(
                            "EXECUTING" if success else "ERROR",
                            "Done" if success else "Failed",
                            result_msg[:40],
                        )
                    time.sleep(2.0)

            except Exception as e:
                print(f"[❌ Pipeline Error]: {e}")
                if config.ENABLE_UI_OVERLAY:
                    overlay.set_state("ERROR", "Error", str(e)[:40])
                time.sleep(2.0)
            finally:
                with self._lock:
                    self.is_busy = False
                # Resume wake-word detection
                if self._wake_listener:
                    self._wake_listener.resume()
                if config.ENABLE_UI_OVERLAY:
                    overlay.set_state("IDLE", "Ready", "Say Novi or press Ctrl+Space")
                print(f"\n[🟢 READY] Say 'Novi' or press {config.HOTKEY.upper()} to speak.\n")

        threading.Thread(target=worker, daemon=True).start()

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        print(f"\n[🟢 READY] Orb assistant active!")
        print(f"  -> Wake word : say '{config.WAKE_WORD.capitalize()}' (e.g. 'Novi, open Spotify')")
        print(f"  -> Hotkey   : [{config.HOTKEY.upper()}]")
        print(f"  -> Orb click: click the floating orb")
        print(f"  -> Text test: type 'cmd: <command>' and press Enter")
        print(f"  -> Reset mem: type 'reset' and press Enter")
        print(f"  -> Exit     : Ctrl+C\n")

        # Start wake-word listener
        if self._wake_listener:
            self._wake_listener.start()

        # Register global hotkey
        try:
            keyboard.add_hotkey(config.HOTKEY, self.trigger_recording_session)
        except Exception as e:
            print(f"[⚠️] Global hotkey '{config.HOTKEY}' failed: {e}")

        # Interactive terminal fallback loop
        try:
            while True:
                line = sys.stdin.readline()
                if line == "":
                    break
                text_input = line.strip()
                if not text_input:
                    self.trigger_recording_session()
                elif text_input == "reset":
                    self.interpreter.reset_conversation_history()
                    print("\n[🧹 Memory Reset] Conversational history cleared.")
                elif text_input.startswith("cmd:"):
                    raw_cmd = text_input[4:].strip()
                    print(f'\n[🧪 Testing]: "{raw_cmd}"')
                    intent_res = self.interpreter.interpret_intent(raw_cmd)
                    if intent_res:
                        if intent_res.intent_type == "conversation":
                            print(f"[💬 Chat]: {intent_res.response_text}")
                            feedback_tool.provide_feedback(intent_res.response_text)
                        elif intent_res.intent_type == "screen_query":
                            success, disp, spk = screen_tool.analyze_screen(
                                intent_res.response_text
                            )
                            feedback_tool.provide_feedback(disp, spk)
                        elif intent_res.intent_type == "action" and intent_res.chain:
                            print(
                                f"[🧠 Chain]: {json.dumps(intent_res.chain.to_dict(), indent=2)}"
                            )
                            self.router.execute_chain(intent_res.chain)
                    else:
                        print("[❓] Not recognized.")
                else:
                    self.trigger_recording_session()
        except KeyboardInterrupt:
            print("\n[👋] Shutting down...")
        finally:
            if self._wake_listener:
                self._wake_listener.stop()
            try:
                keyboard.unhook_all()
            except Exception:
                pass


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
