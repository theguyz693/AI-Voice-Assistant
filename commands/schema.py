"""
Command schema definitions, validation, and multi-step action chains.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


SUPPORTED_ACTIONS = {
    "open_url",
    "web_search",
    "youtube_search",
    "maps_search",
    "amazon_search",
    "open_app",

    "type_text",
    "keypress",
    "set_timer",
    "adjust_volume",
    "control_media",
    "control_window",
    "take_screenshot",
    "get_time",
    "screen_query",
    "play_spotify",
    "create_blank_document",
    "browser_nav",
}


@dataclass
class Command:
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_transcript: str = ""

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the command action and required parameters.
        Returns: (is_valid, error_message)
        """
        if self.action not in SUPPORTED_ACTIONS:
            return False, f"Unsupported action: '{self.action}'."

        if self.action == "open_url":
            url = self.parameters.get("url")
            if not url or not isinstance(url, str):
                return False, "Missing or invalid 'url' parameter for open_url."

        elif self.action in ("web_search", "youtube_search", "maps_search", "amazon_search"):
            query = self.parameters.get("query")
            if not query or not isinstance(query, str):
                return False, f"Missing or invalid 'query' parameter for {self.action}."


        elif self.action == "open_app":
            app = self.parameters.get("app")
            if not app or not isinstance(app, str):
                return False, "Missing or invalid 'app' parameter for open_app."

        elif self.action == "type_text":
            text = self.parameters.get("text")
            if text is None or not isinstance(text, str):
                return False, "Missing or invalid 'text' parameter for type_text."

        elif self.action == "keypress":
            key = self.parameters.get("key")
            if not key or not isinstance(key, str):
                return False, "Missing or invalid 'key' parameter for keypress."

        elif self.action == "set_timer":
            seconds = self.parameters.get("seconds")
            if seconds is None or not isinstance(seconds, (int, float)) or seconds <= 0:
                return False, "Missing or invalid 'seconds' parameter for set_timer."

        elif self.action == "play_spotify":
            query = self.parameters.get("query")
            if not query or not isinstance(query, str):
                return False, "Missing or invalid 'query' parameter for play_spotify."

        elif self.action == "create_blank_document":
            app = self.parameters.get("app", "word")
            if app not in ("word", "powerpoint"):
                return False, f"Unsupported app for blank document: '{app}'. Use 'word' or 'powerpoint'."

        elif self.action == "browser_nav":
            nav = self.parameters.get("action")
            if nav not in ("back", "forward", "refresh", "scroll_down", "scroll_up"):
                return False, f"Unsupported browser navigation action: '{nav}'."

        elif self.action == "screen_query":
            pass

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "parameters": self.parameters,
        }


@dataclass
class ActionChain:
    """Represents a sequential chain of one or more validated actions."""
    actions: List[Command] = field(default_factory=list)
    raw_transcript: str = ""

    def validate(self) -> tuple[bool, Optional[str]]:
        if not self.actions:
            return False, "Action chain contains no actions."
        for idx, cmd in enumerate(self.actions):
            is_valid, err = cmd.validate()
            if not is_valid:
                return False, f"Step {idx + 1} ('{cmd.action}') failed: {err}"
        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actions": [cmd.to_dict() for cmd in self.actions]
        }


@dataclass
class IntentResult:
    """
    Unified representation of an interpreted user utterance:
    - type: 'action' (contains ActionChain)
    - type: 'conversation' (contains response_text)
    - type: 'screen_query' (contains question for on-demand vision analysis)
    """
    intent_type: str  # "action", "conversation", "screen_query"
    chain: Optional[ActionChain] = None
    response_text: Optional[str] = None
    raw_transcript: str = ""
