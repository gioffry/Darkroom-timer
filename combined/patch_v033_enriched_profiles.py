#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# SQLite access for the enriched offline profile tables.
if 'import android.database.Cursor;' not in s:
    s = s.replace('import android.content.SharedPreferences;\n',
                  'import android.content.SharedPreferences;\nimport android.database.Cursor;\nimport android.database.sqlite.SQLiteDatabase;\n', 1)

# One extra operational state for Rollei Supergrain: not declared reusable, but the
# manufacturer recommends fresh working solution rather than publishing a replenishment scheme.
if 'REUSE_FRESH_RECOMMENDED' not in s:
    marker = '    private static final int ROLE_CHEMISTRY = 64;\n'
    if marker not in s:
        raise SystemExit('v033 ROLE_CHEMISTRY marker missing')
    s = s.replace(marker, marker + '    private static final int REUSE_FRESH_RECOMMENDED = 3;\n', 1)

# Fix compound roles: a FILM_DEVELOPER|CHEMISTRY product must be shown as film developer,
# not as generic chemistry (the v0.3.2 FOMADON Excel screenshot regression).
pat = re.compile(r'''    private int typeIndexForRole\(int role\) \{.*?\n    \}''', re.S)
rep = '''    private int typeIndexForRole(int role) {\n        if ((role & ROLE_FILM_DEV) != 0 && (role & ROLE_PAPER_DEV) != 0) return 2;\n        if ((role & ROLE_FILM_DEV) != 0) return 0;\n        if ((role & ROLE_PAPER_DEV) != 0) return 1;\n        if ((role & ROLE_STOP) != 0) return 3;\n        if ((role & ROLE_FIX) != 0) return 4;\n        if ((role & ROLE_WETTING) != 0) return 5;\n        if ((role & ROLE_WASHING) != 0) return 6;\n        if ((role & ROLE_CHEMISTRY) != 0) return 7;\n        return 0;\n    }'''
s, n = pat.subn(rep, s, count=1)
if n != 1:
    raise SystemExit('v033 typeIndexForRole replacement failed')

# Existing saved inventory entries are also enriched at read time. User-entered values win;
# the DB only fills missing values, except the known role classification for canonical developers.
pat = re.compile(r'''    private Product findProduct\(String name\) \{.*?\n    \}\n\n    private FilmStock findFilm''', re.S)
rep = r'''    private Product findProduct(String name) {
        if (name == null) return null;
        String wanted = name.trim();
        Product saved = loadSavedProduct(wanted);
        if (saved != null) return applyDeveloperProfile(saved);

        Product result = null;
        FullCatalogStore.Chemical cat = FullCatalogStore.chemical(wanted);
        if (cat != null && (cat.roles & ~128) != 0) {
            result = new Product(cat.name, cat.roles, cat.stockPrep,
                    cat.filmDilutions, cat.paperDilutions, cat.workingDilution,
                    null, -1, cat.sourceUrl,
                    ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1);
        }

        String canonical = FullCatalogStore.canonicalDeveloper(wanted);
        if (result == null && canonical != null) {
            Product savedCanonical = loadSavedProduct(canonical);
            if (savedCanonical != null) result = savedCanonical;
            else result = offlineDeveloperProduct(canonical);
        }
        if (result == null) result = curatedAuxByName(wanted);
        if (result == null) {
            for (Product fp : fallbackProducts) if (fp.name.equalsIgnoreCase(wanted)) { result = fp; break; }
        }
        return applyDeveloperProfile(result);
    }

    private FilmStock findFilm'''
s, n = pat.subn(rep, s, count=1)
if n != 1:
    raise SystemExit('v033 findProduct replacement failed')

# Enriched database bridge + readable manufacturer summary.
marker = '    private boolean hasFormatSuffix(String s) {'
if marker not in s:
    raise SystemExit('v033 helper insertion marker missing')
