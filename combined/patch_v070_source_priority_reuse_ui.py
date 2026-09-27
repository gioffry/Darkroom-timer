#!/usr/bin/env python3
"""Darkroom 0.7.0: manufacturer-first timing + compact reuse UI."""

from pathlib import Path
import re
import sqlite3

MDC = Path("combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java")
DEV = Path("combined/src/main/java/it/darkroom/assistant/DevTimeEngine.java")
ACT = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")
DB = Path("combined/src/main/assets/mdc_full.sqlite")

mdc = MDC.read_text(encoding="utf-8")
dev = DEV.read_text(encoding="utf-8")
act = ACT.read_text(encoding="utf-8")

if "SOURCE_PRIORITY_REUSE_UI_070" in act:
    print("source_priority_reuse_ui_070=ALREADY_APPLIED")
    raise SystemExit(0)

# ---------------------------------------------------------------------------
# 1. Restore the established JOBO CPE2 rule: continuous rotation = -15%.
#    No prewash is introduced or required by the app.
# ---------------------------------------------------------------------------
old = '''    // FOMA_TIMES_069 — no universal rotary correction is applied automatically.
    private static final double JOBO_FACTOR = 1.0;'''
new = '''    // SOURCE_PRIORITY_REUSE_UI_070 — established CPE2 workflow: continuous rotation, -15%.
    private static final double JOBO_FACTOR = 0.85;'''
if old not in mdc:
    raise SystemExit("v0.7.0 MDC JOBO marker missing")
mdc = mdc.replace(old, new, 1)

old = '''    // FOMA_TIMES_069 — keep source time; rotary calibration is combination-specific.
    private static final double JOBO_FACTOR = 1.0;'''
new = '''    // SOURCE_PRIORITY_REUSE_UI_070 — established CPE2 workflow: continuous rotation, -15%.
    private static final double JOBO_FACTOR = 0.85;'''
if old not in dev:
    raise SystemExit("v0.7.0 DevTimeEngine JOBO marker missing")
dev = dev.replace(old, new, 1)

# Manufacturer rows always outrank Massive Dev Chart rows for the same exact
# film + developer + dilution + ISO. Only when there is no manufacturer row
# does the exact MDC row become the source. Equivalence remains the third tier.
sort_old = '''        Collections.sort(candidates, (a, b) -> {
            int byTemperature = Double.compare('''
sort_new = '''        Collections.sort(candidates, (a, b) -> {
            boolean aManufacturer = SourceBroker.isManufacturerUrl(a.sourceUrl);
            boolean bManufacturer = SourceBroker.isManufacturerUrl(b.sourceUrl);
            if (aManufacturer != bManufacturer) return aManufacturer ? -1 : 1;
            int byTemperature = Double.compare('''
if sort_old not in mdc:
    raise SystemExit("v0.7.0 candidate sort marker missing")
mdc = mdc.replace(sort_old, sort_new, 1)

# Generalise the direct-source label: not only FOMA, any official manufacturer
# row inserted in the local timing database receives first priority.
source_old = '''            boolean directFoma = row.sourceUrl != null && row.sourceUrl.contains("foma.cz/");
            String sourceName = directFoma
                    ? "FOMA BOHEMIA · tabella ufficiale"
                    : SOURCE_NAME;
            String diagnostic = directFoma
                    ? "Dato diretto FOMA per pellicola, rivelatore, diluizione, ISO e temperatura selezionati."
                    : "Dato letto dal database offline sincronizzato da Digitaltruth; nessuna ricerca web durante il calcolo.";
            return new DevTimeEngine.Result(true, low, high, baseLow, baseHigh,
                    row.temp, targetTemp, sourceName, row.sourceUrl,
                    row.film, row.developer, row.dilution, row.iso,
                    format == null ? "35" : format, tempConverted, false, warning,
                    diagnostic);'''
