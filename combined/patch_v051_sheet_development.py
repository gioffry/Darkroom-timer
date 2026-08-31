#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path("combined/src/main/java/it/darkroom/assistant")
STORE = ROOT / "MdcOfflineStore.java"
ACTIVITY = ROOT / "AssistantActivityV2.java"
ENGINE = ROOT / "DevTimeEngine.java"
CATALOG = ROOT / "FullCatalogStore.java"

for p in (STORE, ACTIVITY, ENGINE):
    if not p.exists():
        raise SystemExit("v0.5.1 generated assistant source missing: " + str(p))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"v0.5.1 {label}: expected one marker, found {n}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1) MDC database: expose Sheet as a real third format and use timesheet first.
# ---------------------------------------------------------------------------
store = STORE.read_text(encoding="utf-8")
formats_method = r'''    static String[] formatsForFilm(String filmName) {
        if (!isReady() || filmName == null) return new String[0];
        boolean has35 = false;
        boolean has120 = false;
        boolean hasSheet = false;
        SQLiteDatabase db = helper.getReadableDatabase();
        String wantedFilm = stripFormat(filmName);
        String canonicalFilm = FullCatalogStore.canonicalFilm(wantedFilm);
        if (canonicalFilm != null) wantedFilm = canonicalFilm;
        try (Cursor c = db.rawQuery(
                "SELECT time35,time120,timesheet FROM times WHERE film_norm=?",
                new String[]{norm(wantedFilm)})) {
            while (c.moveToNext()) {
                if (!has35 && hasTime(c.getString(0))) has35 = true;
                if (!has120 && hasTime(c.getString(1))) has120 = true;
                if (!hasSheet && hasTime(c.getString(2))) hasSheet = true;
                if (has35 && has120 && hasSheet) break;
            }
        }
        List<String> out = new ArrayList<>();
        if (has35) out.add("35");
        if (has120) out.add("120");
        if (hasSheet) out.add("4x5");
        return out.toArray(new String[0]);
    }

'''
store, n = re.subn(
    r'''    static String\[\] formatsForFilm\(String filmName\) \{.*?\n    \}\n\n(?=    static boolean isKnownDeveloper)''',
    lambda _m: formats_method,
    store,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("v0.5.1 formatsForFilm replacement failed")

lookup_block = r'''            boolean sheetFormat = "4x5".equalsIgnoreCase(format) || "sheet".equalsIgnoreCase(format);
            String raw = sheetFormat ? row.timeSheet : ("120".equals(format) ? row.time120 : row.time35);
            boolean crossFormat = false;
            if (!hasTime(raw)) {
                // A sheet must never silently inherit a roll-film time. If Digitaltruth has no
                // Sheet value, report no exact time for 4x5 instead of inventing a substitution.
                if (sheetFormat) continue;
                String alt = "120".equals(format) ? row.time35 : row.time120;
                if (!hasTime(alt)) alt = row.timeSheet;
                if (hasTime(alt)) { raw = alt; crossFormat = true; }
            }
            int[] range = parseTimeRange(raw);'''
store, n = re.subn(
    r'''            String raw = "120"\.equals\(format\) \? row\.time120 : row\.time35;\n            boolean crossFormat = false;\n            if \(!hasTime\(raw\)\) \{.*?\n            \}\n            int\[\] range = parseTimeRange\(raw\);''',
    lambda _m: lookup_block,
    store,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("v0.5.1 MDC lookup primary Sheet-time replacement failed")

# Strip an optional 4x5 suffix too, without disturbing canonical film matching.
store = store.replace(
    '(35\\s*mm|120)\\s*$',
    '(35\\s*mm|120|4\\s*[x×]\\s*5|sheet)\\s*$',
)
STORE.write_text(store, encoding="utf-8")


# ---------------------------------------------------------------------------
# 2) Backup DevTimeEngine: if this older engine is ever reached, Sheet is also
#    treated as its own column rather than as 35 mm.
# ---------------------------------------------------------------------------
engine = ENGINE.read_text(encoding="utf-8")
engine = replace_once(
    engine,
    '        String raw = "120".equals(format) ? row.time120 : row.time35;',
    '        String raw = "4x5".equalsIgnoreCase(format) ? row.timeSheet : ("120".equals(format) ? row.time120 : row.time35);',
    "DevTimeEngine build Sheet column",
)
engine = replace_once(
    engine,
    '            String time = "120".equals(format) ? r.time120 : r.time35;',
    '            String time = "4x5".equalsIgnoreCase(format) ? r.timeSheet : ("120".equals(format) ? r.time120 : r.time35);',
    "DevTimeEngine chooser Sheet column",
)
ENGINE.write_text(engine, encoding="utf-8")


# ---------------------------------------------------------------------------
# 3) Development UI: 35 mm + 120 + 4x5, dynamic roll/sheet count and JOBO 2520
#    sheet capacity with 2509N reel.
# ---------------------------------------------------------------------------
activity = ACTIVITY.read_text(encoding="utf-8")

activity = replace_once(
    activity,
    '    private Spinner rollsSpinner;\n    private Spinner tankSpinner;\n    private Spinner formatSpinner;',
    '    private Spinner rollsSpinner;\n    private TextView filmCountLabel;\n    private Spinner tankSpinner;\n    private Spinner formatSpinner;',
    "film count label field",
)

activity = replace_once(
    activity,
    '''    private final Tank[] tanks = new Tank[]{
            new Tank("JOBO 1510", 140, 1, 0),
            new Tank("JOBO 1520", 240, 2, 2),
            new Tank("JOBO 2520", 270, 2, 1),
            new Tank("JOBO 1540", 470, 4, 4),
            new Tank("JOBO 1520 + 1530", 570, 5, 5)
    };''',
    '''    private final Tank[] tanks = new Tank[]{
            new Tank("JOBO 1510", 140, 1, 0, 0),
            new Tank("JOBO 1520", 240, 2, 2, 0),
            // 4x5: la 2520 usa la spirale/loader 2509N, fino a 6 lastre in rotazione.
            new Tank("JOBO 2520", 270, 2, 1, 6),
            new Tank("JOBO 1540", 470, 4, 4, 0),
            new Tank("JOBO 1520 + 1530", 570, 5, 5, 0)
    };''',
    "tank sheet capacities",
)

activity = replace_once(
    activity,
    '''        rollsSpinner = spinner(new String[]{"1", "2", "3", "4", "5"});
        page.addView(fieldBlock("NUMERO RULLI", rollsSpinner));''',
    '''        rollsSpinner = spinner(new String[]{"1", "2", "3", "4", "5"});
        LinearLayout filmCountBlock = fieldBlock("NUMERO RULLI", rollsSpinner);
        filmCountLabel = (TextView) filmCountBlock.getChildAt(0);
        page.addView(filmCountBlock);''',
    "dynamic roll/sheet count block",
)

activity = replace_once(
    activity,
    '''                String label = String.valueOf(formatSpinner.getSelectedItem());
                String f = label.startsWith("120") ? "120" : label.startsWith("35") ? "35" : "";
                if (f.isEmpty()) return;
                selectedFilm = new FilmStock(selectedFilm.name, selectedFilm.nominalIso, f, selectedFilm.sourceUrl);
                updateCompatibleTanks();''',
    '''                String label = String.valueOf(formatSpinner.getSelectedItem());
                String f = label.startsWith("4") ? "4x5" : label.startsWith("120") ? "120" : label.startsWith("35") ? "35" : "";
                if (f.isEmpty()) return;
                selectedFilm = new FilmStock(selectedFilm.name, selectedFilm.nominalIso, f, selectedFilm.sourceUrl);
                updateFilmCountControls(f);
                updateCompatibleTanks();''',
    "format listener 4x5",
)

activity = replace_once(
    activity,
    '            labels.add("120".equals(x) ? "120" : "35 mm");',
    '            labels.add(formatDisplay(x));',
    "format label rendering",
)
activity = replace_once(
    activity,
    '''        String chosenFormat = formats[selected];
        selectedFilm = new FilmStock(f.name, f.nominalIso, chosenFormat, f.sourceUrl);
        updateCompatibleTanks();''',
    '''        String chosenFormat = formats[selected];
        selectedFilm = new FilmStock(f.name, f.nominalIso, chosenFormat, f.sourceUrl);
        updateFilmCountControls(chosenFormat);
        updateCompatibleTanks();''',
    "selected format count controls",
)

activity = replace_once(
    activity,
    '            int cap = "120".equals(selectedFilm.format) ? t.max120 : t.max35;',
    '            int cap = isSheetFormat(selectedFilm.format) ? t.maxSheet : ("120".equals(selectedFilm.format) ? t.max120 : t.max35);',
    "tank capacity by format",
)
activity = replace_once(
    activity,
    '            labels.add(t.name + " — " + t.rotaryMl + " ml");',
    '            labels.add(tankDisplayName(t, selectedFilm.format) + " — " + t.rotaryMl + " ml");',
    "sheet tank display name",
)

helpers = r'''    private boolean isSheetFormat(String format) {
        return format != null && ("4x5".equalsIgnoreCase(format) || "sheet".equalsIgnoreCase(format));
    }

    private String formatDisplay(String format) {
        if (isSheetFormat(format)) return "4×5 / lastre";
        if ("120".equals(format)) return "120";
        return "35 mm";
    }

    private void updateFilmCountControls(String format) {
        if (rollsSpinner == null) return;
        if (isSheetFormat(format)) {
            if (filmCountLabel != null) filmCountLabel.setText("NUMERO LASTRE 4×5");
            setSpinnerItems(rollsSpinner, new String[]{"1", "2", "3", "4", "5", "6"});
        } else {
            if (filmCountLabel != null) filmCountLabel.setText("NUMERO RULLI");
            setSpinnerItems(rollsSpinner, new String[]{"1", "2", "3", "4", "5"});
        }
        rollsSpinner.setSelection(0);
    }

    private String tankDisplayName(Tank tank, String format) {
        if (tank == null) return "—";
        if (isSheetFormat(format) && "JOBO 2520".equals(tank.name)) return "JOBO 2520 + 2509N";
        return tank.name;
    }

    private double filmCapacityUnits(int count, String format) {
        // Capacity sheets are converted only for chemistry-capacity bookkeeping:
        // four 4x5 sheets are about one 135-36/120 roll by emulsion area.
        return isSheetFormat(format) ? count / 4.0 : count;
    }

    private String developedUnitLabel(int count, String format) {
        if (isSheetFormat(format)) return count + (count == 1 ? " lastra 4×5" : " lastre 4×5");
        return count + (count == 1 ? " rullo" : " rulli");
    }

'''
marker = '    private Tank selectedTank() {'
if marker not in activity:
    raise SystemExit("v0.5.1 selectedTank marker missing")
activity = activity.replace(marker, helpers + marker, 1)

# Use the bundled/offline MDC database explicitly: no web lookup for development time.
activity, n = re.subn(
    r'''            DevTimeEngine\.Result result = DevTimeEngine\.lookup\(\n                    selectedFilm\.name, selectedFilm\.format, dev\.name, dilution,\n                    iso, temp, selectedFilm\.sourceUrl, dev\.sourceUrl\);''',
    '''            DevTimeEngine.Result result = MdcOfflineStore.lookup(\n                    selectedFilm.name, selectedFilm.format, dev.name, dilution, iso, temp);''',
    activity,
    count=1,
)
if n != 1:
    raise SystemExit("v0.5.1 calculation offline lookup replacement failed")

activity = activity.replace(
    '        } catch (Exception e) { toast("Controlla ISO, temperatura e rulli."); return; }',
    '        } catch (Exception e) { toast(isSheetFormat(selectedFilm.format) ? "Controlla ISO, temperatura e numero lastre." : "Controlla ISO, temperatura e rulli."); return; }',
    1,
)

activity = replace_once(
    activity,
    '''                            ("120".equals(result.format) ? "120" : "35 mm"));''',
    '''                            formatDisplay(result.format));''',
    "result original format label",
)
activity = replace_once(
    activity,
    '        resultLine(filmResultBox, "TANK", tank.name + " · volume rotazione " + tank.rotaryMl + " ml");',
    '        resultLine(filmResultBox, "TANK", tankDisplayName(tank, result.format) + " · volume rotazione " + tank.rotaryMl + " ml");',
    "result sheet tank label",
)

# Explain the capacity equivalence only for Sheet, and register chemistry use in
# roll-equivalent emulsion area instead of incorrectly counting each sheet as a roll.
activity = replace_once(
    activity,
    '''        filmResultBox.addView(filmCapacityBox);
        renderFilmCapacity(dev, stop, fix, tank.rotaryMl);

        Button register = actionButton("REGISTRA QUESTO SVILUPPO", BURGUNDY);
        register.setOnClickListener(v -> {
            registerFilmUse(dev, tank.rotaryMl, rolls);
            registerFilmUse(stop, tank.rotaryMl, rolls);
            registerFilmUse(fix, tank.rotaryMl, rolls);
            renderFilmCapacity(dev, stop, fix, tank.rotaryMl);
            toast(rolls + (rolls == 1 ? " rullo registrato." : " rulli registrati."));
        });''',
    '''        filmResultBox.addView(filmCapacityBox);
        if (isSheetFormat(result.format)) {
            resultLine(filmResultBox, "EQUIVALENZA CAPACITÀ",
                    "Per il solo contatore chimico: 4 lastre 4×5 ≈ 1 rullo 135-36 / 120 per superficie di emulsione.");
        }
        renderFilmCapacity(dev, stop, fix, tank.rotaryMl);

        Button register = actionButton("REGISTRA QUESTO SVILUPPO", BURGUNDY);
        register.setOnClickListener(v -> {
            double units = filmCapacityUnits(rolls, result.format);
            registerFilmUse(dev, tank.rotaryMl, units);
            registerFilmUse(stop, tank.rotaryMl, units);
            registerFilmUse(fix, tank.rotaryMl, units);
            renderFilmCapacity(dev, stop, fix, tank.rotaryMl);
            toast(developedUnitLabel(rolls, result.format) + " registrat" + (rolls == 1 ? "a." : "e."));
        });''',
    "sheet capacity registration",
)

# Capacity bookkeeping becomes fractional roll-equivalents so 4x5 is not overcounted.
capacity_method = r'''    private String filmCapacityStatus(Product p, double volumeMl) {
        if (p == null) return "—";
        if (p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT)
            return "Monouso: non riutilizzare questo bagno.";
        String k = key(p.name);
        float storedVol = prefs.getFloat("film_bath_volume_" + k, 0f);
        float used = prefs.contains("film_used_units_v2_" + k)
                ? prefs.getFloat("film_used_units_v2_" + k, 0f)
                : prefs.getInt("film_used_" + k, 0);
        if (storedVol > 0 && Math.abs(storedVol - volumeMl) > 1) used = 0;
        if (p.reuseMode != ChemistrySpecEngine.REUSE_REUSABLE)
            return "Riutilizzo non determinato. Equivalenti rullo registrati nel bagno: " + fmt(used) + ".";
        if (p.filmCapacityPerLiter <= 0)
            return "Riutilizzabile; capacità numerica non trovata. Equivalenti rullo registrati: " + fmt(used) + ".";
        double capacity = p.filmCapacityPerLiter * volumeMl / 1000.0;
        double remaining = Math.max(0, capacity - used);
        return "Bagno " + fmt(volumeMl) + " ml · capacità " + fmt(capacity) +
                " rulli equivalenti · usati " + fmt(used) + " · residui " + fmt(remaining) + ".";
    }

'''
activity, n = re.subn(
    r'''    private String filmCapacityStatus\(Product p, double volumeMl\) \{.*?\n    \}\n\n(?=    private String paperCapacityStatus)''',
    lambda _m: capacity_method,
    activity,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("v0.5.1 filmCapacityStatus replacement failed")

register_method = r'''    private void registerFilmUse(Product p, double volumeMl, double units) {
        if (p == null || p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT) return;
        String k = key(p.name);
        float oldVol = prefs.getFloat("film_bath_volume_" + k, 0f);
        float used = prefs.contains("film_used_units_v2_" + k)
                ? prefs.getFloat("film_used_units_v2_" + k, 0f)
                : prefs.getInt("film_used_" + k, 0);
        if (oldVol <= 0 || Math.abs(oldVol - volumeMl) > 1) used = 0;
        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putFloat("film_used_units_v2_" + k, used + (float) units).apply();
    }

'''
activity, n = re.subn(
    r'''    private void registerFilmUse\(Product p, double volumeMl, int rolls\) \{.*?\n    \}\n\n(?=    private void resetFilmBath)''',
    lambda _m: register_method,
    activity,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("v0.5.1 registerFilmUse replacement failed")

activity = replace_once(
    activity,
    '''        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putInt("film_used_" + k, 0).apply();''',
    '''        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putInt("film_used_" + k, 0)
                .putFloat("film_used_units_v2_" + k, 0f).apply();''',
    "film capacity reset v2",
)

# Product details: preserve old integer counters and show new fractional units when present.
activity = replace_once(
    activity,
    '''        int filmUsed = prefs.getInt("film_used_" + k, 0);
        float filmVol = prefs.getFloat("film_bath_volume_" + k, 0f);''',
    '''        float filmUsed = prefs.contains("film_used_units_v2_" + k)
                ? prefs.getFloat("film_used_units_v2_" + k, 0f)
                : prefs.getInt("film_used_" + k, 0);
        float filmVol = prefs.getFloat("film_bath_volume_" + k, 0f);''',
    "stored film capacity units",
)
activity = replace_once(
    activity,
    '''        if (filmVol > 0) msg.append("\nBagno pellicola: ").append(fmt(filmVol))
                .append(" ml · ").append(filmUsed).append(" rulli registrati.");''',
    '''        if (filmVol > 0) msg.append("\nBagno pellicola: ").append(fmt(filmVol))
                .append(" ml · ").append(fmt(filmUsed)).append(" rulli equivalenti registrati.");''',
    "stored capacity wording",
)

activity = activity.replace(
    '        return x.endsWith("35 mm") || x.endsWith("120");',
    '        return x.endsWith("35 mm") || x.endsWith("120") || x.endsWith("4×5") || x.endsWith("4x5") || x.endsWith("sheet");',
    1,
)

activity = replace_once(
    activity,
    '''        final int max35;
        final int max120;
        Tank(String name, int rotaryMl, int max35, int max120) {
            this.name = name;
            this.rotaryMl = rotaryMl;
            this.max35 = max35;
            this.max120 = max120;
        }''',
    '''        final int max35;
        final int max120;
        final int maxSheet;
        Tank(String name, int rotaryMl, int max35, int max120, int maxSheet) {
            this.name = name;
            this.rotaryMl = rotaryMl;
            this.max35 = max35;
            this.max120 = max120;
            this.maxSheet = maxSheet;
        }''',
    "Tank maxSheet field",
)

ACTIVITY.write_text(activity, encoding="utf-8")


# FullCatalogStore may canonicalize display names with a trailing format suffix.
if CATALOG.exists():
    catalog = CATALOG.read_text(encoding="utf-8")
    catalog = catalog.replace(
        '(35\\s*mm|120)\\s*$',
        '(35\\s*mm|120|4\\s*[x×]\\s*5|sheet)\\s*$',
    )
    CATALOG.write_text(catalog, encoding="utf-8")


# ---------------------------------------------------------------------------
# Source acceptance guards.
# ---------------------------------------------------------------------------
store = STORE.read_text(encoding="utf-8")
activity = ACTIVITY.read_text(encoding="utf-8")
engine = ENGINE.read_text(encoding="utf-8")

for marker in [
    'SELECT time35,time120,timesheet FROM times',
    'if (hasSheet) out.add("4x5")',
    'String raw = sheetFormat ? row.timeSheet',
    'if (sheetFormat) continue;',
]:
    if marker not in store:
        raise SystemExit("v0.5.1 MDC source guard failed: " + marker)

for marker in [
    'NUMERO LASTRE 4×5',
    '"4×5 / lastre"',
    'final int maxSheet;',
    'new Tank("JOBO 2520", 270, 2, 1, 6)',
    'JOBO 2520 + 2509N',
    'MdcOfflineStore.lookup(',
    'formatDisplay(result.format)',
    'filmCapacityUnits(rolls, result.format)',
    'film_used_units_v2_',
]:
    if marker not in activity:
        raise SystemExit("v0.5.1 activity source guard failed: " + marker)

for marker in [
    '"4x5".equalsIgnoreCase(format) ? row.timeSheet',
    '"4x5".equalsIgnoreCase(format) ? r.timeSheet',
]:
    if marker not in engine:
        raise SystemExit("v0.5.1 DevTimeEngine source guard failed: " + marker)

print("Darkroom v0.5.1 4x5 sheet-development patch ready")
