import sys, os
sys.path.insert(0, os.path.abspath("."))
import time
import json
from ai.command_interpreter import CommandInterpreter

interpreter = CommandInterpreter()

print("=" * 65)
print("TEST 1: Fast Intent Routing & Reliable Action Chains")
print("=" * 65)

action_queries = [
    "Open Word, create a blank document and type Hello World",
    "Open Spotify and play Blinding Lights",
    "Put on some Blinding Lights",
    "Open YouTube and search for Python decorators",
    "Open Google Maps and search for P.E.S. College",
    "Scroll down",
    "I'm going to work on my presentation. Open PowerPoint.",
]

for q in action_queries:
    t0 = time.time()
    res = interpreter.interpret_intent(q)
    dt = time.time() - t0
    assert res is not None and res.intent_type == "action", f"Failed on '{q}', got {res}"
    assert res.chain is not None, f"Expected chain for '{q}'"
    valid, err = res.chain.validate()
    assert valid, f"Chain invalid for '{q}': {err}"
    print(f"[{dt:.2f}s] [OK] \"{q}\" -> {len(res.chain.actions)} step(s):")
    for i, a in enumerate(res.chain.actions):
        print(f"      Step {i+1}: {a.action} | {a.parameters}")

print("\n" + "=" * 65)
print("TEST 2: Screen Awareness Intent Recognition")
print("=" * 65)

screen_queries = [
    "What's on my screen?",
    "Read this error.",
    "What am I looking at?",
]

for sq in screen_queries:
    t0 = time.time()
    res = interpreter.interpret_intent(sq)
    dt = time.time() - t0
    assert res is not None and res.intent_type == "screen_query", f"Failed on '{sq}', got {res}"
    print(f"[{dt:.2f}s] [OK] \"{sq}\" -> recognized screen query: '{res.response_text}'")

print("\n" + "=" * 65)
print("TEST 3: Conversational AI (Qwen 2.5 7B) & Bounded Memory")
print("=" * 65)

interpreter.reset_conversation_history()
chat_queries = [
    "Hey, how are you?",
    "What is Docker?",
    "And Kubernetes?",
    "Why do companies use them together?",
]

for cq in chat_queries:
    t0 = time.time()
    res = interpreter.interpret_intent(cq)
    dt = time.time() - t0
    assert res is not None and res.intent_type == "conversation", f"Failed on '{cq}', got {res}"
    print(f"\n[{dt:.2f}s] User: {cq}")
    print(f"Assistant: {res.response_text}")

print(f"\nStored conversation history turns: {len(interpreter.conversation_history)}")
assert len(interpreter.conversation_history) == len(chat_queries) * 2

print("\n" + "=" * 65)
print("ALL UPGRADE VERIFICATIONS PASSED SUCCESSFULLY!")
print("=" * 65)
