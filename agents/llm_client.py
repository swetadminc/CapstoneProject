# -*- coding: utf-8 -*-
"""
Shared Gemini client — used by the Investigation Summary Agent and the Chat
Agent. Pulled out of investigation_agent.py during the multi-agent split
(pending item #5) so "who talks to the LLM" is one place, not duplicated
across agents.
"""
import json
import os
import time

import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# gemini-flash-lite-latest, not gemini-flash-latest: during this build,
# flash-lite reliably returned 200s on real-sized prompts while flash was
# consistently 503 (high demand) — see scripts/test_llm_connection.py for
# how to re-check this if it changes. Overridable via GEMINI_MODEL env var.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "models/gemini-flash-lite-latest")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_MODEL}:generateContent"


def call_gemini(prompt: str, schema: dict, max_retries: int = 3) -> dict:
    """Gemini's flash tier returns transient 503s under load reasonably
    often (observed during this build) — retry with backoff rather than
    failing the whole investigation on a temporary blip. This is exactly
    the kind of thing the cached-report fallback (CEO Playbook, Section 12)
    exists for at demo time; this retry is the first, cheaper line of
    defense before falling back to a cached report.

    Shared by the Investigation Summary Agent AND the Chat Agent — schema
    is required (no implicit default) since the two callers use different
    JSON schemas; same HTTP handling, same retry behavior either way."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment.")

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                GEMINI_URL,
                params={"key": GEMINI_API_KEY},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "responseSchema": schema,
                    },
                },
                timeout=60,
            )
            if resp.status_code == 503 and attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 * attempt)
    raise last_error