source_new = '''            boolean directManufacturer = SourceBroker.isManufacturerUrl(row.sourceUrl);
            String sourceName = directManufacturer
                    ? "Produttore · dato ufficiale"
                    : SOURCE_NAME;
            String diagnostic = directManufacturer
                    ? "Dato diretto del produttore del rivelatore per pellicola, diluizione, ISO e temperatura selezionati."
                    : "Dato letto dal database offline sincronizzato da Digitaltruth; nessuna ricerca web durante il calcolo.";
            return new DevTimeEngine.Result(true, low, high, baseLow, baseHigh,
                    row.temp, targetTemp, sourceName, row.sourceUrl,
                    row.film, row.developer, row.dilution, row.iso,
                    format == null ? "35" : format, tempConverted, true, warning,
                    diagnostic);'''
if source_old not in mdc:
    raise SystemExit("v0.7.0 manufacturer source block missing")
mdc = mdc.replace(source_old, source_new, 1)

# The generic local engine must also report the restored JOBO adjustment.
dev = dev.replace(
    '''row.film, row.developer, row.dilution, row.iso, format,
                 tempConverted, false, warning, diagnostic);''',
    '''row.film, row.developer, row.dilution, row.iso, format,
                 tempConverted, true, warning, diagnostic);''',
    1,
)

# Restore the operational heading and explanation in the UI.
if 'addFilmTimeField(summary, "TEMPO CPE2 DI PARTENZA · " + dilution,' not in act:
    raise SystemExit("v0.7.0 time heading marker missing")
act = act.replace(
    'addFilmTimeField(summary, "TEMPO CPE2 DI PARTENZA · " + dilution,',
    'addFilmTimeField(summary, "TEMPO JOBO CPE2 · " + dilution,',
    1,
)
act = act.replace(
    'resultLine(filmResultBox, "TEMPO CPE2 DI PARTENZA", result.finalDisplay());',
    'resultLine(filmResultBox, "TEMPO JOBO CPE2", result.finalDisplay());',
    1,
)
act = act.replace(
    'resultLine(filmResultBox, "TEMPO CPE2 DI PARTENZA", "Tempo non disponibile");',
    'resultLine(filmResultBox, "TEMPO JOBO CPE2", "Tempo non disponibile");',
    1,
)
old_note = '''            conversion += "\\nJOBO CPE2: rotazione continua; nessuna riduzione percentuale universale applicata. Il tempo fonte è usato come punto di partenza." ;'''
new_note = '''            conversion += "\\nJOBO CPE2: rotazione continua, adattamento −15% sul tempo della fonte selezionata.";'''
if old_note not in act:
    raise SystemExit("v0.7.0 JOBO UI note marker missing")
act = act.replace(old_note, new_note, 1)

# ---------------------------------------------------------------------------
# 2. Reuse UI: the blue header is status only; the black bordered cards show
#    name, chosen dilution and exactly the useful operational note.
# ---------------------------------------------------------------------------

summary_pattern = re.compile(r'''    private String filmReuseCompactSummary\(Product dev, Product stop, Product fix,
                                           double volumeMl, String dilution\) \{
.*?    \}

    private void renderFilmCapacityForFormat''', re.S)
