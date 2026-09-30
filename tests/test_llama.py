import time
from ai.command_interpreter import CommandInterpreter

interpreter = CommandInterpreter()

test_phrases = [
    "open chrome",
    "search youtube for car drifting videos",
    "type hello world",
    "set a timer for 5 minutes",
    "turn the volume up",
    "car drifting videos on youtube",
    "find some drifting videos on youtube",
    "put on some car drifting vids",
    "open vscode",
    "launch visual studio code",
    "start vscode",
]

print(f"--- Running Benchmark on Local LLaMA Intent Layer ---")
all_passed = True
for phrase in test_phrases:
    t0 = time.time()
    cmd = interpreter.interpret(phrase)
    dt = time.time() - t0
    if cmd:
        valid, err = cmd.validate()
        status = "PASSED" if valid else f"INVALID ({err})"
        print(f"[{dt:.2f}s] [{status}] \"{phrase}\"")
        print(f"       -> Action: {cmd.action} | Parameters: {cmd.parameters}")
        if not valid:
            all_passed = False
    else:
        print(f"[{dt:.2f}s] [FAILED] \"{phrase}\"")
        all_passed = False

print("-" * 55)
print(f"Benchmark Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
