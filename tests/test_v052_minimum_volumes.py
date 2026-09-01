#!/usr/bin/env python3

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "assistant/db/apply_developer_minimum_volumes_v052.py"
SPEC = importlib.util.spec_from_file_location("minimum_volumes_v052", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class MinimumVolumeDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "mdc.sqlite"
        self.records = ROOT / "assistant/db/developer_minimum_volumes_v052.json"
        payload = json.loads(self.records.read_text(encoding="utf-8"))
        connection = sqlite3.connect(self.database)
        connection.executescript(
            '''CREATE TABLE developer_dilutions(
                 developer_norm TEXT NOT NULL,
                 dilution TEXT NOT NULL,
                 dilution_norm TEXT NOT NULL,
                 source_kind TEXT NOT NULL,
                 source_url TEXT,
                 source_title TEXT,
                 verified_at TEXT,
                 PRIMARY KEY(developer_norm,dilution_norm)
               );
               CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);'''
        )
        for record in payload["records"]:
            connection.execute(
                '''INSERT INTO developer_dilutions(
                     developer_norm,dilution,dilution_norm,source_kind
                   ) VALUES(?,?,?,?)''',
                (
                    record["developerNorm"],
                    record["dilutionNorm"],
                    record["dilutionNorm"],
                    "TEST",
                ),
            )
        connection.execute(
            '''INSERT INTO developer_dilutions(
                 developer_norm,dilution,dilution_norm,source_kind
               ) VALUES('123 pyro','1+100','1+100','TEST')'''
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_schema_values_and_unknown_policy(self):
        counts = MODULE.apply(self.database, self.records)
        self.assertEqual(12, counts["total"])
        self.assertEqual(11, counts["verified"])
        self.assertEqual(1, counts["unverified"])
        connection = sqlite3.connect(self.database)
        try:
            row = connection.execute(
                '''SELECT min_working_ml_500cm2,min_working_ml_4x5_1,min_working_ml_4x5_2
                   FROM developer_dilutions
                   WHERE developer_norm='foma universal' AND dilution_norm='1+3' '''
            ).fetchone()
            self.assertEqual((340.0, 85.0, 170.0), row)
            unknown = connection.execute(
                '''SELECT min_working_ml_500cm2,min_working_ml_4x5_1,min_working_ml_4x5_2
                   FROM developer_dilutions
                   WHERE developer_norm='123 pyro' AND dilution_norm='1+100' '''
            ).fetchone()
            self.assertEqual((None, None, None), unknown)
            self.assertEqual(4, connection.execute("PRAGMA user_version").fetchone()[0])
            self.assertEqual("ok", connection.execute("PRAGMA quick_check").fetchone()[0])
        finally:
            connection.close()

    def test_patch_is_idempotent(self):
        first = MODULE.apply(self.database, self.records)
        second = MODULE.apply(self.database, self.records)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