summary_replacement = '''    private String filmReuseCompactSummary(Product dev, Product stop, Product fix,
                                           double volumeMl, String dilution) {
        return "Rivelatore: " + reuseLabel(effectiveFilmReuseMode(dev, dilution)) +
                "\\nArresto: " + reuseLabel(effectiveAuxReuseMode(stop)) +
                "\\nFissaggio: " + reuseLabel(effectiveAuxReuseMode(fix));
    }

    private int effectiveAuxReuseMode(Product p) {
        if (p == null) return ChemistrySpecEngine.REUSE_ONE_SHOT;
        return p.reuseMode == ChemistrySpecEngine.REUSE_REUSABLE
                ? ChemistrySpecEngine.REUSE_REUSABLE
                : ChemistrySpecEngine.REUSE_ONE_SHOT;
    }

    private int effectiveFilmReuseMode(Product p, String dilution) {
        if (p == null) return ChemistrySpecEngine.REUSE_ONE_SHOT;
        String d = normalizeFilmDilution(dilution);
        String n = p.name == null ? "" : p.name.toLowerCase(Locale.ROOT);

        // Dilution-specific rules supported by manufacturer documentation.
        if (n.equals("fomadon excel"))
            return "stock".equals(d) ? ChemistrySpecEngine.REUSE_REUSABLE
                    : ChemistrySpecEngine.REUSE_ONE_SHOT;
        if (n.contains("id-11") || n.contains("id11") ||
                n.contains("microphen") || n.contains("perceptol"))
            return "stock".equals(d) ? ChemistrySpecEngine.REUSE_REUSABLE
                    : ChemistrySpecEngine.REUSE_ONE_SHOT;
        if (n.contains("xtol") || n.contains("x-tol") ||
                n.contains("d-76") || n.contains("d76"))
            return "stock".equals(d) ? ChemistrySpecEngine.REUSE_REUSABLE
                    : ChemistrySpecEngine.REUSE_ONE_SHOT;

        // Prefer the verified developer profile already stored in the local DB.
        SQLiteDatabase db = MdcOfflineStore.database();
        String canonical = FullCatalogStore.canonicalDeveloper(p.name);
        if (db != null && canonical != null) {
            try (Cursor c = db.rawQuery(
                    "SELECT pr.reuse_mode FROM developer_profiles pr " +
                            "JOIN developers d ON d.norm_name=pr.developer_norm " +
                            "WHERE d.name=? COLLATE NOCASE LIMIT 1",
                    new String[]{canonical})) {
                if (c.moveToFirst()) {
                    String mode = c.getString(0);
                    if (mode != null) {
                        String m = mode.toLowerCase(Locale.ROOT);
                        if (m.contains("one_shot") || m.contains("one-shot"))
                            return ChemistrySpecEngine.REUSE_ONE_SHOT;
                        if (m.contains("reusable"))
                            return ChemistrySpecEngine.REUSE_REUSABLE;
                    }
                }
            } catch (Exception ignored) {}
        }

        if (p.reuseMode == ChemistrySpecEngine.REUSE_REUSABLE)
            return ChemistrySpecEngine.REUSE_REUSABLE;
        return ChemistrySpecEngine.REUSE_ONE_SHOT; // conservative if undocumented
    }

    private String reuseLabel(int mode) {
        return mode == ChemistrySpecEngine.REUSE_REUSABLE
                ? "riutilizzabile" : "monouso";
    }

    private void renderFilmCapacityForFormat'''
act, n = summary_pattern.subn(summary_replacement, act, count=1)
if n != 1:
    raise SystemExit("v0.7.0 compact reuse summary replacement failed")

