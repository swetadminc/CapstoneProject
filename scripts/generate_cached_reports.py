# -*- coding: utf-8 -*-
"""
Generates the cached-report fixtures for the demo (F12 in the PRD): pre-runs
the Investigation Agent for both hero cases and saves the validated output,
so the demo can run instantly with zero API calls during rehearsal — only
the live-vs-cached toggle on demo day actually hits Gemini.

Re-run this whenever the underlying dataset or the agent's prompt changes
meaningfully enough that the cached reports should be refreshed.

Run: railway run python scripts/generate_cached_reports.py
"""
import json
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.investigation_agent import investigate, GEMINI_MODEL

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "cached_reports")
OUT_DIR = os.path.abspath(OUT_DIR)
os.makedirs(OUT_DIR, exist_ok=True)

# One representative case per typology, plus both rapid-movement hero cases —
# item #6/#7: this also doubles as live-agent verification beyond the original
# 2 hero cases, since generating a cached report requires a clean investigate() run.
CASES = ["CASE-001", "CASE-002", "CASE-041", "CASE-003", "CASE-006"]


def main():
    for case_id in CASES:
        print(f"Generating cached report for {case_id}...")
        result = investigate(case_id)
        payload = {
            "case_id": case_id,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "model": GEMINI_MODEL,
            "context": result["context"],
            "evidence": result["evidence"],
            "guidance": result["guidance"],
            "report": result["report"],
        }
        out_path = os.path.join(OUT_DIR, f"{case_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"  saved {out_path}  (validator: {result['report']['_validator_result']})")


if __name__ == "__main__":
    main()
