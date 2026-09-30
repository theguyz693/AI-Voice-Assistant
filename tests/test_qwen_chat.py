import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
from ai.command_interpreter import CommandInterpreter

interpreter = CommandInterpreter()

test_queries = [
    "Hey, how are you?",
    "What is Docker?",
    "And Kubernetes?",
    "Tell me something interesting.",
]

print("--- Testing qwen2.5:7b Conversational Mode ---")
for q in test_queries:
    t0 = time.time()
    res = interpreter.interpret_intent(q)
    dt = time.time() - t0
    assert res is not None
    assert res.intent_type == "conversation"
    print(f"\n[{dt:.2f}s] User: {q}")
    print(f"Assistant ({len(res.response_text.split())} words): {res.response_text}")

print("\n--- Conversational Mode Test Passed! ---")
