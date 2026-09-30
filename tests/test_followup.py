import urllib.request
import json

prompt = """You are a Windows 11 voice assistant intent router.
Determine the intent of the user utterance and output a single JSON object.

Allowed intent types:
1. 'conversation': Casual talk, explanations, questions, follow-ups.
   Output: {"type": "conversation", "response": "<short answer in 1-3 sentences>"}
2. 'action': Computer actions. Output: {"type": "action", "actions": [ ... ]}
3. 'screen_query': Screen questions. Output: {"type": "screen_query", "question": "..."}

Recent conversation history:
User: What is Docker?
Assistant: Docker is a container platform that packages applications and dependencies into portable containers.

Current user utterance: "And Kubernetes?"
JSON:"""

payload = {'model': 'llama3.2:1b', 'prompt': prompt, 'format': 'json', 'stream': False, 'options': {'temperature': 0.0}}
req = urllib.request.Request('http://127.0.0.1:11434/api/generate', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as resp:
    print(json.loads(resp.read().decode('utf-8'))['response'])
