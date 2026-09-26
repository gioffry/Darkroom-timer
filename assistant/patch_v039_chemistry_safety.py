from pathlib import Path
import re

# v0.3.9
# Chemistry safety correction:
# - Fomadon Excel reuse is dilution-specific: stock reusable, 1+1 one-shot
# - Compard Fix Ag Plus film dilution corrected to 1+5 / 1+7
# - remove unverified numeric Compard capacity from UI
# - make the generic JOBO -15% conversion explicit as an estimate, not manufacturer data

p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# ---------------------------------------------------------------------------
# 1) Correct curated Compard Fix Ag Plus data.
# Film: 1+5 rapid / 1+7 standard. Paper: 1+7 / 1+9.
# Default working dilution is 1+5 because the film workflow has one fixer selector.
# ---------------------------------------------------------------------------
pattern = re.compile(r'''            new Product\("Compard Fix Ag Plus", ROLE_FIX, false,
                    new String\[\]\{"1\+4"\}, new String\[\]\{"1\+9"\}, "1\+4", null,
                    90, "", ChemistrySpecEngine\.REUSE_REUSABLE, 20, 2\.1\),''')
replacement = '''            new Product("Compard Fix Ag Plus", ROLE_FIX, false,
                    new String[]{"1+5", "1+7"}, new String[]{"1+7", "1+9"}, "1+5", null,
                    90, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('Compard Fix Ag Plus legacy curated marker missing')

# Repair only the known-bad legacy Compard default persisted by previous app versions.
pattern = re.compile(r'''    private void repairCuratedAuxInventory\(\) \{.*?\n    \}\n\n''', re.S)
replacement = r'''    private void repairCuratedAuxInventory() {
        Set<String> inv = getInventory();
        if (inv.isEmpty()) return;
        for (String name : inv) {
            Product curated = curatedAuxByName(name);
            if (curated == null) continue;
            Product saved = loadSavedProduct(name);
            if (saved == null) {
                saveProductMetadata(curated);
                continue;
            }
            if ("Compard Fix Ag Plus".equalsIgnoreCase(name) &&
                    ("1+4".equalsIgnoreCase(saved.workingDilution) ||
                     (saved.filmDilutions.length == 1 &&
                      "1+4".equalsIgnoreCase(saved.filmDilutions[0])))) {
                saveProductMetadata(curated);
            }
        }
    }

'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('repairCuratedAuxInventory v0.3.8 marker missing')

# ---------------------------------------------------------------------------
# 2) Remember the exact developer dilution used for the current calculation.
# Reuse/capacity must never be shared between stock and 1+1.
# ---------------------------------------------------------------------------
field_marker = '    private int lastFilmRolls;\n'
if field_marker not in s:
    raise SystemExit('lastFilmRolls marker missing')
s = s.replace(field_marker,
              field_marker + '    private String lastFilmDeveloperDilution = "";\n', 1)

dil_marker = '        String dilution = String.valueOf(dilutionSpinner.getSelectedItem());\n'
if dil_marker not in s:
    raise SystemExit('film dilution marker missing')
s = s.replace(dil_marker,
              dil_marker + '        lastFilmDeveloperDilution = dilution;\n', 1)

