#!/usr/bin/env python3
"""Apply the Maco-scoped v0.5.3 developer minimum-volume dataset."""

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
    scope = payload["scope"]
    record_keys = {
        (record["developerNorm"], record["dilutionNorm"]) for record in records
    }
    if len(record_keys) != len(records):
        raise RuntimeError("duplicate developer+dilution record in v0.5.3 dataset")

    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        dilution_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(developer_dilutions)")
        }
        with connection:
            for name, sql_type in COLUMNS:
                if name not in dilution_columns:
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
                     evidence_kind TEXT NOT NULL DEFAULT 'UNKNOWN',
                     PRIMARY KEY(developer_norm,dilution_norm)
                   )"""
            )
            source_columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(developer_minimum_volume_sources)"
                )
            }
            if "evidence_kind" not in source_columns:
                connection.execute(
                    """ALTER TABLE developer_minimum_volume_sources
                       ADD COLUMN evidence_kind TEXT NOT NULL DEFAULT 'UNKNOWN'"""
                )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS maco_developer_scope(
                     developer_norm TEXT PRIMARY KEY,
                     developer_name TEXT NOT NULL,
                     maco_product_title TEXT NOT NULL,
                     maco_url TEXT NOT NULL,
                     availability TEXT NOT NULL,
                     checked_at TEXT NOT NULL,
                     match_note TEXT
                   )"""
            )

            # Historical wrappers can be rerun safely: v0.5.3 owns the complete
            # current scope and deliberately clears the earlier partial census.
            connection.execute(
                """UPDATE developer_dilutions
                   SET min_working_ml_500cm2=NULL,
                       min_working_ml_4x5_1=NULL,
                       min_working_ml_4x5_2=NULL"""
            )
            connection.execute("DELETE FROM developer_minimum_volume_sources")
            connection.execute("DELETE FROM maco_developer_scope")

            for item in scope:
                connection.execute(
                    """INSERT INTO maco_developer_scope(
                           developer_norm,developer_name,maco_product_title,maco_url,
                           availability,checked_at,match_note
                       ) VALUES(?,?,?,?,?,?,?)""",
                    (
                        item["developerNorm"],
                        item["developerName"],
                        item["macoProduct"],
                        item["macoUrl"],
                        item["availability"],
                        payload["checkedAt"],
                        item.get("matchNote", ""),
                    ),
                )

            matched = 0
            manufacturer_rows = 0
            operational_rows = 0
            for record in records:
                minimum_500 = float(record["minWorkingMl500cm2"])
                minimum_one = float(record["minWorkingMl4x5One"])
                minimum_two = float(record["minWorkingMl4x5Two"])
                if abs(minimum_one * 4 - minimum_500) > 0.00001:
                    raise RuntimeError("one-sheet area ratio mismatch: " + str(record))
                if abs(minimum_two * 2 - minimum_500) > 0.00001:
                    raise RuntimeError("two-sheet area ratio mismatch: " + str(record))
                key = (record["developerNorm"], record["dilutionNorm"])
                cursor = connection.execute(
                    """UPDATE developer_dilutions
                       SET min_working_ml_500cm2=?,
                           min_working_ml_4x5_1=?,
                           min_working_ml_4x5_2=?
                       WHERE developer_norm=? AND dilution_norm=?""",
                    (minimum_500, minimum_one, minimum_two, *key),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "minimum-volume record does not match exactly one database row: "
                        + "/".join(key)
                    )
                evidence_kind = record["evidenceKind"]
                if evidence_kind == "CONSERVATIVE_OPERATIONAL":
                    operational_rows += 1
                else:
                    manufacturer_rows += 1
                matched += 1
                connection.execute(
                    """INSERT INTO developer_minimum_volume_sources(
                           developer_norm,dilution_norm,source_title,source_url,
                           checked_at,note,evidence_kind
                       ) VALUES(?,?,?,?,?,?,?)""",
                    (
                        *key,
                        record["sourceTitle"],
                        record["sourceUrl"],
                        payload["checkedAt"],
                        record.get("note", ""),
                        evidence_kind,
                    ),
                )

            metadata = {
                "developer_minimum_volume_schema": "v053",
                "developer_minimum_volume_populated_rows": str(matched),
                "developer_minimum_volume_manufacturer_rows": str(manufacturer_rows),
                "developer_minimum_volume_operational_rows": str(operational_rows),
                "maco_scope_developers": str(len(scope)),
                "maco_scope_checked_at": payload["checkedAt"],
                "maco_scope_catalog_url": payload["catalogSource"],
            }
            for key, value in metadata.items():
                connection.execute(
                    "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, value)
                )
            connection.execute("PRAGMA user_version=5")

        total = connection.execute(
            "SELECT COUNT(*) FROM developer_dilutions"
        ).fetchone()[0]
        populated = connection.execute(
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
        if integrity != "ok" or partial != 0 or populated != len(records):
            raise RuntimeError(
                f"database validation failed: integrity={integrity}, "
                f"populated={populated}, partial={partial}"
            )
        return {
            "total": total,
            "populated": populated,
            "unpopulated": total - populated,
            "scope": len(scope),
            "manufacturer": manufacturer_rows,
            "operational": operational_rows,
        }
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--records", type=Path, required=True)
    args = parser.parse_args()
    counts = apply(args.database, args.records)
    print(
        "developer minimum volumes: "
        f"{counts['populated']} populated ({counts['manufacturer']} manufacturer, "
        f"{counts['operational']} conservative operational), "
        f"{counts['unpopulated']} outside Maco scope, {counts['total']} total; "
        f"{counts['scope']} Maco developers"
    )


if __name__ == "__main__":
    main()
