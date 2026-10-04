"""Checks that the Home walkthrough stays present and source-driven."""

import json
import unittest

from scripts.build_ui_walkthrough import OUTPUT, POSTER, ROOT, SCENE_FOCUS, SCENE_LABELS, SCENES, SCREENS, SUBTITLES, VIDEO_TITLE, WIDTH, HEIGHT


class WalkthroughTests(unittest.TestCase):
    def test_walkthrough_uses_captured_app_screens(self):
        self.assertGreaterEqual(len(SCENES), 25)
        self.assertEqual(SCENES[0]["title"], VIDEO_TITLE)
        for scene in SCENES:
            self.assertTrue(scene["title"])
            first_letter = next((character for character in scene["title"] if character.isalpha()), "")
            self.assertTrue(first_letter.isupper(), scene["title"])
            self.assertTrue(scene["narration"])
            self.assertTrue((SCREENS / scene["screen"]).is_file(), scene["screen"])
        narration = " ".join(scene["narration"] for scene in SCENES)
        for unwanted in ("team", "capstone", "course", "professor", "I I T Bombay"):
            self.assertNotIn(unwanted.lower(), narration.lower())
        for required in ("Case zero four one", "Cash", "R A G", "Grounding Validator",
                         "Request more information", "separate fictional transaction packet", "no decision is recorded",
                         "passcode", "fifty seven indexed chunks", "three hundred fictional accounts",
                         "one million two hundred thousand", "Neither case is proven legal or illegal",
                         "old index version", "twenty one", "zero original identity files"):
            self.assertIn(required.lower(), narration.lower())
        for captured_public_screen in ("22_public_intake_form.jpg", "24_public_intake_chunks.jpg",
                                       "25_public_intake_review.jpg", "26_public_intake_compliance.jpg",
                                       "27_public_admin_knowledge_open.png", "30_public_admin_chunks_table.png",
                                       "31_public_admin_search.png", "32_public_admin_rule_open.png",
                                       "33_public_admin_rule_preview.png", "34_public_intake_rows.png",
                                       "41_public_floating_home_guest.png", "42_public_floating_home_ready.png",
                                       "44_public_floating_case_answer.png", "45_public_floating_count_kyc.png",
                                       "46_public_floating_saved_current.png", "47_public_floating_chunk_answer.png",
                                       "48_public_queue_current.png", "49_public_queue_filtered.png",
                                       "39_public_exact_case_chunk.png"):
            self.assertIn(captured_public_screen, [scene["screen"] for scene in SCENES])
        self.assertGreaterEqual(sum(bool(scene.get("visual")) for scene in SCENES), 3)
        self.assertIn("floating Copilot", narration)
        self.assertIn("press Send at the bottom", narration)
        self.assertIn("sixteen rows in the supplied account dataset", narration)
        self.assertIn("six transactions in its narrower review window", narration)
        self.assertTrue(POSTER.is_file())
        self.assertGreater(POSTER.stat().st_size, 20_000)

    def test_complete_narration_has_subtitles(self):
        self.assertTrue(SUBTITLES.is_file())
        captions = SUBTITLES.read_text(encoding="utf-8")
        self.assertTrue(captions.startswith("WEBVTT\n"))
        self.assertIn("Case zero four one", captions)
        self.assertIn("no decision is recorded", captions.lower())
        self.assertGreater(captions.count(" --> "), 100)

    def test_on_screen_arrows_have_visible_targets(self):
        for index, scene in enumerate(SCENES):
            if index == 0 or scene.get("visual"):
                continue
            self.assertIn(index, SCENE_FOCUS, scene["title"])
            self.assertIn(index, SCENE_LABELS, scene["title"])
            self.assertLessEqual(len(SCENE_LABELS[index]), 26)
            for x, y in SCENE_FOCUS[index]:
                self.assertGreaterEqual(x, 20)
                self.assertLessEqual(x, WIDTH - 20)
                self.assertGreaterEqual(y, 20)
                self.assertLessEqual(y, HEIGHT - 20)

    def test_case_math_and_decision_language_match_saved_evidence(self):
        case = json.loads((ROOT / "data" / "cached_reports" / "CASE-041.json").read_text(encoding="utf-8"))
        cash = [txn for txn in case["evidence"]["window_transactions"] if txn["reference_text"] == "Cash deposit"]
        self.assertEqual(len(cash), 4)
        self.assertEqual(sum(txn["amount"] for txn in cash), 3_870_000)
        self.assertEqual(len(case["evidence"]["window_transactions"]), 6)
        self.assertEqual(case["evidence"]["baseline_avg_amount"], 395_000)
        self.assertEqual(case["evidence"]["deviation_ratio"], 2.5)
        script = " ".join(scene["narration"] for scene in SCENES).lower()
        self.assertIn("three million eight hundred seventy thousand", script)
        self.assertIn("no decision is recorded", script)

    def test_embedded_video_is_an_mp4(self):
        self.assertTrue(OUTPUT.is_file())
        self.assertGreater(OUTPUT.stat().st_size, 100_000)
        with OUTPUT.open("rb") as video:
            header = video.read(12)
        self.assertEqual(header[4:8], b"ftyp")
        contents = OUTPUT.read_bytes()
        self.assertTrue(b"mp4a" in contents, "Walkthrough must include an AAC narration track")
        self.assertTrue(b"soun" in contents, "Walkthrough must include an audio stream")


if __name__ == "__main__":
    unittest.main()