# ---------------------------------------------------------------------------
# 3) Dilution-specific film reuse.
# FOMA states 12 films per litre for Fomadon Excel stock working solution.
# The 1+1 use is treated as one-shot; it must never inherit the stock counter.
# ---------------------------------------------------------------------------
pattern = re.compile(r'''    private String filmCapacityStatus\(Product p, double volumeMl\) \{.*?\n    \}\n\n    private String paperCapacityStatus''', re.S)
replacement = r'''    private String normalizedFilmDeveloperDilution() {
        String d = lastFilmDeveloperDilution == null ? "" : lastFilmDeveloperDilution.trim().toLowerCase(Locale.ROOT);
        d = d.replace(" ", "").replace(":", "+");
        if ("1+0".equals(d) || "undiluted".equals(d) || "fullstrength".equals(d) || "full-strength".equals(d))
            return "stock";
        return d;
    }

    private boolean isFomadonExcel(Product p) {
        return p != null && "Fomadon Excel".equalsIgnoreCase(p.name);
    }

    private String filmCapacityStatus(Product p, double volumeMl) {
        if (p == null) return "—";

        if (isFomadonExcel(p)) {
            String dilution = normalizedFilmDeveloperDilution();
            if ("1+1".equals(dilution)) {
                return "1+1 monouso: prepara fresco e scarta dopo questo sviluppo. " +
                        "Non usa il contatore dello stock.";
            }
            if ("stock".equals(dilution)) {
                String suffix = key(p.name) + "_stock";
                int used = prefs.getInt("film_used_" + suffix, 0);
                float storedVol = prefs.getFloat("film_bath_volume_" + suffix, 0f);
                if (storedVol > 0 && Math.abs(storedVol - volumeMl) > 1) used = 0;
                int capacity = (int)Math.floor(12.0 * volumeMl / 1000.0 + 1e-9);
                int remaining = Math.max(0, capacity - used);
                return "Stock riutilizzabile · capacità FOMA 12 pellicole/L. " +
                        "Bagno " + fmt(volumeMl) + " ml · capacità " + capacity +
                        " · usate " + used + " · residue " + remaining + ".";
            }
            return "Fomadon Excel: seleziona stock oppure 1+1; il riutilizzo dipende dalla diluizione.";
        }

        if (p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT)
            return "Monouso: prepara il bagno fresco e scartalo dopo lo sviluppo.";

        int used = prefs.getInt("film_used_" + key(p.name), 0);
        float storedVol = prefs.getFloat("film_bath_volume_" + key(p.name), 0f);
        if (storedVol > 0 && Math.abs(storedVol - volumeMl) > 1) used = 0;

        if ("Adox Adostop ECO".equalsIgnoreCase(p.name)) {
            return "Riutilizzabile fino al viraggio verde/blu · usati " + used + " rulli.";
        }
        if ("Compard Fix Ag Plus".equalsIgnoreCase(p.name)) {
            return "Riutilizzabile · pellicola: 1+5 rapido oppure 1+7 standard. " +
                    "Capacità numerica non mostrata senza un dato verificato per il bagno in uso · usati " +
                    used + " rulli.";
        }

        if (p.reuseMode != ChemistrySpecEngine.REUSE_REUSABLE)
            return "Il database tempi non contiene dati affidabili sul riutilizzo: nessun contatore applicato.";
        if (p.filmCapacityPerLiter <= 0)
            return "Riutilizzabile; il produttore non esprime la capacità in rulli. " +
                    "Rulli passati nel bagno: " + used + ".";
        int capacity = (int) Math.floor(p.filmCapacityPerLiter * volumeMl / 1000.0 + 1e-9);
        int remaining = Math.max(0, capacity - used);
        return "Bagno " + fmt(volumeMl) + " ml · capacità almeno " + capacity +
                " rulli · passati " + used + " · residui almeno " + remaining + ".";
    }

    private String paperCapacityStatus'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('filmCapacityStatus v0.3.8 marker missing')

# Register stock and 1+1 independently. 1+1 never increments a reuse counter.
pattern = re.compile(r'''    private void registerFilmUse\(Product p, double volumeMl, int rolls\) \{.*?\n    \}\n\n    private void resetFilmBath''', re.S)
replacement = r'''    private void registerFilmUse(Product p, double volumeMl, int rolls) {
        if (p == null) return;

        if (isFomadonExcel(p)) {
            if (!"stock".equals(normalizedFilmDeveloperDilution())) return;
            String suffix = key(p.name) + "_stock";
            float oldVol = prefs.getFloat("film_bath_volume_" + suffix, 0f);
            int used = prefs.getInt("film_used_" + suffix, 0);
            if (oldVol <= 0 || Math.abs(oldVol - volumeMl) > 1) used = 0;
            prefs.edit().putFloat("film_bath_volume_" + suffix, (float) volumeMl)
                    .putInt("film_used_" + suffix, used + rolls).apply();
            return;
        }

        if (p.reuseMode != ChemistrySpecEngine.REUSE_REUSABLE) return;
        String k = key(p.name);
        float oldVol = prefs.getFloat("film_bath_volume_" + k, 0f);
        int used = prefs.getInt("film_used_" + k, 0);
        if (oldVol <= 0 || Math.abs(oldVol - volumeMl) > 1) used = 0;
        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putInt("film_used_" + k, used + rolls).apply();
    }

    private void resetFilmBath'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('registerFilmUse marker missing')

pattern = re.compile(r'''    private void resetFilmBath\(Product p, double volumeMl\) \{.*?\n    \}\n\n    private void registerPaperUse''', re.S)
replacement = r'''    private void resetFilmBath(Product p, double volumeMl) {
        if (p == null) return;

        if (isFomadonExcel(p)) {
            if (!"stock".equals(normalizedFilmDeveloperDilution())) return;
            String suffix = key(p.name) + "_stock";
            prefs.edit().putFloat("film_bath_volume_" + suffix, (float) volumeMl)
                    .putInt("film_used_" + suffix, 0).apply();
            return;
        }

        String k = key(p.name);
        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putInt("film_used_" + k, 0).apply();
    }

    private void registerPaperUse'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('resetFilmBath marker missing')

# Product detail: show the Excel stock counter rather than the obsolete generic counter.
pattern = re.compile(r'''    private void appendStoredBathStatus\(StringBuilder msg, Product p\) \{
        String k = key\(p\.name\);
        int filmUsed = prefs\.getInt\("film_used_" \+ k, 0\);
        float filmVol = prefs\.getFloat\("film_bath_volume_" \+ k, 0f\);''')
replacement = '''    private void appendStoredBathStatus(StringBuilder msg, Product p) {
        String k = key(p.name);
        String filmKey = isFomadonExcel(p) ? k + "_stock" : k;
        int filmUsed = prefs.getInt("film_used_" + filmKey, 0);
        float filmVol = prefs.getFloat("film_bath_volume_" + filmKey, 0f);'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('appendStoredBathStatus marker missing')

# ---------------------------------------------------------------------------
# 4) JOBO conversion: keep the rough calculation, but never present it as
# a manufacturer-verified rotary time.
# ---------------------------------------------------------------------------
s = s.replace('resultLine(filmResultBox, "TEMPO JOBO CPE2", result.finalDisplay());',
              'resultLine(filmResultBox, "STIMA JOBO CPE2", result.finalDisplay());', 1)
s = s.replace('conversion += "JOBO CPE2: rotazione continua, adattamento −15%";',
              'conversion += "JOBO CPE2: stima rotazione continua −15% · regola generale, non dato specifico del produttore";', 1)

p.write_text(s, encoding='utf-8')
print('v0.3.9 chemistry safety patch applied')
