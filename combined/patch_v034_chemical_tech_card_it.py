#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# v0.3.3 introduced developerTechnicalSummary(). Replace it with one Italian
# technical reader that supports both film developers and auxiliary chemistry.
pat = re.compile(r'''    private String developerTechnicalSummary\(String name\) \{.*?\n    \}\n\n    private void appendTech''', re.S)
rep = r'''    private String chemicalTechnicalSummaryIt(String name) {
        SQLiteDatabase db = MdcOfflineStore.database();
        if (db == null || name == null || name.trim().isEmpty()) return "";

        String canonical = FullCatalogStore.canonicalDeveloper(name);
        if (canonical != null) {
            try (Cursor c = db.rawQuery(
                    "SELECT pr.manufacturer,pr.physical_state_it,pr.preparation_it,pr.reuse_instructions_it,pr.capacity_it," +
                    "pr.shelf_life_unopened_it,pr.shelf_life_opened_it,pr.shelf_life_stock_it,pr.shelf_life_working_it," +
                    "pr.storage_notes_it,pr.notes_it," +
                    "(SELECT s.source_title FROM developer_profile_sources s WHERE s.developer_norm=pr.developer_norm AND s.source_kind='MANUFACTURER' ORDER BY s.checked_at DESC LIMIT 1)," +
                    "(SELECT s.source_date FROM developer_profile_sources s WHERE s.developer_norm=pr.developer_norm AND s.source_kind='MANUFACTURER' ORDER BY s.checked_at DESC LIMIT 1) " +
                    "FROM developer_profiles pr JOIN developers d ON d.norm_name=pr.developer_norm WHERE d.name=? COLLATE NOCASE LIMIT 1",
                    new String[]{canonical})) {
                if (c.moveToFirst()) {
                    StringBuilder out = new StringBuilder();
                    appendTech(out, "Produttore", c.getString(0));
                    appendTech(out, "Forma", c.getString(1));
                    appendTech(out, "Preparazione", c.getString(2));
                    appendTech(out, "Riutilizzo", c.getString(3));
                    appendTech(out, "Capacità", c.getString(4));
                    appendTech(out, "Durata confezione", c.getString(5));
                    appendTech(out, "Dopo apertura", c.getString(6));
                    appendTech(out, "Durata stock", c.getString(7));
                    appendTech(out, "Durata soluzione di lavoro", c.getString(8));
                    appendTech(out, "Conservazione", c.getString(9));
                    appendTech(out, "Note", c.getString(10));
                    String source = c.getString(11);
                    String date = c.getString(12);
                    if (source != null && !source.trim().isEmpty()) {
                        if (date != null && !date.trim().isEmpty()) source += " · " + date.trim();
                        appendTech(out, "Fonte tecnica", source);
                    }
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
                "storage_notes_it,notes_it,source_title,source_date FROM auxiliary_chemical_profiles WHERE norm_name=? LIMIT 1",
                new String[]{n})) {
            if (!c.moveToFirst()) return "";
            StringBuilder out = new StringBuilder();
            appendTech(out, "Produttore", c.getString(0));
            appendTech(out, "Tipo", c.getString(1));
            appendTech(out, "Forma", c.getString(2));
            appendTech(out, "Preparazione", c.getString(3));
            appendTech(out, "Capacità", c.getString(4));
            appendTech(out, "Durata confezione", c.getString(5));
            appendTech(out, "Dopo apertura", c.getString(6));
            appendTech(out, "Durata stock", c.getString(7));
            appendTech(out, "Durata soluzione di lavoro", c.getString(8));
            appendTech(out, "Conservazione", c.getString(9));
            appendTech(out, "Note", c.getString(10));
            String source = c.getString(11);
            String date = c.getString(12);
            if (source != null && !source.trim().isEmpty()) {
                if (date != null && !date.trim().isEmpty()) source += " · " + date.trim();
                appendTech(out, "Fonte tecnica", source);
            }
            return out.toString();
        } catch (Throwable ignored) { return ""; }
    }

    private String normalizeTechnicalName(String value) {
        if (value == null) return "";
        String n = java.text.Normalizer.normalize(value, java.text.Normalizer.Form.NFD)
                .replaceAll("\\p{M}+", "").toLowerCase(Locale.ROOT);
        n = n.replaceAll("[^a-z0-9+]+", " ").trim().replaceAll("\\s+", " ");
        return n;
    }

    private void appendTech'''
