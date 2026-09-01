#!/usr/bin/env python3
"""Prepare the historical build chain for a refreshed, larger MDC snapshot."""

from pathlib import Path


ROOT = Path("combined")
BUILD_V011 = ROOT / "build_v011.sh"

text = BUILD_V011.read_text(encoding="utf-8")
marker = "python3 assistant/build_mdc_sqlite_asset_v032.py"
injected = (
    "python3 combined/patch_v056_mdc_download_source.py\n"
    "python3 assistant/build_mdc_sqlite_asset_v032.py"
)
if injected not in text:
    if text.count(marker) != 1:
        raise SystemExit("v0.5.6 build_v011 MDC builder marker missing")
    text = text.replace(marker, injected, 1)
    BUILD_V011.write_text(text, encoding="utf-8")

# Releases v0.3.3-v0.4.8 protected the original 14,504-row snapshot with an
# exact equality check. A refresh may only add rows, so retain the data-loss
# guard as a lower bound instead of rejecting a newer valid snapshot.
changed = 0
for path in sorted(ROOT.glob("build_v*.sh")):
    if path.name in {"build_v055.sh", "build_v056.sh"}:
        continue
    source = path.read_text(encoding="utf-8")
    updated = source
    updated = updated.replace("combinations!=14504", "combinations<14504")
    updated = updated.replace("mdc_dils!=776", "mdc_dils<776")
    updated = updated.replace("== 14504", ">= 14504")
    updated = updated.replace("==14504", ">=14504")
    updated = updated.replace("mdc_times_unchanged=14504", "mdc_times_at_least=14504")
    updated = updated.replace("mdc_combinations=14504", "mdc_combinations_at_least=14504")
    if updated != source:
        path.write_text(updated, encoding="utf-8")
        changed += 1

if changed < 10:
    raise SystemExit(f"v0.5.6 expected historical row guards, changed only {changed} scripts")

print(f"Darkroom v0.5.6 build chain ready; relaxed {changed} additive snapshot guards")
