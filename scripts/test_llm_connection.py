# -*- coding: utf-8 -*-
"""
Smoke test for the Gemini API key — confirms the key works end to end and
discovers which models it currently has access to, rather than hardcoding a
model name that may have been renamed/deprecated since.

This is infrastructure verification only, not the Investigation Copilot's
actual agent code (that's the AI/ML engineer's build — see CEO Playbook,
Section 8). It exists so "is the key wired up correctly" is a yes/no answered
by running a script, not an assumption.

Run locally:   set the GEMINI_API_KEY env var, then `python scripts/test_llm_connection.py`
Run against the real Railway-stored key without ever printing it:
                `railway run python scripts/test_llm_connection.py`
"""
import os
import sys
import requests

API_KEY = os.environ.get("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    if not API_KEY:
        fail("GEMINI_API_KEY is not set in the environment.")

    masked = API_KEY[:6] + "..." + API_KEY[-4:]
    print(f"Using key: {masked}")

    # 1. List models this key can access — also tells us the current valid
    #    model names instead of guessing one that might be stale.
    print("\nListing available models...")
    resp = requests.get(f"{BASE_URL}/models", params={"key": API_KEY}, timeout=15)
    if resp.status_code != 200:
        fail(f"List models failed: HTTP {resp.status_code} — {resp.text[:300]}")

    models = resp.json().get("models", [])
    generate_models = [
        m for m in models
        if "generateContent" in m.get("supportedGenerationMethods", [])
    ]
    if not generate_models:
        fail("Key is valid but no models support generateContent.")

    print(f"  {len(generate_models)} model(s) support generateContent:")
    for m in generate_models:
        print(f"    - {m['name']}")

    # Prefer Google's own "-latest" alias for the flash tier: it always points
    # at their current recommended fast/cheap model, so this never goes stale
    # the way a hardcoded version number (e.g. "gemini-2.5-flash") would —
    # that exact case is what broke on the first run of this script.
    names = [m["name"] for m in generate_models]
    ALIAS_PREFERENCE = ["models/gemini-flash-latest", "models/gemini-pro-latest"]
    chosen = next((a for a in ALIAS_PREFERENCE if a in names), None)
    if not chosen:
        EXCLUDE = ("preview", "lite", "image", "tts", "computer-use", "robotics", "transcribe")
        flash_models = [
            n for n in names
            if "flash" in n.lower() and not any(x in n.lower() for x in EXCLUDE)
        ]
        chosen = (flash_models or names)[0]
    print(f"\nUsing model: {chosen}")

    # 2. Real round-trip generateContent call.
    print("Sending a test prompt...")
    resp = requests.post(
        f"{BASE_URL}/{chosen}:generateContent",
        params={"key": API_KEY},
        json={"contents": [{"parts": [{"text": "Reply with exactly the word: OK"}]}]},
        timeout=30,
    )
    if resp.status_code != 200:
        fail(f"generateContent failed: HTTP {resp.status_code} — {resp.text[:300]}")

    data = resp.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        fail(f"Unexpected response shape: {data}")

    print(f"Model replied: {text!r}")
    print(f"\nSUCCESS — key is valid, model '{chosen}' is reachable and responding.")
    print(f"Recommended model for the agents: {chosen}")


if __name__ == "__main__":
    main()