helpers = r'''    private Product applyDeveloperProfile(Product p) {
        if (p == null) return null;
        String canonical = FullCatalogStore.canonicalDeveloper(p.name);
        if (canonical == null) return p;
        SQLiteDatabase db = MdcOfflineStore.database();
        if (db == null) return p;

        String preparation = "", reuseRaw = "", capacityText = "", manufacturerSource = "";
        try (Cursor c = db.rawQuery(
                "SELECT pr.preparation,pr.reuse_mode,pr.capacity_text," +
                "(SELECT s.source_url FROM developer_profile_sources s WHERE s.developer_norm=pr.developer_norm AND s.source_kind='MANUFACTURER' ORDER BY s.checked_at DESC LIMIT 1) " +
                "FROM developer_profiles pr JOIN developers d ON d.norm_name=pr.developer_norm WHERE d.name=? COLLATE NOCASE LIMIT 1",
                new String[]{canonical})) {
            if (c.moveToFirst()) {
                preparation = c.isNull(0) ? "" : c.getString(0);
                reuseRaw = c.isNull(1) ? "" : c.getString(1);
                capacityText = c.isNull(2) ? "" : c.getString(2);
                manufacturerSource = c.isNull(3) ? "" : c.getString(3);
            }
        } catch (Throwable ignored) { return p; }

        LinkedHashSet<String> dils = new LinkedHashSet<>();
        try (Cursor c = db.rawQuery(
                "SELECT dd.dilution FROM developer_dilutions dd JOIN developers d ON d.norm_name=dd.developer_norm " +
                "WHERE d.name=? COLLATE NOCASE ORDER BY CASE dd.source_kind WHEN 'MDC' THEN 0 ELSE 1 END, dd.dilution_norm",
                new String[]{canonical})) {
            while (c.moveToNext()) {
                String v = c.getString(0);
                if (v != null && !v.trim().isEmpty()) dils.add(v.trim());
            }
        } catch (Throwable ignored) {}

        int roles = p.roles;
        FullCatalogStore.Chemical cat = FullCatalogStore.chemical(p.name);
        if (cat != null && cat.roles != 0) roles = cat.roles;
        else if ((roles & ROLE_FILM_DEV) == 0) roles |= ROLE_FILM_DEV;

        int reuse = p.reuseMode;
        if (reuse == ChemistrySpecEngine.REUSE_UNKNOWN && reuseRaw != null) {
            String r = reuseRaw.toLowerCase(Locale.ROOT);
            if (r.contains("fresh_working_solution_recommended")) reuse = REUSE_FRESH_RECOMMENDED;
            else if (r.contains("reusable") || r.contains("replenish") || r.contains("capacity"))
                reuse = ChemistrySpecEngine.REUSE_REUSABLE;
            else if (r.contains("one_shot") || r.contains("one-shot"))
                reuse = ChemistrySpecEngine.REUSE_ONE_SHOT;
        }

        double filmCap = p.filmCapacityPerLiter;
        if (filmCap <= 0) filmCap = safeWorkingFilmCapacity(capacityText);
        String instructions = p.stockInstructions;
        if ((instructions == null || instructions.trim().isEmpty()) && preparation != null && !preparation.trim().isEmpty())
            instructions = preparation.trim();
        String source = p.sourceUrl;
        if ((source == null || source.isEmpty()) && manufacturerSource != null) source = manufacturerSource;
        String[] filmDil = dils.isEmpty() ? p.filmDilutions : dils.toArray(new String[0]);

        return new Product(p.name, roles, p.stockPrep || (instructions != null && !instructions.isEmpty()),
                filmDil, p.paperDilutions, p.workingDilution, instructions, p.expiryDays,
                source, reuse, filmCap, p.paperCapacitySqMPerLiter);
    }

    private double safeWorkingFilmCapacity(String text) {
        if (text == null || text.trim().isEmpty()) return -1;
        java.util.regex.Matcher a = java.util.regex.Pattern.compile(
                "(?i)1\\s*(?:litre|liter|litro|l\\b)[^0-9]{0,80}(\\d+(?:[.,]\\d+)?)\\s*(?:rolls?|films?|rulli)").matcher(text);
        if (a.find()) return parseProfileDouble(a.group(1));
        java.util.regex.Matcher b = java.util.regex.Pattern.compile(
                "(?i)(\\d+(?:[.,]\\d+)?)\\s*(?:rolls?|films?|rulli)[^.;]{0,80}(?:per|/)\\s*(?:1\\s*)?(?:litre|liter|litro|l\\b)").matcher(text);
        if (b.find()) return parseProfileDouble(b.group(1));
        return -1;
    }

    private double parseProfileDouble(String s) {
        try { return Double.parseDouble(s.replace(',', '.')); } catch (Exception e) { return -1; }
    }

    private String developerTechnicalSummary(String name) {
        String canonical = FullCatalogStore.canonicalDeveloper(name);
        if (canonical == null) return "";
        SQLiteDatabase db = MdcOfflineStore.database();
        if (db == null) return "";
        try (Cursor c = db.rawQuery(
                "SELECT pr.manufacturer,pr.physical_state,pr.preparation,pr.reuse_mode,pr.reuse_instructions,pr.capacity_text," +
                "pr.shelf_life_unopened,pr.shelf_life_opened,pr.shelf_life_stock,pr.shelf_life_working,pr.storage_notes " +
                "FROM developer_profiles pr JOIN developers d ON d.norm_name=pr.developer_norm WHERE d.name=? COLLATE NOCASE LIMIT 1",
                new String[]{canonical})) {
            if (!c.moveToFirst()) return "";
            StringBuilder out = new StringBuilder();
            appendTech(out, "Produttore", c.getString(0));
            appendTech(out, "Stato", c.getString(1));
            appendTech(out, "Preparazione", c.getString(2));
            appendTech(out, "Riutilizzo", prettyProfileValue(c.getString(3)));
            appendTech(out, "Modalità riutilizzo", c.getString(4));
            appendTech(out, "Capacità", c.getString(5));
            appendTech(out, "Conservabilità confezione", c.getString(6));
            appendTech(out, "Conservabilità aperto", c.getString(7));
            appendTech(out, "Conservabilità stock", c.getString(8));
            appendTech(out, "Conservabilità lavoro", c.getString(9));
            appendTech(out, "Conservazione", c.getString(10));
            return out.toString();
        } catch (Throwable ignored) { return ""; }
    }

    private void appendTech(StringBuilder out, String label, String value) {
        if (value == null || value.trim().isEmpty()) return;
        if (out.length() > 0) out.append("\\n");
        out.append(label).append(": ").append(value.trim());
    }

    private String prettyProfileValue(String value) {
        if (value == null) return "";
        return value.replace('_', ' ').trim();
    }

'''
s = s.replace(marker, helpers + marker, 1)

