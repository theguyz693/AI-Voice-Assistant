import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
import json
from ai.command_interpreter import CommandInterpreter

from commands.router import CommandRouter

interpreter = CommandInterpreter()
router = CommandRouter()

print("=" * 60)
print("TEST 1: Chained Actions")
print("=" * 60)

chain_tests = [
    "Open PowerPoint and type Hello World",
    "Open YouTube and search for Python decorators",
    "Open Chrome, search for NeetCode graphs, and press enter",
]

for t in chain_tests:
    res = interpreter.interpret_intent(t)
    assert res is not None, f"Failed to interpret {t}"
    assert res.intent_type == "action", f"Expected action for {t}, got {res.intent_type}"
    assert res.chain is not None and len(res.chain.actions) > 1, f"Expected chained actions for {t}"
    valid, err = res.chain.validate()
    assert valid, f"Chain invalid: {err}"
    print(f"[OK] '{t}' -> {len(res.chain.actions)} steps:")
    for i, a in enumerate(res.chain.actions):
        print(f"      Step {i+1}: {a.action} | {a.parameters}")

print("\n" + "=" * 60)
print("TEST 2: Conversational AI Mode & Short-Term Memory")
print("=" * 60)

interpreter.reset_conversation_history()
chat_sequence = [
    "How are you?",
    "What is Docker?",
    "And Kubernetes?",
    "How are they related?"
]

for q in chat_sequence:
    res = interpreter.interpret_intent(q)
    assert res is not None, f"Failed on {q}"
    assert res.intent_type == "conversation", f"Expected conversation for {q}, got {res.intent_type}"
    print(f"\nUser: {q}")
    print(f"Assistant: {res.response_text}")

print(f"\nStored conversation history turns: {len(interpreter.conversation_history)}")
assert len(interpreter.conversation_history) == len(chat_sequence) * 2

print("\n" + "=" * 60)
print("TEST 3: Action + Conversation Mix")
print("=" * 60)
mix_query = "I'm going to work on my presentation. Open PowerPoint."
res_mix = interpreter.interpret_intent(mix_query)
assert res_mix is not None and res_mix.intent_type == "action"
assert res_mix.chain.actions[0].action == "open_app"
print(f"[OK] '{mix_query}' -> extracted action: {res_mix.chain.actions[0].action} ({res_mix.chain.actions[0].parameters})")

print("\n" + "=" * 60)
print("TEST 4: Screen Awareness Intent & Verification")
print("=" * 60)
screen_query = "What's on my screen?"
res_screen = interpreter.interpret_intent(screen_query)
assert res_screen is not None and res_screen.intent_type == "screen_query"
print(f"[OK] '{screen_query}' -> recognized screen query: {res_screen.response_text}")

import tools.screen_vision as screen_tool
success, display_msg, spoken_msg = screen_tool.analyze_screen(res_screen.response_text)
print(f"Screen vision tool check: success={success}\nSpoken: {spoken_msg}")

print("\n" + "=" * 60)
print("ALL NEW FEATURES TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
