#!/usr/bin/env python3
"""Generate minimum-volume rows for the Maco Direct developer scope."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


DEFAULT_RULES = Path(__file__).with_name("maco_developer_rules_v053.json")


def _rounded(value: float) -> float:
    return round(float(value), 6)


def _parts(dilution: str, aliases: dict[str, str] | None = None) -> list[float]:
    normalized = dilution.strip().lower().replace(":", "+").replace(" ", "")
    if aliases and normalized in aliases:
        normalized = aliases[normalized]
    if normalized == "stock":
        return [1.0]
    chunks = normalized.split("+")
    if len(chunks) < 2:
        raise ValueError(f"unsupported dilution: {dilution}")
    try:
        values = [float(chunk) for chunk in chunks]
    except ValueError as exc:
        raise ValueError(f"non-numeric dilution: {dilution}") from exc
    if any(value <= 0 for value in values):
        raise ValueError(f"non-positive dilution: {dilution}")
    return values


def minimum_for_dilution(rule: dict, dilution_norm: str) -> float:
    overrides = rule.get("overrides", {})
    if dilution_norm in overrides:
        return float(overrides[dilution_norm])

    kind = rule["kind"]
    if kind == "fixed_working":
        return float(rule["workingMl500cm2"])

    values = _parts(dilution_norm, rule.get("dilutionAliases"))
    if kind == "active_solution":
        active = float(rule["activeMl500cm2"])
        if len(values) == 1:
            return active
        developer_parts = sum(values[:-1])
        return active * sum(values) / developer_parts

    if kind == "two_component_minima":
        if len(values) < 3:
            raise ValueError(
                f"two-component rule requires A+B+water dilution: {dilution_norm}"
            )
        minimums = [float(value) for value in rule["minimumComponentMl500cm2"]]
        developer_parts = values[:-1]
        if len(minimums) != len(developer_parts):
            raise ValueError(
                f"component count mismatch for dilution {dilution_norm}: "
                f"{len(minimums)} minima / {len(developer_parts)} components"
            )
        scale = max(
            minimum / component
            for minimum, component in zip(minimums, developer_parts)
        )
        return scale * sum(values)

    raise ValueError(f"unsupported minimum-volume rule kind: {kind}")


def generate(database: Path, rules_file: Path = DEFAULT_RULES) -> dict:
    rules_payload = json.loads(rules_file.read_text(encoding="utf-8"))
    developers = rules_payload["developers"]
    norms = [entry["developerNorm"] for entry in developers]
    if len(norms) != len(set(norms)):
        raise RuntimeError("duplicate developerNorm in Maco scope")

    connection = sqlite3.connect(database)
    try:
        records: list[dict] = []
        scope: list[dict] = []
        for entry in developers:
            developer_norm = entry["developerNorm"]
            rows = connection.execute(
                """SELECT dilution_norm
                   FROM developer_dilutions
                   WHERE developer_norm=?
                   ORDER BY dilution_norm""",
                (developer_norm,),
            ).fetchall()
            if not rows:
                raise RuntimeError(
                    f"Maco-scope developer missing from database: {developer_norm}"
                )
            scope.append(
                {
                    "developerNorm": developer_norm,
                    "developerName": entry["developerName"],
                    "macoProduct": entry["macoProduct"],
                    "macoUrl": rules_payload["catalogSource"]
                    + ("" if entry["macoPage"] == 1 else f"?p={entry['macoPage']}"),
                    "availability": entry["availability"],
                    "matchNote": entry.get("matchNote", ""),
                }
            )
            for (dilution_norm,) in rows:
                minimum_500 = minimum_for_dilution(entry["rule"], dilution_norm)
                if minimum_500 <= 0:
                    raise RuntimeError(
                        f"invalid minimum for {developer_norm}/{dilution_norm}"
                    )
                records.append(
                    {
                        "developerNorm": developer_norm,
                        "dilutionNorm": dilution_norm,
                        "minWorkingMl500cm2": _rounded(minimum_500),
                        "minWorkingMl4x5One": _rounded(minimum_500 / 4.0),
                        "minWorkingMl4x5Two": _rounded(minimum_500 / 2.0),
                        "evidenceKind": entry["evidenceKind"],
                        "sourceTitle": entry["sourceTitle"],
                        "sourceUrl": entry["sourceUrl"],
                        "note": entry["note"],
                    }
                )
    finally:
        connection.close()

    return {
        "schemaVersion": 2,
        "basis": rules_payload["basis"],
        "checkedAt": rules_payload["checkedAt"],
        "catalogSource": rules_payload["catalogSource"],
        "scope": scope,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = generate(args.database, args.rules)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Maco scope: {len(payload['scope'])} developers, "
        f"{len(payload['records'])} developer+dilution rows"
    )


if __name__ == "__main__":
    main()
