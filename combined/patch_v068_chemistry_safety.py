#!/usr/bin/env python3
"""Darkroom 0.6.8: chemistry safety for Fomadon Excel dilution/reuse."""

from pathlib import Path
import re

SOURCE = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")
source = SOURCE.read_text(encoding="utf-8")

if "CHEMISTRY_SAFETY_068" in source:
    print("chemistry_safety_068=ALREADY_APPLIED")
    raise SystemExit(0)

# Marker.
class_marker = "public class AssistantActivityV2 extends Activity {\n"
if class_marker not in source:
    raise SystemExit("v0.6.8 Assistant class marker missing")
source = source.replace(
    class_marker,
    class_marker + "    // CHEMISTRY_SAFETY_068 — developer dilution and reuse are never conflated.\n",
    1,
)

# The selected dilution must be visible beside the dominant JOBO time.
old = '''        addFilmTimeField(summary, "TEMPO JOBO CPE2",
                result != null && result.found ? result.finalDisplay() : "Tempo non disponibile");'''
new = '''        addFilmTimeField(summary, "TEMPO JOBO CPE2 · " + dilution,
                result != null && result.found ? result.finalDisplay() : "Tempo non disponibile");'''
if old not in source:
    raise SystemExit("v0.6.8 dominant time field marker missing")
source = source.replace(old, new, 1)

# For Fomadon Excel, do not silently use an equivalent developer if no exact row exists.
old = '''            DevTimeEngine.Result result = exactResult != null
                    ? exactResult
                    : DevTimeEngine.Result.notFound(MdcOfflineStore.combinationDiagnostic(
                            selectedFilm.name, dev.name, dilution, iso));
            runOnUiThread(() -> showDevelopmentResultSafely(result, tank, rolls,'''.replace("dev.name", "dev.name")
# At this point 'dev' is declared before the thread.
new = '''            DevTimeEngine.Result result = exactResult != null
                    ? exactResult
                    : DevTimeEngine.Result.notFound(MdcOfflineStore.combinationDiagnostic(
                            selectedFilm.name, dev.name, dilution, iso));
            if (result != null && result.found &&
                    "Fomadon Excel".equalsIgnoreCase(dev.name) &&
                    result.diagnostic != null &&
                    result.diagnostic.startsWith("EQUIVALENTE_APPROVATO|")) {
                result = DevTimeEngine.Result.notFound(
                        "Fomadon Excel " + dilution +
                        ": nessun tempo esatto disponibile. Per sicurezza non viene usata automaticamente un'equivalenza con un altro rivelatore.");
            }
            final DevTimeEngine.Result safeResult = result;
            runOnUiThread(() -> showDevelopmentResultSafely(safeResult, tank, rolls,'''
if old not in source:
    raise SystemExit("v0.6.8 result lookup marker missing")
source = source.replace(old, new, 1)

# The reuse accordion must know the developer dilution.
source = source.replace(
    'renderFilmCapacityForFormat(dev, stop, fix, workingVolumeMl, loadFormat);',
    'renderFilmCapacityForFormat(dev, stop, fix, workingVolumeMl, loadFormat, dilution);'
)
source = source.replace(
    'filmReuseCompactSummary(dev, stop, fix, workingVolumeMl)',
    'filmReuseCompactSummary(dev, stop, fix, workingVolumeMl, dilution)'
)

# Register/reset the developer bath with its dilution-specific key.
source = source.replace(
    'registerFilmUse(dev, workingVolumeMl, units);',
    'registerFilmUse(dev, workingVolumeMl, units, dilution);'
)
source = source.replace(
    'resetFilmBath(dev, workingVolumeMl);',
    'resetFilmBath(dev, workingVolumeMl, dilution);'
)

# Compact summary: Excel stock and 1+1 must never be described as the same bath.
pattern = re.compile(r'''    private String filmReuseCompactSummary\(Product dev, Product stop, Product fix,
                                           double volumeMl\) \{
.*?    \}

    private void renderFilmCapacityForFormat''', re.S)
