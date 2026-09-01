#!/usr/bin/env python3
"""Offline MDC selection, compatible dilutions, and compact result layout."""

from pathlib import Path
import re


ROOT = Path("combined/src/main/java/it/darkroom/assistant")
STORE = ROOT / "MdcOfflineStore.java"
ACTIVITY = ROOT / "AssistantActivityV2.java"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.5.6 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


# Database lookup: fresh on-device copy, combination-specific dilutions, and
# deterministic preference for a real Sheet value over a conflicting MDC row.
store = STORE.read_text(encoding="utf-8")
store = replace_once(
    store,
    '    private static final String DB_NAME = "mdc_offline_darkroom_v054.sqlite";',
    '    private static final String DB_NAME = "mdc_offline_darkroom_v056.sqlite";',
    "fresh database filename",
)

dilution_marker = "    static int nominalIsoForFilm(String film) {"
dilution_method = r'''    static String[] dilutionsForCombination(String filmName, String developer) {
        if (!isReady() || filmName == null || developer == null) return new String[0];
        String wantedFilm = stripFormat(filmName);
        String canonicalFilm = FullCatalogStore.canonicalFilm(wantedFilm);
        if (canonicalFilm != null) wantedFilm = canonicalFilm;
        String canonicalDeveloper = FullCatalogStore.canonicalDeveloper(developer);
        String wantedDeveloper = canonicalDeveloper == null ? developer : canonicalDeveloper;

        LinkedHashSet<String> values = new LinkedHashSet<>();
        SQLiteDatabase db = helper.getReadableDatabase();
        try (Cursor c = db.rawQuery(
                "SELECT dilution FROM times WHERE film_norm=? AND developer_norm=? " +
                        "AND dilution<>'' GROUP BY dilution ORDER BY dilution",
                new String[]{norm(wantedFilm), norm(wantedDeveloper)})) {
            while (c.moveToNext()) values.add(c.getString(0));
        }
        return values.toArray(new String[0]);
    }

'''
if dilution_marker not in store:
    raise SystemExit("v0.5.6 dilution insertion marker missing")
store = store.replace(dilution_marker, dilution_method + dilution_marker, 1)

lookup_marker = "    static DevTimeEngine.Result lookup(String filmName, String format, String developer,"
ranking_helpers = r'''    private static String timeForFormat(TimeRow row, String format) {
        boolean sheet = "4x5".equalsIgnoreCase(format) || "sheet".equalsIgnoreCase(format);
        return sheet ? row.timeSheet : ("120".equals(format) ? row.time120 : row.time35);
    }

    private static boolean conflictingSubmission(TimeRow row) {
        return row != null && row.notes != null && row.notes.contains("[63]");
    }

    private static String appendWarning(String current, String extra) {
        if (extra == null || extra.isEmpty()) return current == null ? "" : current;
        if (current == null || current.isEmpty()) return extra;
        return current + "\n" + extra;
    }

'''
if lookup_marker not in store:
    raise SystemExit("v0.5.6 lookup insertion marker missing")
store = store.replace(lookup_marker, ranking_helpers + lookup_marker, 1)

old_sort = "        Collections.sort(candidates, (a,b) -> Double.compare(Math.abs(a.temp-targetTemp), Math.abs(b.temp-targetTemp)));"
new_sort = r'''        Collections.sort(candidates, (a, b) -> {
            int byTemperature = Double.compare(
                    Math.abs(a.temp - targetTemp), Math.abs(b.temp - targetTemp));
            if (byTemperature != 0) return byTemperature;
            int byFormat = Boolean.compare(
                    !hasTime(timeForFormat(a, format)), !hasTime(timeForFormat(b, format)));
            if (byFormat != 0) return byFormat;
            // MDC note [63] marks a contradictory user submission. Keep it only
            // as a last resort when no non-conflicting exact row is available.
            return Boolean.compare(conflictingSubmission(a), conflictingSubmission(b));
        });'''
store = replace_once(store, old_sort, new_sort, "MDC candidate ranking")

warning_marker = '''            if (crossFormat) {
                if (!warning.isEmpty()) warning += "\\n";
                warning += "Digitaltruth non riporta un tempo per questo formato: usato il tempo disponibile per un altro formato come punto di partenza.";
            }
            return new DevTimeEngine.Result'''
warning_replacement = '''            if (crossFormat) {
                if (!warning.isEmpty()) warning += "\\n";
                warning += "Digitaltruth non riporta un tempo per questo formato: usato il tempo disponibile per un altro formato come punto di partenza.";
            }
            if (row.notes != null && row.notes.contains("[40]")) {
                warning = appendWarning(warning,
                        "Nota MDC: questo tempo prevede un prelavaggio di 3–5 minuti.");
            }
            if (conflictingSubmission(row)) {
                warning = appendWarning(warning,
                        "Nota MDC: utilizzata una segnalazione utente contraddittoria perché non era disponibile un'alternativa esatta.");
            }
            return new DevTimeEngine.Result'''
store = replace_once(store, warning_marker, warning_replacement, "MDC note warnings")
STORE.write_text(store, encoding="utf-8")


