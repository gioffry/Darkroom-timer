#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# Replace the v0.3.4 summary reader. Important rules:
# - only *_it fields are shown as technical prose;
# - raw English is retained in SQLite but never used as display fallback;
# - official source title is not injected in English into the Italian body;
# - if no shelf-life field is available, say so explicitly instead of leaving
#   an apparently broken blank duration field.
pat = re.compile(r'''    private String chemicalTechnicalSummaryIt\(String name\) \{.*?\n    \}\n\n    private String normalizeTechnicalName''', re.S)
rep = r'''    private String chemicalTechnicalSummaryIt(String name) {
        SQLiteDatabase db = MdcOfflineStore.database();
        if (db == null || name == null || name.trim().isEmpty()) return "";

        String canonical = FullCatalogStore.canonicalDeveloper(name);
        if (canonical != null) {
            try (Cursor c = db.rawQuery(
                    "SELECT pr.manufacturer,pr.physical_state_it,pr.preparation_it,pr.reuse_instructions_it,pr.capacity_it," +
                    "pr.shelf_life_unopened_it,pr.shelf_life_opened_it,pr.shelf_life_stock_it,pr.shelf_life_working_it," +
                    "pr.storage_notes_it,pr.notes_it," +
                    "(SELECT s.source_date FROM developer_profile_sources s WHERE s.developer_norm=pr.developer_norm AND s.source_kind='MANUFACTURER' ORDER BY s.checked_at DESC LIMIT 1) " +
                    "FROM developer_profiles pr JOIN developers d ON d.norm_name=pr.developer_norm WHERE d.name=? COLLATE NOCASE LIMIT 1",
                    new String[]{canonical})) {
                if (c.moveToFirst()) {
                    StringBuilder out = new StringBuilder();
                    appendTechRaw(out, "Produttore", c.getString(0));
                    appendTech(out, "Forma", c.getString(1));
                    appendTech(out, "Preparazione", c.getString(2));
                    appendTech(out, "Riutilizzo", c.getString(3));
                    appendTech(out, "Capacità", c.getString(4));
                    String unopened = safeItalianTechnical(c.getString(5));
                    String opened = safeItalianTechnical(c.getString(6));
                    String stock = safeItalianTechnical(c.getString(7));
                    String working = safeItalianTechnical(c.getString(8));
                    if (unopened.isEmpty() && opened.isEmpty() && stock.isEmpty() && working.isEmpty()) {
                        appendTechRaw(out, "Durata / conservabilità", "Non dichiarata nella fonte tecnica verificata disponibile nell’app.");
                    } else {
                        appendTech(out, "Durata confezione originale", unopened);
                        appendTech(out, "Durata dopo apertura", opened);
                        appendTech(out, "Durata stock", stock);
                        appendTech(out, "Durata soluzione di lavoro", working);
                    }
                    appendTech(out, "Conservazione", c.getString(9));
                    appendTech(out, "Note", c.getString(10));
                    String date = cleanTechnicalText(c.getString(11));
                    appendTechRaw(out, "Fonte tecnica",
                            "Documentazione ufficiale del produttore" +
                            (date.isEmpty() ? "" : " · " + date));
                    return out.toString();
                }
            } catch (Throwable ignored) {}
        }

        String n = normalizeTechnicalName(name);
        if ("adostop eco".equals(n)) n = "adox adostop eco";
        if ("foma adostop eco".equals(n)) n = "adox adostop eco";
        if ("foma fomatol lqn".equals(n)) n = "fomatol lqn";
        if ("foma fix".equals(n)) n = "fomafix";
        if ("foma fotonal".equals(n)) n = "fotonal";
        try (Cursor c = db.rawQuery(
                "SELECT manufacturer,product_type_it,physical_state_it,preparation_it,capacity_it," +
                "shelf_life_unopened_it,shelf_life_opened_it,shelf_life_stock_it,shelf_life_working_it," +
                "storage_notes_it,notes_it,source_date FROM auxiliary_chemical_profiles WHERE norm_name=? LIMIT 1",
                new String[]{n})) {
            if (!c.moveToFirst()) return "";
            StringBuilder out = new StringBuilder();
            appendTechRaw(out, "Produttore", c.getString(0));
            appendTech(out, "Tipo", c.getString(1));
            appendTech(out, "Forma", c.getString(2));
            appendTech(out, "Preparazione", c.getString(3));
            appendTech(out, "Capacità", c.getString(4));
            String unopened = safeItalianTechnical(c.getString(5));
            String opened = safeItalianTechnical(c.getString(6));
            String stock = safeItalianTechnical(c.getString(7));
            String working = safeItalianTechnical(c.getString(8));
            if (unopened.isEmpty() && opened.isEmpty() && stock.isEmpty() && working.isEmpty()) {
                appendTechRaw(out, "Durata / conservabilità", "Non dichiarata nella fonte tecnica verificata disponibile nell’app.");
            } else {
                appendTech(out, "Durata confezione originale", unopened);
                appendTech(out, "Durata dopo apertura", opened);
                appendTech(out, "Durata stock", stock);
                appendTech(out, "Durata soluzione di lavoro", working);
            }
            appendTech(out, "Conservazione", c.getString(9));
            appendTech(out, "Note", c.getString(10));
            String date = cleanTechnicalText(c.getString(11));
            appendTechRaw(out, "Fonte tecnica",
                    "Documentazione ufficiale del produttore" +
                    (date.isEmpty() ? "" : " · " + date));
            return out.toString();
        } catch (Throwable ignored) { return ""; }
    }

    private String chemicalTechnicalPreparationIt(String name) {
        SQLiteDatabase db = MdcOfflineStore.database();
        if (db == null || name == null) return "";
        String canonical = FullCatalogStore.canonicalDeveloper(name);
        if (canonical != null) {
            try (Cursor c = db.rawQuery(
                    "SELECT pr.preparation_it FROM developer_profiles pr JOIN developers d ON d.norm_name=pr.developer_norm WHERE d.name=? COLLATE NOCASE LIMIT 1",
                    new String[]{canonical})) {
                if (c.moveToFirst()) return safeItalianTechnical(c.getString(0));
            } catch (Throwable ignored) {}
        }
        String n = normalizeTechnicalName(name);
        if ("adostop eco".equals(n)) n = "adox adostop eco";
        if ("foma adostop eco".equals(n)) n = "adox adostop eco";
        if ("foma fomatol lqn".equals(n)) n = "fomatol lqn";
        if ("foma fix".equals(n)) n = "fomafix";
        if ("foma fotonal".equals(n)) n = "fotonal";
        try (Cursor c = db.rawQuery(
                "SELECT preparation_it FROM auxiliary_chemical_profiles WHERE norm_name=? LIMIT 1",
                new String[]{n})) {
            return c.moveToFirst() ? safeItalianTechnical(c.getString(0)) : "";
        } catch (Throwable ignored) { return ""; }
    }

    private String chemicalTechnicalRawPreparation(String name) {
        SQLiteDatabase db = MdcOfflineStore.database();
        if (db == null || name == null) return "";
        String canonical = FullCatalogStore.canonicalDeveloper(name);
        if (canonical == null) return "";
        try (Cursor c = db.rawQuery(
                "SELECT pr.preparation FROM developer_profiles pr JOIN developers d ON d.norm_name=pr.developer_norm WHERE d.name=? COLLATE NOCASE LIMIT 1",
                new String[]{canonical})) {
            return c.moveToFirst() ? cleanTechnicalText(c.getString(0)) : "";
        } catch (Throwable ignored) { return ""; }
    }

    private String normalizeTechnicalName'''