replacement = '''    private String filmReuseCompactSummary(Product dev, Product stop, Product fix,
                                           double volumeMl, String dilution) {
        if (isFomadonExcel(dev)) {
            if ("stock".equals(normalizeFilmDilution(dilution)))
                return "Fomadon Excel stock · capacità FOMA 12 pellicole/L · contatore separato";
            if ("1+1".equals(normalizeFilmDilution(dilution)))
                return "Fomadon Excel 1+1 · capacità di riuso non ereditata dallo stock";
        }
        String developerState = dev != null &&
                dev.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT
                ? "rivelatore monouso" : "stato bagni disponibile";
        return developerState + " · apri per capacità e contatori";
    }

    private void renderFilmCapacityForFormat'''
source, n = pattern.subn(replacement, source, count=1)
if n != 1:
    raise SystemExit("v0.6.8 filmReuseCompactSummary replacement failed")

# Render developer capacity with dilution; stop/fix remain product-level.
pattern = re.compile(r'''    private void renderFilmCapacityForFormat\(Product dev, Product stop, Product fix,
                                             double volumeMl, String format\) \{
        renderFilmCapacity\(dev, stop, fix, volumeMl\);
(.*?)    \}

    private void renderFilmCapacity\(Product dev, Product stop, Product fix, double volumeMl\) \{
        if \(filmCapacityBox == null\) return;
        filmCapacityBox.removeAllViews\(\);
        resultLine\(filmCapacityBox, "RIVELATORE", filmCapacityStatus\(dev, volumeMl\)\);
        resultLine\(filmCapacityBox, "ARRESTO", filmCapacityStatus\(stop, volumeMl\)\);
        resultLine\(filmCapacityBox, "FISSAGGIO", filmCapacityStatus\(fix, volumeMl\)\);
    \}''', re.S)
replacement = '''    private void renderFilmCapacityForFormat(Product dev, Product stop, Product fix,
                                             double volumeMl, String format, String developerDilution) {
        renderFilmCapacity(dev, stop, fix, volumeMl, developerDilution);
\\1    }

    private void renderFilmCapacity(Product dev, Product stop, Product fix,
                                    double volumeMl, String developerDilution) {
        if (filmCapacityBox == null) return;
        filmCapacityBox.removeAllViews();
        resultLine(filmCapacityBox, "RIVELATORE", filmCapacityStatus(dev, volumeMl, developerDilution));
        resultLine(filmCapacityBox, "ARRESTO", filmCapacityStatus(stop, volumeMl, null));
        resultLine(filmCapacityBox, "FISSAGGIO", filmCapacityStatus(fix, volumeMl, null));
    }'''
source, n = pattern.subn(replacement, source, count=1)
if n != 1:
    raise SystemExit("v0.6.8 renderFilmCapacity replacement failed")

# Helpers and dilution-aware capacity status.
pattern = re.compile(r'''    private String filmCapacityStatus\(Product p, double volumeMl\) \{
.*?    \}

    private String paperCapacityStatus''', re.S)
replacement = '''    private boolean isFomadonExcel(Product p) {
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
        if (isFomadonExcel(p)) {
            String d = normalizeFilmDilution(dilution);
            if ("stock".equals(d)) return base + "_stock";
            if ("1+1".equals(d)) return base + "_1plus1";
        }
        return base;
    }

    private String filmCapacityStatus(Product p, double volumeMl, String dilution) {
        if (p == null) return "—";

        if (isFomadonExcel(p)) {
            String d = normalizeFilmDilution(dilution);
            if ("stock".equals(d)) {
                String k = filmBathKey(p, d);
                float storedVol = prefs.getFloat("film_bath_volume_" + k, 0f);
                float used = prefs.contains("film_used_units_v2_" + k)
                        ? prefs.getFloat("film_used_units_v2_" + k, 0f)
                        : prefs.getInt("film_used_" + k, 0);
                if (storedVol > 0 && Math.abs(storedVol - volumeMl) > 1) used = 0;
                double capacity = 12.0 * volumeMl / 1000.0;
                double remaining = Math.max(0, capacity - used);
                return "Stock · capacità FOMA 12 pellicole/L. Bagno " + fmt(volumeMl) +
                        " ml · capacità " + fmt(capacity) +
                        " rulli equivalenti · usati " + fmt(used) +
                        " · residui " + fmt(remaining) + ".";
            }
            if ("1+1".equals(d)) {
                return "1+1 · tempi distinti dallo stock. La capacità FOMA di 12 pellicole/L " +
                        "non viene applicata automaticamente al bagno diluito; contatore di riuso disabilitato.";
            }
            return "Fomadon Excel: il riutilizzo dipende dalla diluizione selezionata.";
        }

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

    private String paperCapacityStatus'''