render_pattern = re.compile(r'''    private void renderFilmCapacityForFormat\(Product dev, Product stop, Product fix,
                                             double volumeMl, String format, String developerDilution\) \{
.*?    \}

    private void renderFilmCapacity\(Product dev, Product stop, Product fix,
                                    double volumeMl, String developerDilution\) \{
.*?    \}
''', re.S)
render_replacement = '''    private void renderFilmCapacityForFormat(Product dev, Product stop, Product fix,
                                             double volumeMl, String format, String developerDilution) {
        renderFilmCapacity(dev, stop, fix, volumeMl, developerDilution);
    }

    private void renderFilmCapacity(Product dev, Product stop, Product fix,
                                    double volumeMl, String developerDilution) {
        if (filmCapacityBox == null) return;
        filmCapacityBox.removeAllViews();
        resultLine(filmCapacityBox, "RIVELATORE",
                bathReuseDetail(dev, developerDilution, volumeMl, true));
        resultLine(filmCapacityBox, "ARRESTO",
                bathReuseDetail(stop, filmAuxDilution(stop), volumeMl, false));
        resultLine(filmCapacityBox, "FISSAGGIO",
                bathReuseDetail(fix, filmAuxDilution(fix), volumeMl, false));
    }

    private String bathReuseDetail(Product p, String dilution, double volumeMl, boolean developer) {
        if (p == null) return "—";
        String d = dilution == null || dilution.trim().isEmpty() ? "—" : dilution.trim();
        int mode = developer ? effectiveFilmReuseMode(p, dilution) : effectiveAuxReuseMode(p);
        StringBuilder out = new StringBuilder();
        out.append(p.name).append("\\nDiluizione: ").append(d);
        if (mode == ChemistrySpecEngine.REUSE_ONE_SHOT) {
            out.append("\\nMonouso: scartare dopo l'uso.");
            return out.toString();
        }

        if (!developer) {
            String indicator = auxiliaryIndicatorNote(p);
            if (!indicator.isEmpty()) {
                out.append("\\n").append(indicator);
                return out.toString();
            }
        }

        out.append("\\n").append(filmCapacityStatus(p, volumeMl, dilution));
        return out.toString();
    }

    private String auxiliaryIndicatorNote(Product p) {
        if (p == null) return "";
        SQLiteDatabase db = MdcOfflineStore.database();
        if (db == null) return "";
        try (Cursor c = db.rawQuery(
                "SELECT notes_it FROM auxiliary_chemical_profiles " +
                        "WHERE name=? COLLATE NOCASE LIMIT 1",
                new String[]{p.name})) {
            if (!c.moveToFirst()) return "";
            String notes = c.getString(0);
            if (notes == null || notes.trim().isEmpty()) return "";
            String lower = notes.toLowerCase(Locale.ROOT);
            if (!(lower.contains("indicatore") || lower.contains("viraggio") ||
                    lower.contains("cambia dal") || lower.contains("cambia colore")))
                return "";
            if (lower.contains("giallo") &&
                    (lower.contains("verde/blu") || lower.contains("verde") && lower.contains("blu")))
                return "Viraggio: giallo → verde/blu = bagno esaurito.";
            return "Viraggio/indicatore: " + notes.trim();
        } catch (Exception ignored) {
            return "";
        }
    }
'''
act, n = render_pattern.subn(render_replacement, act, count=1)
if n != 1:
    raise SystemExit("v0.7.0 reuse cards replacement failed")

# Generalise dilution-specific bath keys and concise counter text.
capacity_pattern = re.compile(r'''    private boolean isFomadonExcel\(Product p\) \{
.*?    private String paperCapacityStatus''', re.S)
capacity_replacement = '''    private boolean isFomadonExcel(Product p) {
        return p != null && "Fomadon Excel".equalsIgnoreCase(p.name);
    }

    private String normalizeFilmDilution(String dilution) {
        if (dilution == null) return "";
        String d = dilution.trim().toLowerCase(Locale.ROOT)
                .replace(" ", "").replace(":", "+");
        if ("1+0".equals(d) || "undiluted".equals(d) || "fullstrength".equals(d))
            return "stock";
        return d;
    }

    private String filmBathKey(Product p, String dilution) {
        String base = key(p.name);
        String d = normalizeFilmDilution(dilution);
        if (d.isEmpty()) return base;
        if (isFomadonExcel(p) && "1+1".equals(d)) return base + "_1plus1";
        return base + "_" + key(d);
    }

    private float filmUsedUnits(Product p, double volumeMl, String dilution) {
        String k = filmBathKey(p, dilution);
        boolean currentExists = prefs.contains("film_used_units_v2_" + k) ||
                prefs.contains("film_used_" + k) || prefs.contains("film_bath_volume_" + k);
        String readKey = k;
        if (!currentExists && dilution != null && !dilution.trim().isEmpty()) {
            String legacy = key(p.name);
            if (prefs.contains("film_used_units_v2_" + legacy) ||
                    prefs.contains("film_used_" + legacy) ||
                    prefs.contains("film_bath_volume_" + legacy)) readKey = legacy;
        }
        float storedVol = prefs.getFloat("film_bath_volume_" + readKey, 0f);
        float used = prefs.contains("film_used_units_v2_" + readKey)
                ? prefs.getFloat("film_used_units_v2_" + readKey, 0f)
                : prefs.getInt("film_used_" + readKey, 0);
        if (storedVol > 0 && Math.abs(storedVol - volumeMl) > 1) return 0f;
        return used;
    }

    private double effectiveFilmCapacityPerLiter(Product p, String dilution) {
        if (p == null) return -1;
        String d = normalizeFilmDilution(dilution);
        if (isFomadonExcel(p) && "stock".equals(d)) return 12.0;
        return p.filmCapacityPerLiter;
    }

    private String filmCapacityStatus(Product p, double volumeMl, String dilution) {
        if (p == null) return "—";
        int mode = (p.roles & ROLE_FILM_DEV) != 0
                ? effectiveFilmReuseMode(p, dilution)
                : effectiveAuxReuseMode(p);
        if (mode == ChemistrySpecEngine.REUSE_ONE_SHOT)
            return "Monouso: scartare dopo l'uso.";

        float used = filmUsedUnits(p, volumeMl, dilution);
        double perLiter = effectiveFilmCapacityPerLiter(p, dilution);
        if (perLiter <= 0)
            return "Contatore: " + fmt(used) + " utilizzi registrati.";

        double capacity = perLiter * volumeMl / 1000.0;
        double remaining = Math.max(0, capacity - used);
        return "Contatore: usati " + fmt(used) +
                " · residui " + fmt(remaining) +
                " · capacità " + fmt(capacity) + ".";
    }

    private String paperCapacityStatus'''