# Show the raw producer-backed data in both the product detail and edit screens.
needle = '        msg.append("\\n\\n").append(reuseDescription(p));'
if needle not in s:
    raise SystemExit('v033 details marker missing')
s = s.replace(needle, '''        String technical = developerTechnicalSummary(p.name);\n        if (!technical.isEmpty()) msg.append("\\n\\nDATI PRODUTTORE\\n").append(technical);\n        msg.append("\\n\\n").append(reuseDescription(p));''', 1)

needle = '        box.addView(fieldBlock("DURATA DOPO APERTURA (giorni)", expiry));'
if needle not in s:
    raise SystemExit('v033 edit technical marker missing')
s = s.replace(needle, needle + '''\n\n        String technical = developerTechnicalSummary(p.name);\n        if (!technical.isEmpty()) {\n            TextView technicalView = label(technical, 13, WHITE, false);\n            technicalView.setPadding(dp(10), dp(10), dp(10), dp(10));\n            technicalView.setBackground(bg(CARD, 10, BORDER, 1));\n            box.addView(fieldBlock("DATI PRODUTTORE (database)", technicalView));\n        }''', 1)

# Preserve the nuanced Supergrain state instead of falsely labelling it reusable.
s = s.replace('''        if (p.reuseMode == ChemistrySpecEngine.REUSE_REUSABLE) {''',
'''        if (p.reuseMode == REUSE_FRESH_RECOMMENDED)\n            return "Riutilizzo: il produttore consiglia soluzione di lavoro fresca; nessun reintegro specifico pubblicato.";\n        if (p.reuseMode == ChemistrySpecEngine.REUSE_REUSABLE) {''', 1)

s = s.replace('''        String[] reuseLabels = new String[]{"Non determinato", "Monouso", "Riutilizzabile"};\n        Spinner reuse = spinner(reuseLabels);\n        reuse.setSelection(p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT ? 1 :\n                p.reuseMode == ChemistrySpecEngine.REUSE_REUSABLE ? 2 : 0);''',
'''        String[] reuseLabels = new String[]{"Non determinato", "Monouso", "Riutilizzabile", "Soluzione fresca consigliata"};\n        Spinner reuse = spinner(reuseLabels);\n        reuse.setSelection(p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT ? 1 :\n                p.reuseMode == ChemistrySpecEngine.REUSE_REUSABLE ? 2 :\n                p.reuseMode == REUSE_FRESH_RECOMMENDED ? 3 : 0);''', 1)

s = s.replace('''                    int reuseMode = reuse.getSelectedItemPosition() == 1\n                            ? ChemistrySpecEngine.REUSE_ONE_SHOT\n                            : reuse.getSelectedItemPosition() == 2\n                            ? ChemistrySpecEngine.REUSE_REUSABLE\n                            : ChemistrySpecEngine.REUSE_UNKNOWN;''',
'''                    int reuseMode = reuse.getSelectedItemPosition() == 1\n                            ? ChemistrySpecEngine.REUSE_ONE_SHOT\n                            : reuse.getSelectedItemPosition() == 2\n                            ? ChemistrySpecEngine.REUSE_REUSABLE\n                            : reuse.getSelectedItemPosition() == 3\n                            ? REUSE_FRESH_RECOMMENDED\n                            : ChemistrySpecEngine.REUSE_UNKNOWN;''', 1)

# Do not automatically count repeated use for the fresh-solution-recommended state.
s = s.replace('''        if (p == null || p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT) return;''',
'''        if (p == null || p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT || p.reuseMode == REUSE_FRESH_RECOMMENDED) return;''', 1)

p.write_text(s, encoding='utf-8')

# Force a fresh bundled catalog copy on upgrade from v0.3.2; user inventory remains in SharedPreferences.
m = Path('combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
ms = m.read_text(encoding='utf-8')
ms = ms.replace('private static final int DB_VERSION = 3;', 'private static final int DB_VERSION = 4;', 1)
ms = ms.replace('private static final String DB_NAME = "mdc_offline_darkroom_v029.sqlite";',
                'private static final String DB_NAME = "mdc_offline_darkroom_v033.sqlite";', 1)
m.write_text(ms, encoding='utf-8')

print('v0.3.3 enriched developer profile bridge applied')
