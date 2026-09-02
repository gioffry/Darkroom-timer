#!/usr/bin/env python3
"""Install the audited, one-hop developer-equivalence fallback for v0.5.8."""

from pathlib import Path
import sqlite3


ROOT = Path("combined/src/main/java/it/darkroom/assistant")
STORE = ROOT / "MdcOfflineStore.java"
ACTIVITY = ROOT / "AssistantActivityV2.java"
DATABASE = Path("combined/src/main/assets/mdc_full.sqlite")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.5.8 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


# This is intentionally directional and explicit. The runtime never follows a
# second mapping, and never guesses by name or by chemical family.
rules = []


def same(selected, source, dilutions):
    for dilution in dilutions:
        rules.append((selected, dilution, source, dilution))


same("ID-11", "D-76", ("stock", "1+1", "1+3"))
same("D-76", "ID-11", ("stock", "1+1", "1+3"))
same("Fomadon P", "D-76", ("stock", "1+1", "1+3"))
same("XT-3", "Xtol", ("stock", "1+1"))
same("Xtol", "XT-3", ("stock", "1+1"))
same("Fomadon Excel", "Xtol", ("stock", "1+1"))
same("Fomadon R09", "Rodinal", ("1+25", "1+50"))
rules.append(("Bellini Euro HC", "1+31", "HC-110", "B"))
rules.append(("Bellini DF2 Duo Step", "stock", "Diafine", "stock"))
same(
    "Spur TRX 2000",
    "Adox HR-DEV",
    ("1+14", "1+17", "1+19", "1+20", "1+24", "1+30", "1+35", "1+40", "1+49"),
)
same(
    "Adox HR-DEV",
    "Spur TRX 2000",
    ("1+14", "1+17", "1+19", "1+20", "1+24", "1+30", "1+35", "1+40", "1+49"),
)
same("Rollei Supergrain", "Amaloco AM74", ("1+9", "1+15"))


def norm(value: str) -> str:
    import re
    import unicodedata

    value = unicodedata.normalize("NFD", value or "").lower().replace("-", " ")
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+]+", " ", value)).strip()


