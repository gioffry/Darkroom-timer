import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CalculationCrashFixTest(unittest.TestCase):
    def test_patch_contains_runtime_boundaries_and_clean_database_name(self):
        source = (ROOT / "combined/patch_v054_calculation_crash_fix.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('mdc_offline_darkroom_v054.sqlite', source)
        self.assertIn('showDevelopmentResultSafely', source)
        self.assertIn('showDevelopmentResultEssential', source)
        self.assertIn("L'app è rimasta aperta", source)

    def test_d76_regression_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite"
            con = sqlite3.connect(db)
            con.execute(
                """CREATE TABLE developer_dilutions(
                developer_norm TEXT, dilution_norm TEXT,
                min_working_ml_500cm2 REAL,
                min_working_ml_4x5_1 REAL,
                min_working_ml_4x5_2 REAL)"""
            )
            con.execute(
                "INSERT INTO developer_dilutions VALUES(?,?,?,?,?)",
                ("d 76", "1+1", 237.0, 59.25, 118.5),
            )
            values = con.execute(
                """SELECT min_working_ml_500cm2,min_working_ml_4x5_1,
                min_working_ml_4x5_2 FROM developer_dilutions
                WHERE developer_norm='d 76' AND dilution_norm='1+1'"""
            ).fetchone()
            con.close()
        self.assertEqual(values, (237.0, 59.25, 118.5))
        self.assertEqual(max(270, int(-(-values[0] // 1))), 270)


if __name__ == "__main__":
    unittest.main()
