#!/usr/bin/env python3
"""
Gemini API tester — klucz czytany z env, nigdy hardcoded.
Użycie:
  $env:GEMINI_API_KEY = "twój_klucz"
  python scripts/test_gemini.py
  python scripts/test_gemini.py "Napisz haiku o AI"
"""
import os
import sys
import json
import urllib.request
import urllib.error

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ Brak zmiennej środowiskowej GEMINI_API_KEY")
    print("   Ustaw: $env:GEMINI_API_KEY = 'twój_klucz'")
    sys.exit(1)

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
PROMPT = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Explain how AI works in a few words"

URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

payload = json.dumps({
    "contents": [{"parts": [{"text": PROMPT}]}]
}).encode()

req = urllib.request.Request(
    URL,
    data=payload,
    headers={
        "Content-Type": "application/json",
        "X-goog-api-key": API_KEY,
    },
    method="POST",
)

print(f"🤖 Model : {MODEL}")
print(f"💬 Prompt: {PROMPT}")
print("-" * 50)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        print(text)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"❌ HTTP {e.code}: {body}")
    sys.exit(1)
