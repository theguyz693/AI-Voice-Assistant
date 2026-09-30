import sys, os
sys.path.insert(0, os.path.abspath("."))
import io, base64, json, urllib.request
import PIL.Image, PIL.ImageDraw
import tools.screen_vision as vision

import config

# Create mock test screenshot
img = PIL.Image.new('RGB', (400, 150), color=(255, 255, 255))
draw = PIL.ImageDraw.Draw(img)
draw.text((20, 50), 'Python Error: ModuleNotFoundError: No module named test', fill=(200, 0, 0))
buf = io.BytesIO()
img.save(buf, format='JPEG')
b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')

# Mock the capture function to return this test image
orig_capture = vision._capture_screen_bytes
vision._capture_screen_bytes = lambda: b64_str

print("--- Testing Vision + Conversational Synthesis Pipeline ---")
success, raw_vis, spoken_res = vision.analyze_screen("What error is on my screen?")
print(f"Success: {success}")
print(f"Moondream Raw Vision:\n{raw_vis}\n")
print(f"Qwen Conversational Synthesis for Voice TTS:\n{spoken_res}")

vision._capture_screen_bytes = orig_capture
assert success
assert "ModuleNotFoundError" in raw_vis or "error" in raw_vis.lower()
print("\n--- Vision + Conversational Synthesis Test Passed! ---")