# UI: list only dilutions present for the selected film/developer combination.
activity = ACTIVITY.read_text(encoding="utf-8")
old_listener = '''        developerSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                selectedFilmDeveloper = productAt(developers, position);
                String[] ds = selectedFilmDeveloper == null ||
                        selectedFilmDeveloper.filmDilutions.length == 0
                        ? new String[]{"—"} : selectedFilmDeveloper.filmDilutions;
                setSpinnerItems(dilutionSpinner, ds);
            }
        });'''
new_listener = '''        developerSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                selectedFilmDeveloper = productAt(developers, position);
                refreshFilmDilutions();
            }
        });'''
activity = replace_once(activity, old_listener, new_listener, "developer dilution listener")

wire_marker = "    private void wireFilmSearch(AutoCompleteTextView field,"
refresh_method = r'''    private void refreshFilmDilutions() {
        if (dilutionSpinner == null) return;
        String previous = spinnerText(dilutionSpinner);
        String[] values;
        if (selectedFilm != null && selectedFilmDeveloper != null) {
            values = MdcOfflineStore.dilutionsForCombination(
                    selectedFilm.name, selectedFilmDeveloper.name);
        } else if (selectedFilmDeveloper != null &&
                selectedFilmDeveloper.filmDilutions.length > 0) {
            values = selectedFilmDeveloper.filmDilutions;
        } else {
            values = new String[0];
        }
        if (values.length == 0) values = new String[]{"—"};
        setSpinnerItems(dilutionSpinner, values);
        if (previous != null && !previous.isEmpty()) selectSpinnerText(dilutionSpinner, previous);
    }

'''
if wire_marker not in activity:
    raise SystemExit("v0.5.6 film dilution helper marker missing")
activity = activity.replace(wire_marker, refresh_method + wire_marker, 1)

select_pattern = re.compile(
    r'''    private void selectFilm\(FilmStock f\) \{.*?\n    \}\n\n(?=    private void updateCompatibleTanks\(\))''',
    re.S,
)
match = select_pattern.search(activity)
if not match:
    raise SystemExit("v0.5.6 selectFilm method missing")
select_method = match.group(0)
updated_select = select_method.replace(
    "            updateCompatibleTanks();",
    "            refreshFilmDilutions();\n            updateCompatibleTanks();",
).replace(
    "        updateCompatibleTanks();",
    "        refreshFilmDilutions();\n        updateCompatibleTanks();",
)
if updated_select.count("refreshFilmDilutions();") < 2:
    raise SystemExit("v0.5.6 film selection dilution refresh incomplete")
activity = activity[:match.start()] + updated_select + activity[match.end():]


# The first card shows the answer only. Repeated combination/tank details remain
# available on demand in the calculation accordion.
summary_details = '''        addUnifiedChemicalField(summary, "COMBINAZIONE",
                filmName + " · " + dev.name + " " + dilution);
        addUnifiedChemicalField(summary, "TANK / VOLUME",
                tankDisplayName(tank, loadFormat) + " · " + fmt(workingVolumeMl) +
                        " ml (minimo tank " + fmt(tank.rotaryMl) + " ml)");
'''
activity = replace_once(activity, summary_details, "", "duplicate summary details")

calculation_marker = "        LinearLayout calculation = accordionBody();\n"
calculation_details = '''        LinearLayout calculation = accordionBody();
        addUnifiedChemicalField(calculation, "COMBINAZIONE",
                filmName + " · " + dev.name + " " + dilution);
        addUnifiedChemicalField(calculation, "TANK / VOLUME",
                tankDisplayName(tank, loadFormat) + " · " + fmt(workingVolumeMl) +
                        " ml (minimo tank " + fmt(tank.rotaryMl) + " ml)");
'''
activity = replace_once(
    activity, calculation_marker, calculation_details, "calculation detail insertion"
)

ACTIVITY.write_text(activity, encoding="utf-8")

for expected in (
    'DB_NAME = "mdc_offline_darkroom_v056.sqlite"',
    "dilutionsForCombination",
    "timeForFormat",
    "conflictingSubmission",
    "prelavaggio di 3–5 minuti",
):
    if expected not in STORE.read_text(encoding="utf-8"):
        raise SystemExit("v0.5.6 store guard failed: " + expected)

for expected in (
    "refreshFilmDilutions",
    "MdcOfflineStore.dilutionsForCombination",
    'addUnifiedChemicalField(calculation, "COMBINAZIONE"',
    'addUnifiedChemicalField(calculation, "TANK / VOLUME"',
):
    if expected not in activity:
        raise SystemExit("v0.5.6 activity guard failed: " + expected)

if 'addUnifiedChemicalField(summary, "COMBINAZIONE"' in activity:
    raise SystemExit("v0.5.6 combination still duplicated in summary")
if 'addUnifiedChemicalField(summary, "TANK / VOLUME"' in activity:
    raise SystemExit("v0.5.6 tank still duplicated in summary")

print("Darkroom v0.5.6 offline MDC selection and compact UI ready")