source, n = pattern.subn(replacement, source, count=1)
if n != 1:
    raise SystemExit("v0.6.8 filmCapacityStatus replacement failed")

# Dilution-aware registration/reset. Excel 1+1 deliberately has no automatic reuse counter.
pattern = re.compile(r'''    private void registerFilmUse\(Product p, double volumeMl, double units\) \{
.*?    \}

    private void resetFilmBath\(Product p, double volumeMl\) \{
.*?    \}

    private void registerPaperUse''', re.S)
replacement = '''    private void registerFilmUse(Product p, double volumeMl, double units) {
        registerFilmUse(p, volumeMl, units, null);
    }

    private void registerFilmUse(Product p, double volumeMl, double units, String dilution) {
        if (p == null || p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT) return;
        if (isFomadonExcel(p) && "1+1".equals(normalizeFilmDilution(dilution))) return;
        String k = filmBathKey(p, dilution);
        float oldVol = prefs.getFloat("film_bath_volume_" + k, 0f);
        float used = prefs.contains("film_used_units_v2_" + k)
                ? prefs.getFloat("film_used_units_v2_" + k, 0f)
                : prefs.getInt("film_used_" + k, 0);
        if (oldVol <= 0 || Math.abs(oldVol - volumeMl) > 1) used = 0;
        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putFloat("film_used_units_v2_" + k, used + (float) units).apply();
    }

    private void resetFilmBath(Product p, double volumeMl) {
        resetFilmBath(p, volumeMl, null);
    }

    private void resetFilmBath(Product p, double volumeMl, String dilution) {
        if (p == null) return;
        if (isFomadonExcel(p) && "1+1".equals(normalizeFilmDilution(dilution))) return;
        String k = filmBathKey(p, dilution);
        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putInt("film_used_" + k, 0)
                .putFloat("film_used_units_v2_" + k, 0f).apply();
    }

    private void registerPaperUse'''
source, n = pattern.subn(replacement, source, count=1)
if n != 1:
    raise SystemExit("v0.6.8 film register/reset replacement failed")

# Product card: do not present one generic reuse rule for both Excel dilutions.
needle = '''    private String reuseDescription(Product p) {
        if (p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT)'''
repl = '''    private String reuseDescription(Product p) {
        if (isFomadonExcel(p))
            return "Riutilizzo: dipende dalla diluizione. Stock: capacità FOMA 12 pellicole/L. " +
                    "1+1: capacità di riuso non ereditata automaticamente dallo stock.";
        if (p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT)'''
if needle not in source:
    raise SystemExit("v0.6.8 reuseDescription marker missing")
source = source.replace(needle, repl, 1)

# Guardrails.
required = [
    "CHEMISTRY_SAFETY_068",
    '"TEMPO JOBO CPE2 · " + dilution',
    "Fomadon Excel stock · capacità FOMA 12 pellicole/L",
    "Fomadon Excel 1+1 · capacità di riuso non ereditata dallo stock",
    "contatore di riuso disabilitato",
    'result.diagnostic.startsWith("EQUIVALENTE_APPROVATO|")',
    "registerFilmUse(dev, workingVolumeMl, units, dilution);",
    "resetFilmBath(dev, workingVolumeMl, dilution);",
]
for marker in required:
    if marker not in source:
        raise SystemExit("v0.6.8 guardrail missing: " + marker)

SOURCE.write_text(source, encoding="utf-8")
print("chemistry_safety_068=APPLIED")
print("fomadon_excel_stock_reuse=12_FILMS_PER_LITRE")
print("fomadon_excel_1plus1_reuse=NOT_INHERITED")
print("fomadon_excel_equivalent_fallback=BLOCKED")
print("time_heading_includes_selected_dilution=PASS")
