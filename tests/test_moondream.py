import sys
import os
sys.path.insert(0, os.path.abspath("."))
import tools.screen_vision as vision

print("--- Testing Moondream Screen Awareness ---")
print("Installed vision models:", vision._get_installed_vision_models())
success, display_msg, spoken_msg = vision.analyze_screen("What is on my screen?")
print(f"Success: {success}")
print(f"Display text:\n{display_msg}")
print(f"Spoken text:\n{spoken_msg}")
