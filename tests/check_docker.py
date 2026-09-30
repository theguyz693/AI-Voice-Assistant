import sys, os
sys.path.insert(0, os.path.abspath("."))
import urllib.request, json
from ai.command_interpreter import SYSTEM_INTENT_PROMPT

prompt = f'{SYSTEM_INTENT_PROMPT}\nUser utterance: "What is Docker?"\nJSON:'
payload = {'model': 'llama3.2:1b', 'prompt': prompt, 'format': 'json', 'stream': False, 'options': {'temperature': 0.0}}
req = urllib.request.Request('http://127.0.0.1:11434/api/generate', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as resp:
    print(resp.read().decode('utf-8'))