s, n = pat.subn(lambda _m: rep, s, count=1)
if n != 1:
    raise SystemExit('v0.3.5 technical summary replacement failed')

# Fix the literal "\\n" bug at its source and block residual English prose.
pat = re.compile(r'''    private void appendTech\(StringBuilder out, String label, String value\) \{.*?\n    \}\n\n    private String prettyProfileValue''', re.S)
rep = r'''    private String cleanTechnicalText(String value) {
        if (value == null) return "";
        return value.replace("\\r\\n", "\n")
                .replace("\\n", "\n")
                .replace("\\r", "\n")
                .trim();
    }

    private boolean containsEnglishTechnical(String value) {
        String v = " " + cleanTechnicalText(value).toLowerCase(Locale.ROOT)
                .replace('\n', ' ') + " ";
        String[] bad = new String[]{
                " the ", " and ", " with ", " when ", " should ", " stored ",
                " working solution ", " original package ", " minimum ", " defines ",
                " processing ", " explicitly ", " before ", " protected ", " darkness ",
                " oxidation ", " later use ", " replace ", " guaranteed ", " reached ",
                " direct sun ", " air access ", " unopened ", " opened concentrate ",
                " prepared ", " manufacturer states ", " depending on ", " once opened ",
                " use once ", " discard ", " recommended ", " per litre ", " per liter ",
                " rolls ", " sheets ", " developer ", " full tightly ", " half full "
        };
        for (String word : bad) if (v.contains(word)) return true;
        return false;
    }

    private String safeItalianTechnical(String value) {
        String v = cleanTechnicalText(value);
        return v.isEmpty() || containsEnglishTechnical(v) ? "" : v;
    }

    private boolean sameTechnicalText(String a, String b) {
        String aa = cleanTechnicalText(a).replaceAll("\\s+", " ").trim();
        String bb = cleanTechnicalText(b).replaceAll("\\s+", " ").trim();
        return !aa.isEmpty() && aa.equalsIgnoreCase(bb);
    }

    private void appendTech(StringBuilder out, String label, String value) {
        String v = safeItalianTechnical(value);
        if (v.isEmpty()) return;
        if (out.length() > 0) out.append("\n");
        out.append(label).append(": ").append(v);
    }

    private void appendTechRaw(StringBuilder out, String label, String value) {
        String v = cleanTechnicalText(value);
        if (v.isEmpty()) return;
        if (out.length() > 0) out.append("\n");
        out.append(label).append(": ").append(v);
    }

    private String prettyProfileValue'''
