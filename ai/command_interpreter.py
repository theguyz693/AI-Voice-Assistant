"""
Multi-Model Intent Router & Conversational AI.
Architecture:
- Fast Intent & Action Chaining: llama3.2:1b (instant, grammar-constrained JSON)
- Conversational Discussion & Explanations: qwen2.5:7b (natural, deep, chill tone) with bounded context memory
- On-Demand Screen Understanding: moondream (vision-language model)
"""

import json
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any
import config
from commands.schema import Command, ActionChain, IntentResult, SUPPORTED_ACTIONS
from commands.parser import CommandParser
from tools.timers import parse_time_duration


SYSTEM_INTENT_PROMPT = """You are a Windows 11 desktop voice assistant intent router.
Determine the intent of the user's speech and output a single JSON object.

Allowed intent types:
1. 'screen_query': User EXPLICITLY asks about their computer screen, display, or visible error. Requires explicit words like "screen", "display", "looking at", or "read this error".
   Output: {"type": "screen_query", "question": "<exact question>"}

2. 'conversation': General conversation, greetings, questions about tech/concepts (e.g. "What is Docker?", "What is Kubernetes?"), casual talk, jokes, follow-ups.
   Output: {"type": "conversation"}

3. 'action': The user wants the assistant to execute one or more computer actions.
   Output: {"type": "action", "actions": [{"action": "<action>", "parameters": { ... }}]}


Supported computer actions:
- open_url: {"url": "<full_url>"}
- web_search: {"query": "<query>"}
- youtube_search: {"query": "<query>"}
- maps_search: {"query": "<location_or_place>"} — ALWAYS use this for Google Maps / directions / location searches. NEVER use open_url + web_search for maps.
- amazon_search: {"query": "<product_or_item>"} — ALWAYS use this for Amazon product searches. NEVER use open_url + web_search for Amazon. Triggered by: "find X on Amazon", "search Amazon for X", "look for X on Amazon", "open Amazon and search for X".
- open_app: {"app": "<app_name>"}
- play_spotify: {"query": "<song_or_artist>"}
- create_blank_document: {"app": "<word|powerpoint>"}
- browser_nav: {"action": "<back|forward|refresh|scroll_down|scroll_up>"}
- type_text: {"text": "<exact text to type>"}
- keypress: {"key": "<enter|escape|copy|paste|tab>"}
- set_timer: {"seconds": <integer_seconds>, "label": "<duration_str>"}
- adjust_volume: {"action": "<up|down|mute>"}
- control_media: {"action": "<playpause|next|previous>"}
- control_window: {"action": "<minimize|maximize|close>"}
- take_screenshot: {}
- get_time: {"type": "<time|date>"}

CRITICAL RULES:
- Action Priority: If the utterance contains ANY actionable command (e.g. open an app, search, play music, type text, set timer, volume), you MUST classify as 'action' even if preceded or followed by casual talk (e.g. "I'm going to work on my presentation. Open PowerPoint." -> action: open_app).
- Google Maps / Directions: ANY request involving Google Maps, directions, finding a place, or navigating to a location MUST use ONLY the 'maps_search' action. NEVER combine open_url + web_search for maps. Examples: "Open Google Maps and search for PES College" -> [{"action": "maps_search", "parameters": {"query": "PES College"}}] (single action only).
- Amazon Search: ANY request involving finding, searching, or looking for a product on Amazon MUST use ONLY the 'amazon_search' action. NEVER combine open_url + web_search for Amazon. Examples: "Find Hot Wheels on Amazon" -> [{"action": "amazon_search", "parameters": {"query": "Hot Wheels"}}] (single action only).
- Spotify Music: Phrases like "put on Blinding Lights", "play Blinding Lights on Spotify", or "open Spotify and play Blinding Lights" -> {"action": "play_spotify", "parameters": {"query": "Blinding Lights"}}.
- Office Workflows: Phrases like "open Word, create a blank document and type Hello World" -> [{"action": "create_blank_document", "parameters": {"app": "word"}}, {"action": "type_text", "parameters": {"text": "Hello World"}}].
- Multi-step chains: if the user asks for multiple sequential actions, output ALL actions in the 'actions' array in execution order.
- Never output executable code (no python, no shell, no powershell).
- Never invent actions outside the allowed list.

Examples:
- "How are you?" -> {"type": "conversation"}
- "What is the difference between Docker and Kubernetes?" -> {"type": "conversation"}
- "What's on my screen?" -> {"type": "screen_query", "question": "What's on my screen?"}
- "Put on some Blinding Lights" -> {"type": "action", "actions": [{"action": "play_spotify", "parameters": {"query": "Blinding Lights"}}]}
- "Open Google Maps and search for PES College" -> {"type": "action", "actions": [{"action": "maps_search", "parameters": {"query": "PES College"}}]}
- "Show me directions to the nearest hospital" -> {"type": "action", "actions": [{"action": "maps_search", "parameters": {"query": "nearest hospital"}}]}
- "Find PES University on maps" -> {"type": "action", "actions": [{"action": "maps_search", "parameters": {"query": "PES University"}}]}
- "Find Hot Wheels on Amazon" -> {"type": "action", "actions": [{"action": "amazon_search", "parameters": {"query": "Hot Wheels"}}]}
- "Search Amazon for running shoes" -> {"type": "action", "actions": [{"action": "amazon_search", "parameters": {"query": "running shoes"}}]}
- "Look for AirPods on Amazon.com" -> {"type": "action", "actions": [{"action": "amazon_search", "parameters": {"query": "AirPods"}}]}
- "Open Amazon and search for LEGO" -> {"type": "action", "actions": [{"action": "amazon_search", "parameters": {"query": "LEGO"}}]}
- "Open Word, create a blank document and type Hello World" -> {"type": "action", "actions": [{"action": "create_blank_document", "parameters": {"app": "word"}}, {"action": "type_text", "parameters": {"text": "Hello World"}}]}
- "Open PowerPoint and type Introduction" -> {"type": "action", "actions": [{"action": "open_app", "parameters": {"app": "powerpoint"}}, {"action": "type_text", "parameters": {"text": "Introduction"}}]}
- "Open YouTube and search for Python decorators" -> {"type": "action", "actions": [{"action": "open_url", "parameters": {"url": "https://youtube.com"}}, {"action": "youtube_search", "parameters": {"query": "Python decorators"}}]}
- "Open Chrome, search for NeetCode graphs, and press enter" -> {"type": "action", "actions": [{"action": "open_app", "parameters": {"app": "chrome"}}, {"action": "web_search", "parameters": {"query": "NeetCode graphs"}}, {"action": "keypress", "parameters": {"key": "enter"}}]}
- "Scroll down" -> {"type": "action", "actions": [{"action": "browser_nav", "parameters": {"action": "scroll_down"}}]}
- "Go back" -> {"type": "action", "actions": [{"action": "browser_nav", "parameters": {"action": "back"}}]}
- "turn the volume up" -> {"type": "action", "actions": [{"action": "adjust_volume", "parameters": {"action": "up"}}]}

Respond with ONLY the JSON object.
"""


