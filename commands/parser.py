"""
Rule-based Command Parser for all supported actions, basic chains, and conversational fallbacks.
Converts transcribed natural language into validated Command or ActionChain instances.
"""

import re
from typing import Optional, List
import config
from commands.schema import Command, ActionChain, IntentResult
from tools.timers import parse_time_duration


class CommandParser:
    """Deterministic rule-based parser serving as reliable fallback for local LLM."""

    def parse(self, transcript: str) -> Optional[Command]:
        if not transcript or not transcript.strip():
            return None

        # Clean punctuation and normalize whitespace
        text = transcript.strip()
        lower = text.lower()
        clean_lower = re.sub(r"[.?!,]+$", "", lower).strip()

        # 1. Type text: "type ...", "type: ...", "write ..."
        match_type = re.match(r"^(?:type[:]?\s+|write[:]?\s+)(.+)$", text, re.IGNORECASE)
        if match_type:
            raw_content = match_type.group(1).strip()
            return Command(action="type_text", parameters={"text": raw_content}, raw_transcript=text)

        # 2. Timers and Stopwatches: "set a timer for ...", "start a stopwatch of ...", "timer 5 minutes"
        match_timer = re.match(
            r"^(?:set\s+(?:a\s+)?timer\s+(?:for|of)\s+|start\s+(?:a\s+)?(?:timer|stopwatch)\s+(?:for|of)\s+|timer\s+(?:for\s+)?)(.+)$",
            clean_lower,
        )
        if match_timer:
            dur_str = match_timer.group(1).strip()
            seconds = parse_time_duration(dur_str)
            if seconds > 0:
                return Command(
                    action="set_timer",
                    parameters={"seconds": seconds, "label": dur_str},
                    raw_transcript=text,
                )

        # 3. YouTube Search: "search youtube for ...", "youtube search ...", "youtube ..."
        match_yt = re.match(
            r"^(?:search\s+youtube\s+for\s+|search\s+on\s+youtube\s+for\s+|youtube\s+search\s+|youtube\s+)(.+)$",
            clean_lower,
        )
        if match_yt:
            query = match_yt.group(1).strip()
            return Command(action="youtube_search", parameters={"query": query}, raw_transcript=text)

        # 4a. Google Maps Search — several natural phrasings
        # "open google maps and search for X", "maps search for X", "google maps search X"
        match_maps_search = re.match(
            r"^(?:(?:open\s+)?(?:google\s+)?maps?\s+(?:and\s+)?(?:search|look|find)\s+(?:for\s+)?)(.+)$",
            clean_lower,
        )
        if match_maps_search:
            query = match_maps_search.group(1).strip()
            if query:
                return Command(action="maps_search", parameters={"query": query}, raw_transcript=text)

        # "find X on maps", "find X on google maps"
        match_find_on_maps = re.match(
            r"^find\s+(.+?)\s+on\s+(?:google\s+)?maps?$",
            clean_lower,
        )
        if match_find_on_maps:
            query = match_find_on_maps.group(1).strip()
            if query:
                return Command(action="maps_search", parameters={"query": query}, raw_transcript=text)

        # "directions to X", "navigate to X"
        match_directions = re.match(r"^(?:directions?\s+to\s+|navigate\s+to\s+)(.+)$", clean_lower)
        if match_directions:
            query = match_directions.group(1).strip()
            return Command(action="maps_search", parameters={"query": query}, raw_transcript=text)

        # 4b. Amazon Search — several natural phrasings
        # "search amazon for X", "open amazon and search for X", "amazon search X"
        match_amazon_search = re.match(
            r"^(?:(?:open\s+)?amazon(?:\.com)?\s+(?:and\s+)?(?:search|look|find)\s+(?:for\s+)?|search\s+(?:on\s+)?amazon(?:\.com)?\s+(?:for\s+)?)(.+)$",
            clean_lower,
        )
        if match_amazon_search:
            query = match_amazon_search.group(1).strip()
            if query:
                return Command(action="amazon_search", parameters={"query": query}, raw_transcript=text)

        # "find X on amazon", "look for X on amazon.com"
        match_find_on_amazon = re.match(
            r"^(?:find|look\s+for|search\s+for)\s+(.+?)\s+on\s+amazon(?:\.com)?$",
            clean_lower,
        )
        if match_find_on_amazon:
            query = match_find_on_amazon.group(1).strip()
            if query:
                return Command(action="amazon_search", parameters={"query": query}, raw_transcript=text)

        # 4. Google / Web Search: "search google for ...", "search for ...", "search on google for ...", "google search ...", "google ...", "search ..."
        match_search = re.match(
            r"^(?:search\s+google\s+for\s+|search\s+for\s+|search\s+on\s+google\s+for\s+|google\s+search\s+|google\s+|search\s+)(.+)$",
            clean_lower,
        )
        if match_search:
            query = match_search.group(1).strip()
            return Command(action="web_search", parameters={"query": query}, raw_transcript=text)

        # 5. Volume Controls
        if re.search(r"\b(?:turn\s+up\s+volume|volume\s+up|increase\s+volume|louder)\b", clean_lower):
            return Command(action="adjust_volume", parameters={"action": "up"}, raw_transcript=text)
        if re.search(r"\b(?:turn\s+down\s+volume|volume\s+down|decrease\s+volume|quieter)\b", clean_lower):
            return Command(action="adjust_volume", parameters={"action": "down"}, raw_transcript=text)
        if re.search(r"\b(?:mute\s+volume|mute|unmute)\b", clean_lower):
            return Command(action="adjust_volume", parameters={"action": "mute"}, raw_transcript=text)

        # 6. Media Playback Controls
        if re.search(r"\b(?:next\s+track|next\s+song|skip\s+song)\b", clean_lower):
            return Command(action="control_media", parameters={"action": "next"}, raw_transcript=text)
        if re.search(r"\b(?:previous\s+track|previous\s+song|prev\s+track)\b", clean_lower):
            return Command(action="control_media", parameters={"action": "previous"}, raw_transcript=text)
        if re.search(r"\b(?:pause\s+music|play\s+music|pause|resume|play)\b", clean_lower):
            return Command(action="control_media", parameters={"action": "playpause"}, raw_transcript=text)

        # 7. Screenshot
        if re.search(r"\b(?:take\s+(?:a\s+)?screenshot|capture\s+screen|screenshot)\b", clean_lower):
            return Command(action="take_screenshot", parameters={}, raw_transcript=text)

        # 8. Time / Date queries
        if re.search(r"\b(?:what\s+time\s+is\s+it|what's\s+the\s+time|current\s+time)\b", clean_lower):
            return Command(action="get_time", parameters={"type": "time"}, raw_transcript=text)
        if re.search(r"\b(?:what\s+date\s+is\s+it|what's\s+today's\s+date|what\s+day\s+is\s+it|today's\s+date)\b", clean_lower):
            return Command(action="get_time", parameters={"type": "date"}, raw_transcript=text)

        # 9. Window Controls
        if re.search(r"\b(?:minimize\s+window|minimize)\b", clean_lower):
            return Command(action="control_window", parameters={"action": "minimize"}, raw_transcript=text)
        if re.search(r"\b(?:maximize\s+window|maximize)\b", clean_lower):
            return Command(action="control_window", parameters={"action": "maximize"}, raw_transcript=text)
        if re.search(r"\b(?:close\s+window|close\s+app)\b", clean_lower):
            return Command(action="control_window", parameters={"action": "close"}, raw_transcript=text)

        # 10. Safe Keypress actions
        match_key = re.match(
            r"^(?:press\s+)?(enter|escape|esc|tab|space|backspace|copy|paste|cut|undo|redo|select all|save|control shift p|ctrl shift p)$",
            clean_lower,
        )
        if match_key:
            key_name = match_key.group(1).strip()
            return Command(action="keypress", parameters={"key": key_name}, raw_transcript=text)

        # 11. Open Website or Application: "open ..."
        match_open = re.match(r"^(?:open|launch|start)\s+(.+)$", clean_lower)
        if match_open:
            target = match_open.group(1).strip()

            # Check if target is a known website shortcut
            if target in config.WEBSITES:
                return Command(
                    action="open_url",
                    parameters={"url": config.WEBSITES[target]},
                    raw_transcript=text,
                )

            # Check if target is a known app shortcut
            if target in config.APPS:
                return Command(
                    action="open_app",
                    parameters={"app": target},
                    raw_transcript=text,
                )

            # Check if target looks like a web URL
            if re.search(r"(?:https?://|\.com|\.org|\.io|\.net|\.dev|\.edu|\.ai)", target):
                url = target if target.startswith("http") else f"https://{target}"
                return Command(action="open_url", parameters={"url": url}, raw_transcript=text)

            # Check partial match in apps
            for app_name in config.APPS:
                if target in app_name or app_name in target:
                    return Command(action="open_app", parameters={"app": app_name}, raw_transcript=text)

            # Fallback for unrecognized 'open <target>': try launching as app / protocol
            return Command(action="open_app", parameters={"app": target}, raw_transcript=text)

        return None

    def parse_intent(self, transcript: str) -> Optional[IntentResult]:
        """
        Parses intent from transcript into IntentResult:
        Handles basic chained actions, screen queries, and conversational greetings.
        """
        if not transcript or not transcript.strip():
            return None

        clean_lower = re.sub(r"[.?!,]+$", "", transcript.lower()).strip()

        # 1. Screen awareness queries
        if re.search(r"\b(?:what'?s\s+on\s+my\s+screen|what\s+am\s+i\s+looking\s+at|read\s+this\s+error|explain\s+(?:the\s+)?error|what\s+does\s+this\s+say)\b", clean_lower):
            return IntentResult(intent_type="screen_query", raw_transcript=transcript)

        # 2. Conversational greetings
        if re.search(r"^(?:hey|hello|hi|howdy|what'?s\s+up|how\s+are\s+you)\b", clean_lower):
            return IntentResult(
                intent_type="conversation",
                response_text="Hey! I'm doing well, ready to help. What would you like to do?",
                raw_transcript=transcript,
            )
        if re.search(r"^(?:thanks|thank\s+you|thanks\s+bro)\b", clean_lower):
            return IntentResult(
                intent_type="conversation",
                response_text="You're welcome! Let me know if you need anything else.",
                raw_transcript=transcript,
            )

        # 3. Action chaining ("... and ...", "... then ...")
        # Split on coordinating conjunctions for actions
        parts = re.split(r"\s+(?:and\s+then|then|and)\s+", transcript, flags=re.IGNORECASE)
        if len(parts) > 1:
            actions: List[Command] = []
            for part in parts:
                cmd = self.parse(part.strip())
                if cmd:
                    actions.append(cmd)
                else:
                    break

            if len(actions) == len(parts):
                return IntentResult(
                    intent_type="action",
                    chain=ActionChain(actions=actions, raw_transcript=transcript),
                    raw_transcript=transcript,
                )

        # 4. Single action fallback
        single_cmd = self.parse(transcript)
        if single_cmd:
            return IntentResult(
                intent_type="action",
                chain=ActionChain(actions=[single_cmd], raw_transcript=transcript),
                raw_transcript=transcript,
            )

        return None