s, n = pat.subn(lambda _m: rep, s, count=1)
if n != 1:
    raise SystemExit('v0.3.4 technical summary replacement failed')

# v0.3.3 inserted two calls to developerTechnicalSummary: details + edit.
if s.count('developerTechnicalSummary(p.name)') != 2:
    raise SystemExit('v0.3.4 expected exactly two v0.3.3 technical summary calls')
s = s.replace('developerTechnicalSummary(p.name)', 'chemicalTechnicalSummaryIt(p.name)')
s = s.replace('DATI PRODUTTORE\\n', 'SCHEDA TECNICA\\n')
s = s.replace('DATI PRODUTTORE (database)', 'SCHEDA TECNICA (database)')

# Replace development result so MDC recipe + technical product information are
# two sections in ONE visual card, never two competing cards/sources.
pat = re.compile(r'''    private void showDevelopmentResult\(DevTimeEngine\.Result result,.*?\n    \}\n\n    private void renderFilmCapacity''', re.S)
rep = r'''    private void showDevelopmentResult(DevTimeEngine.Result result,
                                       Tank tank, int rolls,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix) {
        filmResultBox.removeAllViews();

        LinearLayout unified = new LinearLayout(this);
        unified.setOrientation(LinearLayout.VERTICAL);
        unified.setPadding(dp(18), dp(16), dp(18), dp(16));
        unified.setBackground(bg(CARD, 13, BORDER, 1));
        unified.addView(label("RIVELATORE · RICETTA + SCHEDA TECNICA", 15, WHITE, true));
        unified.addView(space(10));

        unified.addView(label("COMBINAZIONE PELLICOLA / RIVELATORE", 12, MUTED, true));
        if (!result.found) {
            addUnifiedChemicalField(unified, "TEMPO JOBO CPE2", "Tempo non disponibile");
            addUnifiedChemicalField(unified, "MASSIVE DEV CHART", result.diagnostic);
        } else {
            addUnifiedChemicalField(unified, "TEMPO JOBO CPE2", result.finalDisplay());
            addUnifiedChemicalField(unified, "DATO MDC ORIGINALE",
                    result.baseDisplay() + " @ " + fmtTemp(result.baseTemperature) +
                            " · ISO " + result.sourceIso + " · " +
                            ("120".equals(result.format) ? "120" : "35 mm"));
            String conversion = result.temperatureConverted
                    ? "Temperatura compensata a " + fmtTemp(result.targetTemperature)
                    : "Temperatura: dato originale";
            conversion += "\nJOBO CPE2: rotazione continua, adattamento −15%";
            addUnifiedChemicalField(unified, "ADATTAMENTI", conversion);
            addUnifiedChemicalField(unified, "FONTE COMBINAZIONE",
                    result.sourceName + "\n" + result.sourceFilm + " · " +
                            result.sourceDeveloper + " · " + result.sourceDilution);
            if (result.warning != null && !result.warning.isEmpty())
                addUnifiedChemicalField(unified, "ATTENZIONE", result.warning);
        }
        addUnifiedChemicalField(unified, "BAGNO RIVELATORE",
                dev.name + "\n" + formatMix(devMix, tank.rotaryMl));

        unified.addView(space(8));
        unified.addView(label("SCHEDA TECNICA DEL PRODOTTO", 12, MUTED, true));
        String technical = chemicalTechnicalSummaryIt(dev.name);
        if (technical.isEmpty()) {
            addUnifiedChemicalField(unified, "DATI TECNICI",
                    "Scheda italiana non ancora verificata per questo prodotto. Nessun dato viene inventato.");
        } else {
            addUnifiedChemicalField(unified, "DATI TECNICI", technical);
        }

        filmResultBox.addView(unified);
        filmResultBox.addView(space(10));
        resultLine(filmResultBox, "TANK", tank.name + " · volume rotazione " + tank.rotaryMl + " ml");
        resultLine(filmResultBox, "ARRESTO", formatMix(stopMix, tank.rotaryMl));
        resultLine(filmResultBox, "FISSAGGIO", formatMix(fixMix, tank.rotaryMl));

        filmCapacityBox = new LinearLayout(this);
        filmCapacityBox.setOrientation(LinearLayout.VERTICAL);
        filmResultBox.addView(label("RIUTILIZZO BAGNI", 15, WHITE, true));
        filmResultBox.addView(space(8));
        filmResultBox.addView(filmCapacityBox);
        renderFilmCapacity(dev, stop, fix, tank.rotaryMl);

        Button register = actionButton("REGISTRA QUESTO SVILUPPO", BURGUNDY);
        register.setOnClickListener(v -> {
            registerFilmUse(dev, tank.rotaryMl, rolls);
            registerFilmUse(stop, tank.rotaryMl, rolls);
            registerFilmUse(fix, tank.rotaryMl, rolls);
            renderFilmCapacity(dev, stop, fix, tank.rotaryMl);
            toast(rolls + (rolls == 1 ? " rullo registrato." : " rulli registrati."));
        });
        filmResultBox.addView(register);
        filmResultBox.addView(space(9));
        Button fresh = smallButton("NUOVO BAGNO / AZZERA CONTATORE");
        fresh.setOnClickListener(v -> {
            resetFilmBath(dev, tank.rotaryMl);
            resetFilmBath(stop, tank.rotaryMl);
            resetFilmBath(fix, tank.rotaryMl);
            renderFilmCapacity(dev, stop, fix, tank.rotaryMl);
            toast("Contatori del bagno azzerati.");
        });
        filmResultBox.addView(fresh);
        filmResultBox.addView(space(20));
    }

    private void addUnifiedChemicalField(LinearLayout parent, String title, String value) {
        if (value == null || value.trim().isEmpty()) return;
        TextView h = label(title, 11, MUTED, true);
        h.setPadding(0, dp(8), 0, dp(3));
        parent.addView(h);
        parent.addView(label(value.trim(), 15, WHITE, false));
    }

    private void renderFilmCapacity'''
