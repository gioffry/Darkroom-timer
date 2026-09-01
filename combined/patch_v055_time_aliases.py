#!/usr/bin/env python3
"""Resolve commercial developer aliases before looking up MDC times."""

from pathlib import Path


ROOT = Path("combined/src/main/java/it/darkroom/assistant")
STORE = ROOT / "MdcOfflineStore.java"
ACTIVITY = ROOT / "AssistantActivityV2.java"


store = STORE.read_text(encoding="utf-8")
old = "        String dn = norm(developer);"
count = store.count(old)
if count not in (1, 2):
    raise SystemExit(f"v0.5.5 developer alias normalization: expected 1 or 2 markers, found {count}")
new = '''        String canonicalDeveloper = FullCatalogStore.canonicalDeveloper(developer);
        String dn = norm(canonicalDeveloper == null ? developer : canonicalDeveloper);'''
store = store.replace(old, new)
STORE.write_text(store, encoding="utf-8")


activity = ACTIVITY.read_text(encoding="utf-8")
old = '''            DevTimeEngine.Result result = MdcOfflineStore.lookup(
                    selectedFilm.name, selectedFilm.format, dev.name, dilution, iso, temp);
            runOnUiThread(() -> showDevelopmentResultSafely(result, tank, rolls,'''
new = '''            DevTimeEngine.Result exactResult = MdcOfflineStore.lookup(
                    selectedFilm.name, selectedFilm.format, dev.name, dilution, iso, temp);
            DevTimeEngine.Result result = exactResult != null
                    ? exactResult
                    : DevTimeEngine.Result.notFound(MdcOfflineStore.combinationDiagnostic(
                            selectedFilm.name, dev.name, dilution, iso));
            runOnUiThread(() -> showDevelopmentResultSafely(result, tank, rolls,'''
if activity.count(old) != 1:
    raise SystemExit("v0.5.5 null MDC result marker missing")
activity = activity.replace(old, new, 1)
ACTIVITY.write_text(activity, encoding="utf-8")

store = STORE.read_text(encoding="utf-8")
activity = ACTIVITY.read_text(encoding="utf-8")
canonical_calls = store.count("FullCatalogStore.canonicalDeveloper(developer)")
if canonical_calls < 2:
    raise SystemExit("v0.5.5 canonical developer guards failed")
for expected in (
    "DevTimeEngine.Result exactResult",
    "DevTimeEngine.Result.notFound",
    "MdcOfflineStore.combinationDiagnostic",
):
    if expected not in activity:
        raise SystemExit("v0.5.5 time lookup guard failed: " + expected)

print("Darkroom v0.5.5 developer time aliases ready")
