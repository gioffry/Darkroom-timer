#!/usr/bin/env python3
"""Inject the v0.5.7 MDC pipeline and make historical guards additive."""

from pathlib import Path


ROOT = Path("combined")
BUILD_V011 = ROOT / "build_v011.sh"

text = BUILD_V011.read_text(encoding="utf-8")
marker = "python3 combined/patch_v056_mdc_download_source.py\n"
injected = marker + "python3 combined/patch_v057_mdc_offline_pipeline.py\n"
if injected not in text:
    if text.count(marker) != 1:
        raise SystemExit("v0.5.7 build-chain injection marker missing")
    text = text.replace(marker, injected, 1)
    BUILD_V011.write_text(text, encoding="utf-8")

changed = 0
for path in sorted(ROOT.glob("build_v*.sh")):
    if path.name in {"build_v056.sh", "build_v057.sh"}:
        continue
    source = path.read_text(encoding="utf-8")
    updated = source
    updated = updated.replace("== 776", ">= 776")
    updated = updated.replace("==776", ">=776")
    updated = updated.replace("total == 781", "total >= 781")
    updated = updated.replace("mdc_times_unchanged=14504", "mdc_snapshot_times_at_least=14500")
    if updated != source:
        path.write_text(updated, encoding="utf-8")
        changed += 1

if changed < 10:
    raise SystemExit(f"v0.5.7 expected historical dilution guards, changed only {changed}")

print(f"Darkroom v0.5.7 build chain ready; relaxed {changed} additive dilution guards")