class CommandInterpreter:
    def __init__(self):
        self.fallback_parser = CommandParser()
        # Bounded conversation memory: list of {"role": "user"|"assistant", "content": str}
        self.conversation_history: List[Dict[str, str]] = []

    def reset_conversation_history(self):
        """Clears short-term conversational memory."""
        self.conversation_history.clear()

    def interpret_intent(self, transcript: str) -> Optional[IntentResult]:
        """
        Unified interpretation: returns an IntentResult classifying the utterance
        as 'action' (with ActionChain), 'conversation' (with response), or 'screen_query'.
        """
        if not transcript or not transcript.strip():
            return None

        # 1. Attempt AI Intent Interpretation via local LLaMA
        if config.USE_LOCAL_LLM:
            try:
                intent_res = self._query_ollama_intent(transcript)
                if intent_res:
                    return intent_res
            except Exception as e:
                print(f"[AI Warning]: LLM interpretation error ({e})")

            print(f"[Fallback]: Falling back to rule-based interpreter for: \"{transcript}\"")

        # 2. Rule-based fallback
        return self.fallback_parser.parse_intent(transcript)

    def interpret(self, transcript: str) -> Optional[Command]:
        """Backward-compatible method returning a single Command."""
        intent_res = self.interpret_intent(transcript)
        if intent_res and intent_res.intent_type == "action" and intent_res.chain:
            return intent_res.chain.actions[0] if intent_res.chain.actions else None
        return None

    def _generate_chat_response(self, user_query: str) -> str:
        """
        Generates a natural, conversational response using the dedicated conversational model
        (qwen2.5:7b) with bounded short-term memory.
        """
        # Build chat messages payload
        messages = [{"role": "system", "content": config.CONVERSATION_SYSTEM_PROMPT}]

        # Append recent bounded history
        for msg in self.conversation_history[-config.MAX_CONVERSATION_HISTORY:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_query})

        # Try CHAT_MODEL first, fallback to COMMAND_MODEL if not yet available
        for target_model in [config.CHAT_MODEL, config.COMMAND_MODEL]:
            payload = {
                "model": target_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 180,
                },
            }

            try:
                req = urllib.request.Request(
                    config.OLLAMA_CHAT_URL,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=12.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    answer = data.get("message", {}).get("content", "").strip()
                    if answer:
                        # Clean any leftover markdown fences
                        if answer.startswith("```"):
                            answer = "\n".join(answer.split("\n")[1:-1]).strip()
                        return answer
            except Exception:
                continue

        return "I'm doing well! How can I assist you with your computer today?"

    def _query_ollama_intent(self, transcript: str) -> Optional[IntentResult]:
        """
        Queries the fast command model (llama3.2:1b) for instant intent classification
        and structured action extraction.
        """
        user_prompt = f'User utterance: "{transcript}"\nJSON:'
        full_prompt = f"{SYSTEM_INTENT_PROMPT}\n{user_prompt}"

        payload = {
            "model": config.COMMAND_MODEL,
            "prompt": full_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 180,
            },
        }

        req = urllib.request.Request(
            config.OLLAMA_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=5.0) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            raw_output = res_data.get("response", "").strip()

            if not raw_output:
                return None

            data = json.loads(raw_output)
            intent_type = data.get("type", "").lower()

            # --- CASE 1: CONVERSATION ---
            if intent_type == "conversation":
                # Route to conversational model (qwen2.5:7b) for natural, articulate dialogue
                resp_text = self._generate_chat_response(transcript)

                # Update bounded memory
                self.conversation_history.append({"role": "user", "content": transcript})
                self.conversation_history.append({"role": "assistant", "content": resp_text})
                if len(self.conversation_history) > config.MAX_CONVERSATION_HISTORY * 2:
                    self.conversation_history = self.conversation_history[-(config.MAX_CONVERSATION_HISTORY * 2):]

                return IntentResult(
                    intent_type="conversation",
                    response_text=resp_text,
                    raw_transcript=transcript,
                )

            # --- CASE 2: SCREEN QUERY ---
            elif intent_type == "screen_query":
                # Guardrail: Verify the user actually asked about their screen or a visible error
                screen_keywords = ("screen", "display", "monitor", "looking at", "read this error", "what does this say", "see on my")
                transcript_lower = transcript.lower()
                if any(kw in transcript_lower for kw in screen_keywords):
                    question = data.get("question", transcript)
                    return IntentResult(
                        intent_type="screen_query",
                        response_text=question,
                        raw_transcript=transcript,
                    )
                else:
                    # Model misclassified a general question as screen_query -> route to conversation!
                    resp_text = self._generate_chat_response(transcript)
                    self.conversation_history.append({"role": "user", "content": transcript})
                    self.conversation_history.append({"role": "assistant", "content": resp_text})
                    return IntentResult(
                        intent_type="conversation",
                        response_text=resp_text,
                        raw_transcript=transcript,
                    )


            # --- CASE 3: ACTION / ACTION CHAIN ---
            elif intent_type == "action" or "actions" in data or "action" in data:
                raw_actions = data.get("actions")
                if not raw_actions and "action" in data:
                    raw_actions = [{"action": data["action"], "parameters": data.get("parameters", {})}]

                if not raw_actions or not isinstance(raw_actions, list):
                    return None

                parsed_commands: List[Command] = []

                for item in raw_actions:
                    act = item.get("action")
                    params = item.get("parameters", {})

                    if not act or act not in SUPPORTED_ACTIONS:
                        return None

                    # Parameter normalization
                    if act == "set_timer" and "seconds" not in params:
                        label = params.get("label", "") or params.get("duration", "")
                        sec = parse_time_duration(label)
                        if sec > 0:
                            params["seconds"] = sec
                            params["label"] = label

                    if act == "type_text" and "text" in params:
                        params["text"] = str(params["text"])

                    cmd = Command(action=act, parameters=params, raw_transcript=transcript)
                    is_valid, err = cmd.validate()
                    if not is_valid:
                        print(f"[AI Schema Warning]: Action '{act}' failed validation: {err}")
                        return None

                    parsed_commands.append(cmd)

                if parsed_commands:
                    chain = ActionChain(actions=parsed_commands, raw_transcript=transcript)
                    return IntentResult(
                        intent_type="action",
                        chain=chain,
                        raw_transcript=transcript,
                    )

        return None