s, n = pat.subn(lambda _m: rep, s, count=1)
if n != 1:
    raise SystemExit('v0.3.5 appendTech replacement failed')

# Existing inventory may have persisted the old English manufacturer preparation.
# Replace it with Italian only when it is empty, equal to the raw DB text, or is
# clearly English. A genuine user-entered Italian override keeps priority.
old = '''        String instructions = p.stockInstructions;
        if ((instructions == null || instructions.trim().isEmpty()) && preparation != null && !preparation.trim().isEmpty())
            instructions = preparation.trim();'''
new = '''        String instructions = p.stockInstructions;
        String preparationIt = chemicalTechnicalPreparationIt(p.name);
        if (!preparationIt.isEmpty() &&
                (instructions == null || instructions.trim().isEmpty() ||
                        sameTechnicalText(instructions, preparation) || containsEnglishTechnical(instructions))) {
            instructions = preparationIt;
        } else if ((instructions == null || instructions.trim().isEmpty()) && preparation != null && !preparation.trim().isEmpty()) {
            instructions = preparation.trim();
        }'''
if old not in s:
    raise SystemExit('v0.3.5 applyDeveloperProfile instruction marker missing')
s = s.replace(old, new, 1)

# The edit field itself gets the same migration guard, so an already-installed
# v0.3.4 inventory does not keep displaying the persisted English sentence.
old = '''        EditText instructions = edit(p.stockInstructions == null ? "" : p.stockInstructions,
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);'''
new = '''        String prepForDisplay = cleanTechnicalText(p.stockInstructions);
        String prepItForDisplay = chemicalTechnicalPreparationIt(p.name);
        String prepRawForDisplay = chemicalTechnicalRawPreparation(p.name);
        if (!prepItForDisplay.isEmpty() &&
                (prepForDisplay.isEmpty() || sameTechnicalText(prepForDisplay, prepRawForDisplay) ||
                        containsEnglishTechnical(prepForDisplay))) {
            prepForDisplay = prepItForDisplay;
        }
        EditText instructions = edit(prepForDisplay,
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);'''
if old not in s:
    raise SystemExit('v0.3.5 edit preparation marker missing')
