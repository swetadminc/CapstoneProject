"""Checks that the Home walkthrough stays present and source-driven."""

import unittest

from scripts.build_ui_walkthrough import OUTPUT, POSTER, SCENES, SCREENS


class WalkthroughTests(unittest.TestCase):
    def test_walkthrough_uses_captured_app_screens(self):
        self.assertGreaterEqual(len(SCENES), 10)
        for scene in SCENES:
            self.assertTrue(scene["title"])
            self.assertTrue(scene["title"][0].isupper(), scene["title"])
            self.assertTrue(scene["narration"])
            self.assertTrue((SCREENS / scene["screen"]).is_file(), scene["screen"])
        self.assertTrue(POSTER.is_file())
        self.assertGreater(POSTER.stat().st_size, 20_000)

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
