#!/usr/bin/env python3
"""Force installation of the v0.5.7 bundled offline snapshot."""

from pathlib import Path


STORE = Path("combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java")
ACTIVITY = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")
source = STORE.read_text(encoding="utf-8")
old = '    private static final String DB_NAME = "mdc_offline_darkroom_v056.sqlite";'
new = '    private static final String DB_NAME = "mdc_offline_darkroom_v057.sqlite";'
if source.count(old) != 1:
    raise SystemExit("v0.5.7 database filename marker missing")
STORE.write_text(source.replace(old, new, 1), encoding="utf-8")

# Prefer dilutions documented for the exact film/developer combination.  When
# the time snapshot has no row for that combination, keep the developer usable
# offline by falling back to its technical product dilutions.  This is a
# catalogue-wide rule, not a special case for FOMADON Excel.
activity = ACTIVITY.read_text(encoding="utf-8")
old_refresh = '''        String[] values;
        if (selectedFilm != null && selectedFilmDeveloper != null) {
            values = MdcOfflineStore.dilutionsForCombination(
                    selectedFilm.name, selectedFilmDeveloper.name);
        } else if (selectedFilmDeveloper != null &&
                selectedFilmDeveloper.filmDilutions.length > 0) {
            values = selectedFilmDeveloper.filmDilutions;
        } else {
            values = new String[0];
        }
        if (values.length == 0) values = new String[]{"—"};'''
new_refresh = '''        String[] values = new String[0];
        if (selectedFilm != null && selectedFilmDeveloper != null) {
            values = MdcOfflineStore.dilutionsForCombination(
                    selectedFilm.name, selectedFilmDeveloper.name);
        }
        if (values.length == 0 && selectedFilmDeveloper != null &&
                selectedFilmDeveloper.filmDilutions.length > 0) {
            values = selectedFilmDeveloper.filmDilutions;
        }
        if (values.length == 0) values = new String[]{"—"};'''
if activity.count(old_refresh) != 1:
    raise SystemExit("v0.5.7 dilution fallback marker missing")
activity = activity.replace(old_refresh, new_refresh, 1)
ACTIVITY.write_text(activity, encoding="utf-8")

print("Darkroom v0.5.7 runtime uses a fresh bundled offline snapshot")
print("Developer technical dilution fallback enabled for missing MDC combinations")
