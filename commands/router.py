"""
Command router that validates and executes structured commands and sequential action chains.
Features dynamic window readiness verification, app-specific workflows, and reliable Spotify/Office integration.
"""

import time
import pyautogui
from typing import Tuple, Optional, Callable
from commands.schema import Command, ActionChain
import config
import tools.browser as browser_tool
import tools.applications as app_tool
import tools.keyboard as keyboard_tool
import tools.feedback as feedback_tool
import tools.timers as timer_tool
import tools.system as system_tool
import tools.spotify as spotify_tool
import tools.office_workflows as office_tool
import tools.window_manager as window_mgr


class CommandRouter:
    """Dispatches validated Command and ActionChain objects to appropriate tools."""

    def _execute_single_tool(self, command: Command) -> Tuple[bool, str, str]:
        """
        Executes a single command tool without firing feedback (used by chains & execute).
        Returns: (success, result_message, spoken_text)
        """
        success = False
        message = ""
        spoken = ""

        if command.action == "open_url":
            url = command.parameters["url"]
            success, message = browser_tool.open_url(url)
            spoken = f"Opening {url}"

        elif command.action == "web_search":
            query = command.parameters["query"]
            success, message = browser_tool.search_web(query)
            spoken = f"Searching Google for {query}"

        elif command.action == "youtube_search":
            query = command.parameters["query"]
            success, message = browser_tool.search_youtube(query)
            spoken = f"Searching YouTube for {query}"

        elif command.action == "maps_search":
            query = command.parameters["query"]
            success, message = browser_tool.search_maps(query)
            spoken = f"Searching Google Maps for {query}"

        elif command.action == "amazon_search":
            query = command.parameters["query"]
            success, message = browser_tool.search_amazon(query)
            spoken = f"Searching Amazon for {query}"


        elif command.action == "open_app":
            app = command.parameters["app"]
            success, message = app_tool.launch_app(app)
            spoken = f"Opening {app}"

        elif command.action == "type_text":
            text = command.parameters["text"]
            success, message = keyboard_tool.type_text(text)
            spoken = "Typed requested text"

        elif command.action == "keypress":
            key = command.parameters["key"]
            success, message = keyboard_tool.press_key(key)
            spoken = f"Pressed {key}"

        elif command.action == "set_timer":
            seconds = command.parameters["seconds"]
            label = command.parameters.get("label", "")
            success, message = timer_tool.set_timer(seconds, label)
            spoken = message

        elif command.action == "adjust_volume":
            act = command.parameters["action"]
            success, message = system_tool.adjust_volume(act)
            spoken = message

        elif command.action == "control_media":
            act = command.parameters["action"]
            success, message = system_tool.control_media(act)
            spoken = message

        elif command.action == "control_window":
            act = command.parameters["action"]
            success, message = system_tool.control_window(act)
            spoken = message

        elif command.action == "take_screenshot":
            success, message = system_tool.take_screenshot()
            spoken = "Screenshot captured"

        elif command.action == "get_time":
            info_type = command.parameters.get("type", "time")
            success, message = system_tool.get_current_time_date(info_type)
            spoken = message

        elif command.action == "play_spotify":
            query = command.parameters["query"]
            success, message = spotify_tool.play_spotify_track(query)
            spoken = f"Playing {query} on Spotify"

        elif command.action == "create_blank_document":
            target_app = command.parameters.get("app", "word").lower()
            if target_app == "word":
                success, message = office_tool.open_word_and_prepare_document()
                spoken = "Created blank Word document"
            elif target_app == "powerpoint":
                success, message = office_tool.open_powerpoint_and_prepare_presentation()
                spoken = "Created blank presentation"
            else:
                success = False
                message = f"Unsupported blank document app: {target_app}"
                spoken = "Unsupported document type"

        elif command.action == "browser_nav":
            nav_action = command.parameters["action"]
            try:
                if nav_action == "back":
                    pyautogui.hotkey("alt", "left")
                    success, message = True, "Navigated back"
                elif nav_action == "forward":
                    pyautogui.hotkey("alt", "right")
                    success, message = True, "Navigated forward"
                elif nav_action == "refresh":
                    pyautogui.press("f5")
                    success, message = True, "Refreshed page"
                elif nav_action == "scroll_down":
                    pyautogui.scroll(-600)
                    success, message = True, "Scrolled down"
                elif nav_action == "scroll_up":
                    pyautogui.scroll(600)
                    success, message = True, "Scrolled up"
                spoken = message
            except Exception as e:
                success, message = False, f"Navigation failed: {e}"
                spoken = "Navigation failed"

        else:
            success = False
            message = f"Unhandled action '{command.action}'"
            spoken = "Unsupported command"

        return success, message, spoken

    def execute(self, command: Command) -> Tuple[bool, str]:
        """Execute a single validated command."""
        is_valid, error = command.validate()
        if not is_valid:
            msg = f"Command validation failed: {error}"
            print(f"[❌] {msg}")
            feedback_tool.provide_feedback(msg, "Action validation failed.")
            return False, msg

        print(f"\n[🚀 EXECUTING] Action: '{command.action}' | Parameters: {command.parameters}")
        success, message, spoken = self._execute_single_tool(command)
        feedback_tool.provide_feedback(message, spoken)
        return success, message

    def execute_chain(
        self,
        chain: ActionChain,
        progress_callback: Optional[Callable[[int, int, Command, str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Executes a sequence of actions with full chain validation and dynamic window verification.
        Stops immediately if any action fails.
        """
        # 1. Validate complete chain upfront
        is_valid, err = chain.validate()
        if not is_valid:
            msg = f"Chain validation failed: {err}"
            print(f"[❌] {msg}")
            feedback_tool.provide_feedback(msg, "I could not execute that sequence because a step is invalid.")
            return False, msg

        total = len(chain.actions)
        print(f"\n[⚡ EXECUTING CHAIN] Total steps: {total}")

        executed_descriptions = []

        for idx, cmd in enumerate(chain.actions):
            step_num = idx + 1
            step_desc = f"{cmd.action}: {list(cmd.parameters.values())[0] if cmd.parameters else ''}"
            print(f"\n  [Step {step_num}/{total}] {cmd.action} -> {cmd.parameters}")

            if progress_callback:
                progress_callback(step_num, total, cmd, step_desc)

            success, msg, spoken = self._execute_single_tool(cmd)

            if not success:
                error_msg = f"{msg}"
                print(f"[❌ Error]: Chain stopped at step {step_num}/{total}: {error_msg}")
                feedback_tool.provide_feedback(error_msg, f"Stopped at step {step_num}. {error_msg}")
                return False, error_msg

            executed_descriptions.append(spoken if spoken else cmd.action)

            # Smart dynamic window verification & readiness
            if step_num < total:
                if cmd.action == "open_app":
                    app_name = cmd.parameters.get("app", "")
                    print(f"  [⏳ Verifying window readiness for '{app_name}'...]")
                    hwnd = window_mgr.wait_for_window(app_name, timeout=6.0, ensure_foreground=True)
                    if not hwnd:
                        stop_msg = f"{app_name.capitalize()} didn't appear to open, so I stopped the task."
                        print(f"[❌ Focus Verification Failed]: {stop_msg}")
                        feedback_tool.provide_feedback(stop_msg, stop_msg)
                        return False, stop_msg
                    time.sleep(0.3)
                elif cmd.action in ("open_url", "web_search", "youtube_search", "maps_search", "amazon_search"):
                    time.sleep(config.URL_OPEN_WAIT)
                else:
                    time.sleep(config.ACTION_STEP_WAIT)

        summary_msg = f"Successfully executed all {total} actions."
        spoken_summary = f"Done. Executed {total} actions."
        feedback_tool.provide_feedback(summary_msg, spoken_summary)
        return True, summary_msg
