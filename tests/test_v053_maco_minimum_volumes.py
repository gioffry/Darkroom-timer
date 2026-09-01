#!/usr/bin/env python3

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GENERATOR = load_module(
    "minimum_volume_generator_v053",
    "assistant/db/generate_maco_minimum_volumes_v053.py",
)
APPLIER = load_module(
    "minimum_volume_applier_v053",
    "assistant/db/apply_developer_minimum_volumes_v053.py",
)
RULES_PATH = ROOT / "assistant/db/maco_developer_rules_v053.json"


class MacoMinimumVolumeRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        cls.rules = {
            entry["developerNorm"]: entry["rule"]
            for entry in cls.payload["developers"]
        }

    def test_scope_has_37_unique_developers(self):
        norms = [entry["developerNorm"] for entry in self.payload["developers"]]
        self.assertEqual(37, len(norms))
        self.assertEqual(len(norms), len(set(norms)))

    def test_key_capacity_and_recipe_formulas(self):
        self.assertAlmostEqual(
            333.333333,
            GENERATOR.minimum_for_dilution(self.rules["foma universal"], "1+3"),
            places=5,
        )
        self.assertEqual(
            300,
            GENERATOR.minimum_for_dilution(self.rules["xt 3"], "1+1"),
        )
        self.assertEqual(
            265,
            GENERATOR.minimum_for_dilution(self.rules["moersch eco"], "2+1+50"),
        )
        self.assertEqual(
            120,
            GENERATOR.minimum_for_dilution(self.rules["jobo alpha"], "1+1+18"),
        )
        self.assertEqual(
            200,
            GENERATOR.minimum_for_dilution(self.rules["hc 110"], "b"),
        )
        self.assertEqual(
            255,
            GENERATOR.minimum_for_dilution(self.rules["rodinal"], "1+50"),
        )
        self.assertEqual(
            237,
            GENERATOR.minimum_for_dilution(self.rules["d 76"], "1+1"),
        )
        self.assertEqual(
            270,
            GENERATOR.minimum_for_dilution(self.rules["id 11"], "1+3"),
        )

    def test_sheet_values_are_exact_area_fractions(self):
        minimum = GENERATOR.minimum_for_dilution(
            self.rules["foma universal"], "1+3"
        )
        self.assertAlmostEqual(minimum / 4, 83.33333333333333)
        self.assertAlmostEqual(minimum / 2, 166.66666666666666)


class MacoMinimumVolumeApplyTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "mdc.sqlite"
        self.records_file = Path(self.tempdir.name) / "records.json"
        connection = sqlite3.connect(self.database)
        connection.executescript(
            '''CREATE TABLE developer_dilutions(
                 developer_norm TEXT NOT NULL,
                 dilution TEXT NOT NULL,
                 dilution_norm TEXT NOT NULL,
                 source_kind TEXT NOT NULL,
                 PRIMARY KEY(developer_norm,dilution_norm)
               );
               CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
               INSERT INTO developer_dilutions VALUES(
                 'foma universal','1+3','1+3','TEST'
               );
               INSERT INTO developer_dilutions VALUES(
                 '123 pyro','1+100','1+100','TEST'
               );'''
        )
        connection.commit()
        connection.close()
        payload = {
            "schemaVersion": 2,
            "basis": "test",
            "checkedAt": "2026-09-01",
            "catalogSource": "https://www.macodirect.de/",
            "scope": [
                {
                    "developerNorm": "foma universal",
                    "developerName": "Foma Universal",
                    "macoProduct": "Foma universal developer",
                    "macoUrl": "https://www.macodirect.de/",
                    "availability": "ready_to_ship",
                    "matchNote": "",
                }
            ],
            "records": [
                {
                    "developerNorm": "foma universal",
                    "dilutionNorm": "1+3",
                    "minWorkingMl500cm2": 333.333333,
                    "minWorkingMl4x5One": 83.333333,
                    "minWorkingMl4x5Two": 166.666667,
                    "evidenceKind": "MANUFACTURER_CAPACITY",
                    "sourceTitle": "FOMA",
                    "sourceUrl": "https://www.foma.cz/",
                    "note": "test",
                }
            ],
        }
        self.records_file.write_text(json.dumps(payload), encoding="utf-8")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_apply_schema_scope_values_and_outside_scope_policy(self):
        counts = APPLIER.apply(self.database, self.records_file)
        self.assertEqual(
            {
                "total": 2,
                "populated": 1,
                "unpopulated": 1,
                "scope": 1,
                "manufacturer": 1,
                "operational": 0,
            },
            counts,
        )
        connection = sqlite3.connect(self.database)
        try:
            self.assertEqual(
                (333.333333, 83.333333, 166.666667),
                connection.execute(
                    '''SELECT min_working_ml_500cm2,min_working_ml_4x5_1,
                              min_working_ml_4x5_2
                       FROM developer_dilutions
                       WHERE developer_norm='foma universal' AND dilution_norm='1+3' '''
                ).fetchone(),
            )
            self.assertEqual(
                (None, None, None),
                connection.execute(
                    '''SELECT min_working_ml_500cm2,min_working_ml_4x5_1,
                              min_working_ml_4x5_2
                       FROM developer_dilutions
                       WHERE developer_norm='123 pyro' AND dilution_norm='1+100' '''
                ).fetchone(),
            )
            self.assertEqual(
                "MANUFACTURER_CAPACITY",
                connection.execute(
                    "SELECT evidence_kind FROM developer_minimum_volume_sources"
                ).fetchone()[0],
            )
            self.assertEqual(1, connection.execute(
                "SELECT COUNT(*) FROM maco_developer_scope"
            ).fetchone()[0])
            self.assertEqual(5, connection.execute("PRAGMA user_version").fetchone()[0])
            self.assertEqual("ok", connection.execute("PRAGMA quick_check").fetchone()[0])
        finally:
            connection.close()

    def test_apply_is_idempotent(self):
        first = APPLIER.apply(self.database, self.records_file)
        second = APPLIER.apply(self.database, self.records_file)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
