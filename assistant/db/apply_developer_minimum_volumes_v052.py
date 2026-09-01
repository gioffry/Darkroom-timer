#!/usr/bin/env python3
"""Add sourced minimum working volumes to every developer+dilution row."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


COLUMNS = (
    ("min_working_ml_500cm2", "REAL"),
    ("min_working_ml_4x5_1", "REAL"),
    ("min_working_ml_4x5_2", "REAL"),
)


def apply(database: Path, records_file: Path) -> dict[str, int]:
    payload = json.loads(records_file.read_text(encoding="utf-8"))
    records = payload["records"]
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        existing = {
            row[1] for row in connection.execute("PRAGMA table_info(developer_dilutions)")
        }
        with connection:
            for name, sql_type in COLUMNS:
                if name not in existing:
                    connection.execute(
                        f"ALTER TABLE developer_dilutions ADD COLUMN {name} {sql_type}"
                    )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS developer_minimum_volume_sources(
                     developer_norm TEXT NOT NULL,
                     dilution_norm TEXT NOT NULL,
                     source_title TEXT NOT NULL,
                     source_url TEXT NOT NULL,
                     checked_at TEXT NOT NULL,
                     note TEXT,
                     PRIMARY KEY(developer_norm,dilution_norm)
                   )"""
            )
            # Idempotency matters because historical build wrappers may be retried.
            connection.execute(
                """UPDATE developer_dilutions
                   SET min_working_ml_500cm2=NULL,
                       min_working_ml_4x5_1=NULL,
                       min_working_ml_4x5_2=NULL"""
            )
            connection.execute("DELETE FROM developer_minimum_volume_sources")

            matched = 0
            for record in records:
                key = (record["developerNorm"], record["dilutionNorm"])
                cursor = connection.execute(
                    """UPDATE developer_dilutions
                       SET min_working_ml_500cm2=?,
                           min_working_ml_4x5_1=?,
                           min_working_ml_4x5_2=?
                       WHERE developer_norm=? AND dilution_norm=?""",
                    (
                        record["minWorkingMl500cm2"],
                        record["minWorkingMl4x5One"],
                        record["minWorkingMl4x5Two"],
                        *key,
                    ),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "minimum-volume record does not match exactly one database row: "
                        + "/".join(key)
                    )
                matched += 1
                connection.execute(
                    """INSERT INTO developer_minimum_volume_sources(
                           developer_norm,dilution_norm,source_title,source_url,checked_at,note
                       ) VALUES(?,?,?,?,?,?)""",
                    (
                        *key,
                        record["sourceTitle"],
                        record["sourceUrl"],
                        payload["checkedAt"],
                        record.get("note", ""),
                    ),
                )

            connection.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                ("developer_minimum_volume_schema", "v052"),
            )
            connection.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                ("developer_minimum_volume_verified_rows", str(matched)),
            )
            connection.execute("PRAGMA user_version=4")

        total = connection.execute(
            "SELECT COUNT(*) FROM developer_dilutions"
        ).fetchone()[0]
        verified = connection.execute(
            """SELECT COUNT(*) FROM developer_dilutions
               WHERE min_working_ml_500cm2 IS NOT NULL
                 AND min_working_ml_4x5_1 IS NOT NULL
                 AND min_working_ml_4x5_2 IS NOT NULL"""
        ).fetchone()[0]
        partial = connection.execute(
            """SELECT COUNT(*) FROM developer_dilutions
               WHERE (min_working_ml_500cm2 IS NULL) +
                     (min_working_ml_4x5_1 IS NULL) +
                     (min_working_ml_4x5_2 IS NULL) NOT IN (0,3)"""
        ).fetchone()[0]
        integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
        if integrity != "ok" or partial != 0 or verified != len(records):
            raise RuntimeError(
                f"database validation failed: integrity={integrity}, "
                f"verified={verified}, partial={partial}"
            )
        return {"total": total, "verified": verified, "unverified": total - verified}
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument(
        "--records",
        type=Path,
        default=Path(__file__).with_name("developer_minimum_volumes_v052.json"),
    )
    args = parser.parse_args()
    counts = apply(args.database, args.records)
    print(
        "developer minimum volumes: "
        f"{counts['verified']} verified, {counts['unverified']} unverified, "
        f"{counts['total']} total dilution rows"
    )


if __name__ == "__main__":
    main()
