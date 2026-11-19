from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import originals


class OriginalsTest(unittest.TestCase):
    def test_both_regions_are_supported_and_europe_is_the_reference(self):
        self.assertEqual(originals.REFERENCE_SHA256, originals.EUROPE_SHA256)
        self.assertEqual(set(originals.SUPPORTED_ORIGINALS),
                         {originals.EUROPE_SHA256, originals.NORTH_AMERICA_SHA256})

    def test_unknown_binary_is_rejected(self):
        with self.assertRaises(ValueError):
            originals.require_supported(b"not the game")

    def test_only_the_region_flag_slot_differs(self):
        self.assertEqual(originals.REGION_DISPATCH_TARGETS,
                         {originals.NORTH_AMERICA_SHA256: {("primary", 0x7C): 0x00486A70}})

    def test_configured_original_reads_the_setup_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "reccmp-user.yml").write_text(
                'targets:\n  LEGORACERS2:\n    path: "C:\\\\Games\\\\LEGO Racers 2.exe"\n', encoding="utf-8")
            with patch.object(originals, "ROOT", root):
                self.assertEqual(originals.configured_original(), Path("C:\\Games\\LEGO Racers 2.exe"))

    def test_configured_original_falls_back_to_the_default(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(originals, "ROOT", Path(directory)):
                self.assertEqual(originals.configured_original(), originals.DEFAULT_ORIGINAL)


if __name__ == "__main__":
    unittest.main()
