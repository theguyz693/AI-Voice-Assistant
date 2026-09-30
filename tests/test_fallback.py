import config
from ai.command_interpreter import CommandInterpreter

print("--- Testing Fallback Mechanism ---")
# Simulate Ollama being down or invalid URL
orig_url = config.OLLAMA_API_URL
config.OLLAMA_API_URL = "http://127.0.0.1:9999/invalid"

interpreter = CommandInterpreter()
cmd = interpreter.interpret("open chrome")
print(f"Fallback result for 'open chrome': {cmd}")
assert cmd is not None, "Fallback failed to return a command!"
assert cmd.action == "open_app"
assert cmd.parameters["app"] == "chrome"

# Restore URL
config.OLLAMA_API_URL = orig_url
print("Fallback test passed successfully!")
