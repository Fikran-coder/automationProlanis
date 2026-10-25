import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest

from pcare_gui import (
    App,
    RIWAYAT_PAGE_DELAY_MS,
    registered_kartu_from_riwayat_rows,
)


class KegiatanRiwayatCheckTest(unittest.TestCase):
    def test_riwayat_checker_is_available(self):
        self.assertTrue(hasattr(App, "_collect_registered_kartu"))

    def test_extracts_only_selected_kegiatan(self):
        rows = [
            ["A1", "CARD-001", "Nama", "P", "48", "Senam-Kelompok Prolanis"],
            ["A2", "CARD-002", "Nama", "P", "48", "Edukasi-Kelompok Prolanis"],
            ["A3", "CARD-003", "Nama", "P", "48", "POLI UMUM"],
        ]

        self.assertEqual(
            registered_kartu_from_riwayat_rows(rows, "037"),
            {"CARD-001"},
        )

    def test_page_click_delay_is_at_least_one_second(self):
        self.assertGreaterEqual(RIWAYAT_PAGE_DELAY_MS, 1000)

    def test_phs_automation_option_available(self):
        from pcare_gui import AUTOMATION_OPTIONS
        self.assertIn("📝 Survei PHS 2026", AUTOMATION_OPTIONS)
        self.assertTrue(hasattr(App, "_run_phs_automation"))


if __name__ == "__main__":
    unittest.main()