act, n = capacity_pattern.subn(capacity_replacement, act, count=1)
if n != 1:
    raise SystemExit("v0.7.0 capacity methods replacement failed")

# Generalise register/reset to all dilution-specific baths while retaining a
# migration path from the legacy product-only counter.
register_pattern = re.compile(r'''    private void registerFilmUse\(Product p, double volumeMl, double units\) \{
.*?    private void registerPaperUse''', re.S)
register_replacement = '''    private void registerFilmUse(Product p, double volumeMl, double units) {
        registerFilmUse(p, volumeMl, units, null);
    }

    private void registerFilmUse(Product p, double volumeMl, double units, String dilution) {
        if (p == null) return;
        int mode = (p.roles & ROLE_FILM_DEV) != 0
                ? effectiveFilmReuseMode(p, dilution)
                : effectiveAuxReuseMode(p);
        if (mode == ChemistrySpecEngine.REUSE_ONE_SHOT) return;
        String k = filmBathKey(p, dilution);
        float used = filmUsedUnits(p, volumeMl, dilution);
        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putFloat("film_used_units_v2_" + k, used + (float) units).apply();
    }

    private void resetFilmBath(Product p, double volumeMl) {
        resetFilmBath(p, volumeMl, null);
    }

    private void resetFilmBath(Product p, double volumeMl, String dilution) {
        if (p == null) return;
        String k = filmBathKey(p, dilution);
        SharedPreferences.Editor e = prefs.edit()
                .putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putInt("film_used_" + k, 0)
                .putFloat("film_used_units_v2_" + k, 0f);
        String legacy = key(p.name);
        if (!legacy.equals(k)) {
            e.remove("film_used_" + legacy)
                    .remove("film_used_units_v2_" + legacy)
                    .remove("film_bath_volume_" + legacy);
        }
        e.apply();
    }

    private void registerPaperUse'''
act, n = register_pattern.subn(register_replacement, act, count=1)
if n != 1:
    raise SystemExit("v0.7.0 register/reset replacement failed")

# Register/reset stop and fixer with the actual selected film dilution too.
act = act.replace(
    'registerFilmUse(stop, workingVolumeMl, units);',
    'registerFilmUse(stop, workingVolumeMl, units, filmAuxDilution(stop));',
    1,
)
act = act.replace(
    'registerFilmUse(fix, workingVolumeMl, units);',
    'registerFilmUse(fix, workingVolumeMl, units, filmAuxDilution(fix));',
    1,
)
act = act.replace(
    'resetFilmBath(stop, workingVolumeMl);',
    'resetFilmBath(stop, workingVolumeMl, filmAuxDilution(stop));',
    1,
)
act = act.replace(
    'resetFilmBath(fix, workingVolumeMl);',
    'resetFilmBath(fix, workingVolumeMl, filmAuxDilution(fix));',
    1,
)