s = s.replace(old, new, 1)
s = s.replace('fieldBlock("PREPARAZIONE STOCK", instructions)',
              'fieldBlock("PREPARAZIONE / SOLUZIONE STOCK", instructions)', 1)

# Replace the misleading blank "duration after opening" field. Official shelf
# lives remain in the single technical card; the numeric field is only an
# optional personal override and is labelled accordingly.
pat = re.compile(r'''        EditText expiry = edit\(p\.expiryDays > 0 \? String\.valueOf\(p\.expiryDays\) : "",\n                InputType\.TYPE_CLASS_NUMBER\);\n        box\.addView\(fieldBlock\("DURATA DOPO APERTURA \(giorni\)", expiry\)\);\n\n        String technical = chemicalTechnicalSummaryIt\(p\.name\);\n        if \(!technical\.isEmpty\(\)\) \{.*?\n        \}\n''', re.S)
rep = r'''        String technical = chemicalTechnicalSummaryIt(p.name);
        if (!technical.isEmpty()) {
            TextView technicalView = label(technical, 13, WHITE, false);
            technicalView.setPadding(dp(10), dp(10), dp(10), dp(10));
            technicalView.setBackground(bg(CARD, 10, BORDER, 1));
            box.addView(fieldBlock("SCHEDA TECNICA · PRODUTTORE", technicalView));
        }

        EditText expiry = edit(p.expiryDays > 0 ? String.valueOf(p.expiryDays) : "",
                InputType.TYPE_CLASS_NUMBER);
        box.addView(fieldBlock("SCADENZA LOCALE PERSONALIZZATA (giorni)", expiry));
'''
s, n = pat.subn(lambda _m: rep, s, count=1)
if n != 1:
    raise SystemExit('v0.3.5 duration/edit technical block replacement failed')

# Normalize any escaped newline before a value is rendered in the unified result
# card. MDC content is not changed; this only affects display formatting.
old = '''    private void addUnifiedChemicalField(LinearLayout parent, String title, String value) {
        if (value == null || value.trim().isEmpty()) return;
        TextView h = label(title, 11, MUTED, true);
        h.setPadding(0, dp(8), 0, dp(3));
        parent.addView(h);
        parent.addView(label(value.trim(), 15, WHITE, false));
    }'''
new = '''    private void addUnifiedChemicalField(LinearLayout parent, String title, String value) {
        String clean = cleanTechnicalText(value);
        if (clean.isEmpty()) return;
        TextView h = label(title, 11, MUTED, true);
        h.setPadding(0, dp(8), 0, dp(3));
        parent.addView(h);
        parent.addView(label(clean, 15, WHITE, false));
    }'''
if old not in s:
    raise SystemExit('v0.3.5 unified field marker missing')
s = s.replace(old, new, 1)

# Force fresh corrected SQLite on upgrade from v0.3.4.
m = Path('combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
ms = m.read_text(encoding='utf-8')
if 'mdc_offline_darkroom_v034.sqlite' not in ms:
    raise SystemExit('v0.3.5 expected v034 database filename after base build')
ms = ms.replace('mdc_offline_darkroom_v034.sqlite', 'mdc_offline_darkroom_v035.sqlite', 1)
m.write_text(ms, encoding='utf-8')

# Source-level acceptance guards for the exact regressions visible in screenshots.
if 'DURATA DOPO APERTURA (giorni)' in s:
    raise SystemExit('old misleading duration label still present')
if 'SCADENZA LOCALE PERSONALIZZATA (giorni)' not in s:
    raise SystemExit('new local expiry label missing')
if 'SCHEDA TECNICA · PRODUTTORE' not in s:
    raise SystemExit('technical card label missing')
if 'out.append("\\n")' not in s:
    raise SystemExit('real Java newline append missing')

p.write_text(s, encoding='utf-8')
print('v0.3.5 duration + strict Italian + newline UI fix applied')