db = sqlite3.connect(DATABASE)
try:
    db.execute("DROP TABLE IF EXISTS developer_time_equivalents")
    db.execute(
        """CREATE TABLE developer_time_equivalents(
               selected_developer_norm TEXT NOT NULL,
               selected_developer TEXT NOT NULL,
               selected_dilution_norm TEXT NOT NULL,
               selected_dilution TEXT NOT NULL,
               source_developer_norm TEXT NOT NULL,
               source_developer TEXT NOT NULL,
               source_dilution_norm TEXT NOT NULL,
               source_dilution TEXT NOT NULL,
               evidence_kind TEXT NOT NULL,
               PRIMARY KEY(selected_developer_norm, selected_dilution_norm)
           )"""
    )
    for selected, selected_dilution, source, source_dilution in rules:
        if db.execute(
            "SELECT COUNT(*) FROM maco_developer_scope WHERE developer_norm=?",
            (norm(selected),),
        ).fetchone()[0] != 1:
            raise SystemExit(f"equivalent target is not in Maco scope: {selected}")
        if db.execute(
            "SELECT COUNT(*) FROM developers WHERE norm_name=?", (norm(source),)
        ).fetchone()[0] != 1:
            raise SystemExit(f"equivalent MDC source is missing: {source}")
        db.execute(
            """INSERT INTO developer_time_equivalents VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                norm(selected),
                selected,
                norm(selected_dilution),
                selected_dilution,
                norm(source),
                source,
                norm(source_dilution),
                source_dilution,
                "AUDITED_DIRECT_ONE_HOP",
            ),
        )
    db.commit()
    if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise SystemExit("v0.5.8 database integrity check failed")
finally:
    db.close()


store = STORE.read_text(encoding="utf-8")
store = replace_once(
    store,
    '    private static final String DB_NAME = "mdc_offline_darkroom_v057.sqlite";',
    '    private static final String DB_NAME = "mdc_offline_darkroom_v058.sqlite";',
    "fresh database filename",
)

# Offer exact dilutions first, then only the approved equivalent dilutions for
# which the bundled database contains at least one row for the selected film.
dilution_return = "        return values.toArray(new String[0]);\n    }\n\n    static int nominalIsoForFilm"
dilution_fallback = '''        String selectedCanonical = FullCatalogStore.canonicalDeveloper(developer);
        String selectedNorm = norm(selectedCanonical == null ? developer : selectedCanonical);
        try (Cursor c = db.rawQuery(
                "SELECT e.selected_dilution FROM developer_time_equivalents e " +
                        "WHERE e.selected_developer_norm=? AND EXISTS(" +
                        "SELECT 1 FROM times t WHERE t.film_norm=? " +
                        "AND t.developer_norm=e.source_developer_norm " +
                        "AND t.dilution_norm=e.source_dilution_norm) " +
                        "ORDER BY e.selected_dilution",
                new String[]{selectedNorm, norm(wantedFilm)})) {
            while (c.moveToNext()) values.add(c.getString(0));
        }
        return values.toArray(new String[0]);
    }

    static int nominalIsoForFilm'''
store = replace_once(
    store, dilution_return, dilution_fallback, "combination dilution fallback"
)

lookup_signature = '''    static DevTimeEngine.Result lookup(String filmName, String format, String developer,
                                       String dilution, int iso, double targetTemp) {'''
exact_signature = '''    private static DevTimeEngine.Result lookupExact(String filmName, String format, String developer,
                                                    String dilution, int iso, double targetTemp) {'''
store = replace_once(store, lookup_signature, exact_signature, "exact lookup extraction")

wrapper = r'''    private static final class EquivalentRule {
        String selectedDeveloper;
        String selectedDilution;
        String sourceDeveloper;
        String sourceDilution;
    }

    private static EquivalentRule directEquivalent(String developer, String dilution) {
        String canonical = FullCatalogStore.canonicalDeveloper(developer);
        String developerNorm = norm(canonical == null ? developer : canonical);
        String dilutionNorm = normDilution(dilution);
        SQLiteDatabase db = helper.getReadableDatabase();
        EquivalentRule result = null;
        int matches = 0;
        try (Cursor c = db.rawQuery(
                "SELECT selected_developer,selected_dilution,source_developer,source_dilution " +
                        "FROM developer_time_equivalents " +
                        "WHERE selected_developer_norm=? AND selected_dilution_norm=?",
                new String[]{developerNorm, dilutionNorm})) {
            while (c.moveToNext()) {
                matches++;
                EquivalentRule row = new EquivalentRule();
                row.selectedDeveloper = c.getString(0);
                row.selectedDilution = c.getString(1);
                row.sourceDeveloper = c.getString(2);
                row.sourceDilution = c.getString(3);
                result = row;
            }
        }
        // Ambiguity is a hard stop. There is deliberately no fuzzy or chained lookup.
        return matches == 1 ? result : null;
    }

    static DevTimeEngine.Result lookup(String filmName, String format, String developer,
                                       String dilution, int iso, double targetTemp) {
        DevTimeEngine.Result exact = lookupExact(
                filmName, format, developer, dilution, iso, targetTemp);
        if (exact != null) return exact;

        EquivalentRule rule = directEquivalent(developer, dilution);
        if (rule == null) return null;
        DevTimeEngine.Result equivalent = lookupExact(
                filmName, format, rule.sourceDeveloper, rule.sourceDilution, iso, targetTemp);
        if (equivalent == null) return null;

        String notice = "Tempo ricavato da rivelatore equivalente approvato: " +
                rule.sourceDeveloper + " " + rule.sourceDilution + ".";
        String warning = appendWarning(equivalent.warning, notice);
        return new DevTimeEngine.Result(
                equivalent.found,
                equivalent.finalLowSeconds, equivalent.finalHighSeconds,
                equivalent.baseLowSeconds, equivalent.baseHighSeconds,
                equivalent.baseTemperature, equivalent.targetTemperature,
                equivalent.sourceName + " · equivalenza offline controllata",
                equivalent.sourceUrl,
                equivalent.sourceFilm, equivalent.sourceDeveloper,
                equivalent.sourceDilution, equivalent.sourceIso,
                equivalent.format, equivalent.temperatureConverted,
                equivalent.joboAdjusted, warning,
                "EQUIVALENTE_APPROVATO|" + rule.selectedDeveloper + "|" +
                        rule.selectedDilution + "|" + rule.sourceDeveloper + "|" +
                        rule.sourceDilution);
    }

'''
store = replace_once(
    store, exact_signature, wrapper + exact_signature, "one-hop lookup wrapper"
)
STORE.write_text(store, encoding="utf-8")


activity = ACTIVITY.read_text(encoding="utf-8")
summary_time = '''        addUnifiedChemicalField(summary, "TEMPO JOBO CPE2",
                result != null && result.found ? result.finalDisplay() : "Tempo non disponibile");'''
summary_equivalent = '''        addUnifiedChemicalField(summary, "TEMPO JOBO CPE2",
                result != null && result.found ? result.finalDisplay() : "Tempo non disponibile");
        if (result != null && result.found && result.diagnostic != null &&
                result.diagnostic.startsWith("EQUIVALENTE_APPROVATO|")) {
            addUnifiedChemicalField(summary, "EQUIVALENZA CONTROLLATA",
                    dev.name + " " + dilution + " → " + result.sourceDeveloper + " " +
                            result.sourceDilution +
                            "\\nUsata solo perché la corrispondenza esatta non è presente nel database offline.");
        }'''
activity = replace_once(
    activity, summary_time, summary_equivalent, "visible equivalent disclosure"
)
ACTIVITY.write_text(activity, encoding="utf-8")


for expected in (
    'DB_NAME = "mdc_offline_darkroom_v058.sqlite"',
    "developer_time_equivalents",
    "lookupExact",
    "directEquivalent",
    "EQUIVALENTE_APPROVATO|",
    "if (exact != null) return exact;",
):
    if expected not in STORE.read_text(encoding="utf-8"):
        raise SystemExit("v0.5.8 store guard failed: " + expected)
for expected in (
    "EQUIVALENZA CONTROLLATA",
    "EQUIVALENTE_APPROVATO|",
    "Usata solo perché la corrispondenza esatta non è presente",
):
    if expected not in ACTIVITY.read_text(encoding="utf-8"):
        raise SystemExit("v0.5.8 UI guard failed: " + expected)

print(f"Darkroom v0.5.8: installed {len(rules)} audited one-hop equivalence rules")