# Marker.
class_marker = "public class AssistantActivityV2 extends Activity {\n"
if class_marker not in act:
    raise SystemExit("v0.7.0 Assistant class marker missing")
act = act.replace(
    class_marker,
    class_marker + "    // SOURCE_PRIORITY_REUSE_UI_070\n",
    1,
)

MDC.write_text(mdc, encoding="utf-8")
DEV.write_text(dev, encoding="utf-8")
ACT.write_text(act, encoding="utf-8")

# ---------------------------------------------------------------------------
# 3. Add audited manufacturer rows. They coexist with MDC rows; Java sorting
#    guarantees producer data wins for an exact combination.
# ---------------------------------------------------------------------------
FOMA_FOREIGN = "https://www.foma.cz/ew/33a06207-643b-4282-94ff-2c1953493fcd-en"
FOMA_FILM = "https://www.foma.cz/en/film"

con = sqlite3.connect(DB)
try:
    cur = con.cursor()

    def add_row(film_norm, developer_norm, dilution, iso, time_value, source_url, source_title):
        film = cur.execute("SELECT name FROM films WHERE norm_name=?", (film_norm,)).fetchone()
        devrow = cur.execute("SELECT name FROM developers WHERE norm_name=?", (developer_norm,)).fetchone()
        if film is None or devrow is None:
            return False
        dilution_norm = dilution.lower().replace(":", "+").replace(" ", "")
        cur.execute(
            """DELETE FROM times
               WHERE film_norm=? AND developer_norm=? AND dilution_norm=? AND iso=?
                 AND source_url=?""",
            (film_norm, developer_norm, dilution_norm, iso, source_url),
        )
        cur.execute(
            """INSERT INTO times(
                 film,film_norm,developer,developer_norm,dilution,dilution_norm,iso,
                 time35,time120,timesheet,temp,notes,source_url
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                film[0], film_norm, devrow[0], developer_norm, dilution, dilution_norm, iso,
                time_value, time_value, time_value, 20.0,
                source_title + " · tempo ufficiale produttore.", source_url,
            ),
        )
        return True

    # FOMA 09/16: foreign films in FOMA developers.
    foreign = [
        # film, ISO, developer, dilution, time
        ("ilford pan f+", 50, "fomadon r09", "1+50", "11-12"),
        ("ilford pan f+", 50, "fomadon p", "stock", "9"),
        ("ilford pan f+", 50, "fomadon p", "1+1", "12"),
        ("ilford pan f+", 50, "fomadon excel", "stock", "7.5"),
        ("ilford pan f+", 50, "fomadon excel", "1+1", "8.5"),

        ("ilford fp4+", 125, "fomadon lqn", "1+10", "9"),
        ("ilford fp4+", 125, "fomadon r09", "1+50", "18"),
        ("ilford fp4+", 125, "fomadon p", "stock", "10"),
        ("ilford fp4+", 125, "fomadon p", "1+1", "13"),
        ("ilford fp4+", 125, "fomadon excel", "stock", "10"),
        ("ilford fp4+", 125, "fomadon excel", "1+1", "14"),

        ("ilford hp5+", 400, "fomadon lqn", "1+10", "9-10"),
        ("ilford hp5+", 400, "fomadon r09", "1+25", "8"),
        ("ilford hp5+", 400, "fomadon p", "stock", "12"),
        ("ilford hp5+", 400, "fomadon p", "1+1", "16"),
        ("ilford hp5+", 400, "fomadon excel", "stock", "8-9"),
        ("ilford hp5+", 400, "fomadon excel", "1+1", "12-13"),

        ("ilford delta 100 pro", 100, "fomadon r09", "1+50", "15-16"),
        ("ilford delta 100 pro", 100, "fomadon p", "stock", "9.5"),
        ("ilford delta 100 pro", 100, "fomadon p", "1+1", "12.5"),
        ("ilford delta 100 pro", 100, "fomadon excel", "stock", "8"),
        ("ilford delta 100 pro", 100, "fomadon excel", "1+1", "10.5-11"),

        ("ilford delta 400 pro", 400, "fomadon r09", "1+50", "18"),
        ("ilford delta 400 pro", 400, "fomadon p", "stock", "10"),
        ("ilford delta 400 pro", 400, "fomadon p", "1+1", "14.5"),
        ("ilford delta 400 pro", 400, "fomadon excel", "stock", "7"),
        ("ilford delta 400 pro", 400, "fomadon excel", "1+1", "9.5-10"),

        ("ilford delta 3200 pro", 3200, "fomadon r09", "1+25", "11-12"),
        ("ilford delta 3200 pro", 3200, "fomadon p", "stock", "18-20"),
        ("ilford delta 3200 pro", 3200, "fomadon excel", "stock", "8-9"),

        ("ilford sfx 200", 200, "fomadon lqn", "1+10", "9"),
        ("ilford sfx 200", 200, "fomadon r09", "1+50", "15-16"),
        ("ilford sfx 200", 200, "fomadon excel", "stock", "9-10"),

        ("kodak tmax 100", 100, "fomadon lqn", "1+10", "11-12"),
        ("kodak tmax 100", 100, "fomadon r09", "1+50", "15-16"),
        ("kodak tmax 100", 100, "fomadon p", "stock", "12-13"),
        ("kodak tmax 100", 100, "fomadon p", "1+1", "18-19"),
        ("kodak tmax 100", 100, "fomadon excel", "stock", "7-7.5"),
        ("kodak tmax 100", 100, "fomadon excel", "1+1", "9-10"),

        ("kodak tmax 400", 400, "fomadon lqn", "1+10", "12"),
        ("kodak tmax 400", 400, "fomadon r09", "1+50", "11-12"),
        ("kodak tmax 400", 400, "fomadon p", "stock", "11-12"),
        ("kodak tmax 400", 400, "fomadon p", "1+1", "19-20"),
        ("kodak tmax 400", 400, "fomadon excel", "stock", "6.5-7"),

        ("kodak tri x 400", 400, "fomadon r09", "1+50", "13-14"),
        ("kodak tri x 400", 400, "fomadon p", "stock", "11"),
        ("kodak tri x 400", 400, "fomadon p", "1+1", "14"),
        ("kodak tri x 400", 400, "fomadon excel", "stock", "7"),
        ("kodak tri x 400", 400, "fomadon excel", "1+1", "9"),

        ("kodak tmax p3200", 3200, "fomadon r09", "1+50", "16-17"),
        ("kodak tmax p3200", 3200, "fomadon p", "stock", "18-20"),
        ("kodak tmax p3200", 3200, "fomadon p", "1+1", "23-25"),
        ("kodak tmax p3200", 3200, "fomadon excel", "stock", "13-14"),
        ("kodak tmax p3200", 3200, "fomadon excel", "1+1", "18-19"),
    ]
    inserted_foreign = sum(
        1 for film, iso, developer, dilution, t in foreign
        if add_row(film, developer, dilution, iso, t, FOMA_FOREIGN,
                   "FOMA 09/16 · Developing times of some foreign films in FOMA developers")
    )

    # FOMA 04/23: FOMA films in FOMA developers.
    foma_films = [
        ("fomapan 100", 100, "fomadon lqn", "1+10", "7-8"),
        ("fomapan 100", 100, "fomadon lqr", "1+10", "5-6"),
        ("fomapan 100", 100, "foma universal", "1+3", "5"),
        ("fomapan 100", 100, "fomadon r09", "1+25", "4"),
        ("fomapan 100", 100, "fomadon r09", "1+50", "9"),
        ("fomapan 100", 100, "fomadon p", "stock", "7-8"),
        ("fomapan 100", 100, "fomadon excel", "stock", "5-6"),

        ("fomapan 200", 200, "fomadon lqn", "1+10", "5-6"),
        ("fomapan 200", 200, "fomadon lqr", "1+10", "5-6"),
        ("fomapan 200", 200, "foma universal", "1+3", "3.5"),
        ("fomapan 200", 200, "fomadon r09", "1+25", "5"),
        ("fomapan 200", 200, "fomadon r09", "1+50", "10"),
        ("fomapan 200", 200, "fomadon p", "stock", "5-6"),
        ("fomapan 200", 200, "fomadon excel", "stock", "6-7"),

        ("fomapan 400", 400, "fomadon lqn", "1+10", "9-10"),
        ("fomapan 400", 400, "fomadon lqr", "1+10", "7-8"),
        ("fomapan 400", 400, "foma universal", "1+3", "7.5"),
        ("fomapan 400", 400, "fomadon r09", "1+25", "6"),
        ("fomapan 400", 400, "fomadon r09", "1+50", "12"),
        ("fomapan 400", 400, "fomadon p", "stock", "10-11"),
        ("fomapan 400", 400, "fomadon excel", "stock", "7"),

        ("foma ortho 400", 400, "fomadon lqn", "1+10", "8.5-10"),
        ("foma ortho 400", 400, "fomadon lqr", "1+10", "7-8"),
        ("foma ortho 400", 400, "foma universal", "1+3", "7"),
        ("foma ortho 400", 400, "fomadon r09", "1+25", "5-6"),
        ("foma ortho 400", 400, "fomadon r09", "1+50", "10-12"),
        ("foma ortho 400", 400, "fomadon p", "stock", "9.5-10.5"),
        ("foma ortho 400", 400, "fomadon excel", "stock", "6-7"),
    ]
    inserted_foma = sum(
        1 for film, iso, developer, dilution, t in foma_films
        if add_row(film, developer, dilution, iso, t, FOMA_FILM,
                   "FOMA 04/23 · Developers for black-and-white negative films")
    )

    con.commit()

    # Regression anchors: producer times are the source values before JOBO -15%.
    fp4 = cur.execute(
        """SELECT dilution_norm,time120,source_url FROM times
           WHERE film_norm='ilford fp4+' AND developer_norm='fomadon excel'
             AND iso=125 AND source_url=?
           ORDER BY dilution_norm""",
        (FOMA_FOREIGN,),
    ).fetchall()
    expected_fp4 = [
        ("1+1", "14", FOMA_FOREIGN),
        ("stock", "10", FOMA_FOREIGN),
    ]
    if fp4 != expected_fp4:
        raise SystemExit("v0.7.0 FP4/Fomadon Excel manufacturer rows mismatch: " + repr(fp4))

    kentmere_direct = cur.execute(
        """SELECT COUNT(*) FROM times
           WHERE film_norm LIKE 'kentmere%' AND developer_norm='fomadon excel'
             AND source_url LIKE '%foma.cz%'"""
    ).fetchone()[0]
    if kentmere_direct != 0:
        raise SystemExit("v0.7.0 Kentmere must fall back to MDC: unexpected FOMA direct row")
finally:
    con.close()

# Final source guardrails.
for marker in [
    "SOURCE_PRIORITY_REUSE_UI_070",
    "JOBO_FACTOR = 0.85",
    "Produttore · dato ufficiale",
    "aManufacturer != bManufacturer",
]:
    if marker not in mdc and marker not in act:
        raise SystemExit("v0.7.0 guardrail missing: " + marker)

for marker in [
    'Rivelatore: " + reuseLabel',
    'Arresto: " + reuseLabel',
    'Fissaggio: " + reuseLabel',
    'Diluizione: "',
    "Viraggio: giallo → verde/blu = bagno esaurito.",
    'TEMPO JOBO CPE2 · " + dilution',
    "adattamento −15%",
]:
    if marker not in act:
        raise SystemExit("v0.7.0 UI guardrail missing: " + marker)

print("source_priority_reuse_ui_070=APPLIED")
print("timing_priority=MANUFACTURER_THEN_MDC_THEN_EQUIVALENCE")
print("jobo_cpe2_minus15=RESTORED")
print("prewash_added=NO")
print("foma_foreign_rows_added=" + str(inserted_foreign))
print("foma_film_rows_added=" + str(inserted_foma))
print("reuse_header=THREE_BINARY_STATUSES")
print("reuse_cards=NAME_DILUTION_OPERATIONAL_NOTE")