s, n = pat.subn(lambda _m: rep, s, count=1)
if n != 1:
    raise SystemExit('v0.3.4 unified development card replacement failed')

# Paper developer result remains one existing RIVELATORE card; append technical
# data inside that same card rather than creating a second card.
needle = '        resultLine(paperResultBox, "RIVELATORE", devDilution + " · " + formatMix(devMix, volume));'
if needle not in s:
    raise SystemExit('v0.3.4 paper developer result marker missing')
repl = '''        String paperTech = chemicalTechnicalSummaryIt(dev.name);\n        String paperDevText = devDilution + " · " + formatMix(devMix, volume);\n        if (!paperTech.isEmpty()) paperDevText += "\\n\\nSCHEDA TECNICA\\n" + paperTech;\n        resultLine(paperResultBox, "RIVELATORE", paperDevText);'''
s = s.replace(needle, repl, 1)

# Force the enriched SQLite asset to be recopied on upgrade from v0.3.3.
m = Path('combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
ms = m.read_text(encoding='utf-8')
if 'mdc_offline_darkroom_v033.sqlite' not in ms:
    raise SystemExit('v0.3.4 expected v033 database filename after base build')
ms = ms.replace('mdc_offline_darkroom_v033.sqlite', 'mdc_offline_darkroom_v034.sqlite', 1)
m.write_text(ms, encoding='utf-8')

p.write_text(s, encoding='utf-8')
print('v0.3.4 unified Italian chemical technical card applied')
