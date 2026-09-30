import urllib.request
import json

test_utterances = [
    "Open PowerPoint and type Introduction",
    "Open YouTube and search for Python decorators",
    "How are you?",
    "What is the difference between Docker and Kubernetes?",
    "What's on my screen?",
    "I'm going to work on my presentation. Open PowerPoint.",
]

prompt_template = """You are a Windows 11 voice assistant intent router.
Determine the intent of the user utterance and output a single JSON object.

Allowed intent types:
1. 'screen_query': User explicitly asks what is on their screen, or to read/explain an error on screen.
   Output: {"type": "screen_query", "question": "<question>"}

2. 'conversation': General conversation, greetings, questions about concepts/technology, casual talk, jokes, follow-ups.
   Output: {"type": "conversation", "response": "<short, natural, friendly answer in 1-3 sentences>"}

3. 'action': The user wants the assistant to execute one or more computer actions.
   Supported actions: open_url, web_search, youtube_search, open_app, type_text, keypress, set_timer, adjust_volume, control_media, control_window, take_screenshot, get_time.
   Output: {"type": "action", "actions": [{"action": "<action>", "parameters": { ... }}]}

Rules:
- For multi-step commands, return an array of actions in execution order.
- If the user mixes conversational talk with an action (e.g. "I'm going to work on my slides. Open PowerPoint."), extract the action.
- Never output executable code.

Examples:
- "How are you?" -> {"type": "conversation", "response": "I'm doing great! How can I help you today?"}
- "What's on my screen?" -> {"type": "screen_query", "question": "What's on my screen?"}
- "Open PowerPoint and type Introduction" -> {"type": "action", "actions": [{"action": "open_app", "parameters": {"app": "powerpoint"}}, {"action": "type_text", "parameters": {"text": "Introduction"}}]}
- "Open YouTube and search for Python decorators" -> {"type": "action", "actions": [{"action": "open_url", "parameters": {"url": "https://youtube.com"}}, {"action": "youtube_search", "parameters": {"query": "Python decorators"}}]}

User utterance: "%s"
JSON:"""

for u in test_utterances:
    p = prompt_template % u.replace('"', '\\"')
    payload = {
        "model": "llama3.2:1b",
        "prompt": p,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 180},
    }
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))["response"]
        print(f"Utterance: {u!r}\nResult: {res}\n")
