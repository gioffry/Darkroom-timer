import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT.parent / "release-v054" / "mdc_full-v054.sqlite"


class AliasAndProgressiveUiTest(unittest.TestCase):
    def test_d76_sheet_time_exists(self):
        if not DB.exists():
            self.skipTest("v0.5.4 extracted release database is not present")
        con = sqlite3.connect(DB)
        row = con.execute(
            """SELECT time35,time120,timesheet,temp FROM times
            WHERE film_norm='fomapan 100' AND developer_norm='d 76'
              AND dilution_norm='1+1' AND iso=100 AND temp=20 LIMIT 1"""
        ).fetchone()
        con.close()
        self.assertEqual(row, ("10", "10", "10", 20.0))

    def test_alias_patch_is_general_not_d76_special_case(self):
        source = (ROOT / "combined/patch_v055_time_aliases.py").read_text(encoding="utf-8")
        self.assertIn("FullCatalogStore.canonicalDeveloper(developer)", source)
        self.assertNotIn('if (developer.equals("KODAK D-76"))', source)
        self.assertIn("DevTimeEngine.Result.notFound", source)

    def test_ui_has_three_collapsed_sections(self):
        source = (ROOT / "combined/patch_v055_results_ui.py").read_text(encoding="utf-8")
        for title in (
            "DETTAGLI DEL CALCOLO",
            "SCHEDA TECNICA RIVELATORE",
            "RIUTILIZZO BAGNI",
        ):
            self.assertIn(title, source)
        self.assertIn("PREPARAZIONE BAGNI", source)
        self.assertIn("body.setVisibility(View.GONE)", source)
        self.assertIn("private void addUnifiedChemicalField", source)


if __name__ == "__main__":
    unittest.main()
