#!/usr/bin/env python3
from pathlib import Path
import re

p=Path('combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s=p.read_text(encoding='utf-8')

# ---------------------------------------------------------------------------
# v0.3.6 rule requested by the user:
# - ONE storage condition: full, tightly closed bottle with minimum headspace
# - liquid product: opened concentrate shelf life
# - powder product: prepared stock shelf life
# - NEVER use 1+X working-solution life for inventory expiration
# ---------------------------------------------------------------------------

# Replace v0.3.5 technical summary so the visible duration is the operational
# stock/concentrate value only. Other technical fields remain in the same card.
pat=re.compile(r'''    private String chemicalTechnicalSummaryIt\(String name\) \{.*?\n    \}\n\n    private String chemicalTechnicalPreparationIt''',re.S)
rep=r'''    private String chemicalTechnicalSummaryIt(String name) {
        SQLiteDatabase db = MdcOfflineStore.database();
        if (db == null || name == null || name.trim().isEmpty()) return "";

        String canonical = FullCatalogStore.canonicalDeveloper(name);
        if (canonical != null) {
            try (Cursor c = db.rawQuery(
                    "SELECT pr.manufacturer,pr.physical_state_it,pr.preparation_it,pr.reuse_instructions_it,pr.capacity_it," +
                    "pr.operational_life_kind,pr.operational_life_it,pr.operational_life_condition_it," +
                    "pr.storage_notes_it,pr.notes_it,pr.operational_source_kind " +
                    "FROM developer_profiles pr JOIN developers d ON d.norm_name=pr.developer_norm WHERE d.name=? COLLATE NOCASE LIMIT 1",
                    new String[]{canonical})) {
                if (c.moveToFirst()) {
                    StringBuilder out = new StringBuilder();
                    appendTechRaw(out, "Produttore", c.getString(0));
                    appendTech(out, "Forma", c.getString(1));
                    appendTech(out, "Preparazione", c.getString(2));
                    appendTech(out, "Riutilizzo", c.getString(3));
                    appendTech(out, "Capacità", c.getString(4));
                    appendOperationalDuration(out, c.getString(5), c.getString(6), c.getString(7));
                    appendTech(out, "Conservazione", c.getString(8));
                    appendTech(out, "Note", c.getString(9));
                    appendTechRaw(out, "Fonte durata", operationalSourceLabel(c.getString(10)));
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
                "operational_life_kind,operational_life_it,operational_life_condition_it," +
                "storage_notes_it,notes_it,operational_source_kind " +
                "FROM auxiliary_chemical_profiles WHERE norm_name=? LIMIT 1",
                new String[]{n})) {
            if (!c.moveToFirst()) return "";
            StringBuilder out = new StringBuilder();
            appendTechRaw(out, "Produttore", c.getString(0));
            appendTech(out, "Tipo", c.getString(1));
            appendTech(out, "Forma", c.getString(2));
            appendTech(out, "Preparazione", c.getString(3));
            appendTech(out, "Capacità", c.getString(4));
            appendOperationalDuration(out, c.getString(5), c.getString(6), c.getString(7));
            appendTech(out, "Conservazione", c.getString(8));
            appendTech(out, "Note", c.getString(9));
            appendTechRaw(out, "Fonte durata", operationalSourceLabel(c.getString(10)));
            return out.toString();
        } catch (Throwable ignored) { return ""; }
    }

    private void appendOperationalDuration(StringBuilder out, String kind, String value, String condition) {
        String v = cleanTechnicalText(value);
        if (v.isEmpty()) return;
        String label = "STOCK_PREPARATO".equals(kind)
                ? "Durata stock preparato · bottiglia piena"
                : "Durata concentrato aperto · bottiglia piena";
        appendTechRaw(out, label, v);
        String c = cleanTechnicalText(condition);
        if (!c.isEmpty()) appendTechRaw(out, "Condizione di conservazione usata", c);
    }

    private String operationalSourceLabel(String kind) {
        if (kind == null || kind.trim().isEmpty()) return "";
        if ("MANUFACTURER".equals(kind)) return "Produttore";
        if ("TECHNICAL_DATASHEET".equals(kind)) return "Scheda tecnica";
        if ("TECHNICAL_GUIDE".equals(kind)) return "Guida tecnica";
        if ("TECHNICAL_RETAILER".equals(kind)) return "Fonte tecnica secondaria";
        return "Fonte tecnica";
    }

    private String chemicalTechnicalPreparationIt'''
s,n=pat.subn(lambda _m:rep,s,count=1)
if n!=1: raise SystemExit('v0.3.6 technical summary replacement failed')

# Operational life object + lookup. It intentionally reads only the dedicated
# v0.3.6 columns, so working-solution shelf life can never leak into expiry.
marker='    private String normalizeTechnicalName(String value) {'
if marker not in s: raise SystemExit('v0.3.6 operational helper marker missing')
helpers=r'''    private static final class OperationalLifeInfo {
        final String kind, text, condition, sourceKind, sourceTitle, sourceUrl;
        final int months, days, hours;
        OperationalLifeInfo(String kind, String text, int months, int days, int hours,
                            String condition, String sourceKind, String sourceTitle, String sourceUrl) {
            this.kind = kind == null ? "" : kind;
            this.text = text == null ? "" : text;
            this.months = months;
            this.days = days;
            this.hours = hours;
            this.condition = condition == null ? "" : condition;
            this.sourceKind = sourceKind == null ? "" : sourceKind;
            this.sourceTitle = sourceTitle == null ? "" : sourceTitle;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
        boolean calculable() { return months > 0 || days > 0 || hours > 0; }
        boolean stock() { return "STOCK_PREPARATO".equals(kind); }
    }

    private OperationalLifeInfo operationalLife(String name) {
        SQLiteDatabase db = MdcOfflineStore.database();
        if (db == null || name == null || name.trim().isEmpty()) return null;
        String canonical = FullCatalogStore.canonicalDeveloper(name);
        if (canonical != null) {
            try (Cursor c = db.rawQuery(
                    "SELECT pr.operational_life_kind,pr.operational_life_it," +
                    "COALESCE(pr.operational_life_months,0),COALESCE(pr.operational_life_days,0),COALESCE(pr.operational_life_hours,0)," +
                    "pr.operational_life_condition_it,pr.operational_source_kind,pr.operational_source_title,pr.operational_source_url " +
                    "FROM developer_profiles pr JOIN developers d ON d.norm_name=pr.developer_norm WHERE d.name=? COLLATE NOCASE LIMIT 1",
                    new String[]{canonical})) {
                if (c.moveToFirst() && c.getString(1) != null && !c.getString(1).trim().isEmpty())
                    return new OperationalLifeInfo(c.getString(0), c.getString(1), c.getInt(2), c.getInt(3), c.getInt(4),
                            c.getString(5), c.getString(6), c.getString(7), c.getString(8));
            } catch (Throwable ignored) {}
        }
        String n = normalizeTechnicalName(name);
        if ("adostop eco".equals(n)) n = "adox adostop eco";
        if ("foma adostop eco".equals(n)) n = "adox adostop eco";
        if ("foma fomatol lqn".equals(n)) n = "fomatol lqn";
        if ("foma fix".equals(n)) n = "fomafix";
        if ("foma fotonal".equals(n)) n = "fotonal";
        try (Cursor c = db.rawQuery(
                "SELECT operational_life_kind,operational_life_it,COALESCE(operational_life_months,0)," +
                "COALESCE(operational_life_days,0),COALESCE(operational_life_hours,0),operational_life_condition_it," +
                "operational_source_kind,operational_source_title,operational_source_url " +
                "FROM auxiliary_chemical_profiles WHERE norm_name=? LIMIT 1", new String[]{n})) {
            if (c.moveToFirst() && c.getString(1) != null && !c.getString(1).trim().isEmpty())
                return new OperationalLifeInfo(c.getString(0), c.getString(1), c.getInt(2), c.getInt(3), c.getInt(4),
                        c.getString(5), c.getString(6), c.getString(7), c.getString(8));
        } catch (Throwable ignored) {}
        return null;
    }

    private String operationalDateTitle(OperationalLifeInfo info) {
        return info != null && info.stock() ? "DATA PREPARAZIONE STOCK" : "DATA APERTURA CONCENTRATO";
    }

    private String operationalDurationTitle(OperationalLifeInfo info) {
        return info != null && info.stock()
                ? "DURATA STOCK · BOTTIGLIA PIENA"
                : "DURATA CONCENTRATO APERTO · BOTTIGLIA PIENA";
    }

    private String operationalExpiryTitle(OperationalLifeInfo info) {
        return info != null && info.stock() ? "SCADENZA STOCK" : "SCADENZA CONCENTRATO";
    }

    private String operationalExpiryValue(OperationalLifeInfo info, long startMillis) {
        if (info == null || info.text.trim().isEmpty()) return "Durata tecnica non disponibile.";
        if (startMillis <= 0) return "Inserisci la data per calcolare la scadenza.";
        if (!info.calculable()) return "Durata: " + cleanTechnicalText(info.text) + "\nScadenza automatica non calcolabile da un intervallo non numerico.";
        Calendar c = Calendar.getInstance();
        c.setTimeInMillis(startMillis);
        if (info.months > 0) c.add(Calendar.MONTH, info.months);
        if (info.days > 0) c.add(Calendar.DAY_OF_MONTH, info.days);
        if (info.hours > 0) c.add(Calendar.HOUR_OF_DAY, info.hours);
        return new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY).format(c.getTime());
    }

'''
s=s.replace(marker,helpers+marker,1)

# Date picker title while adding a chemical is now semantically exact.
old='''        picker.setTitle(p.stockPrep ? "Data preparazione stock" : "Data apertura");'''
new='''        OperationalLifeInfo life = operationalLife(p.name);
        picker.setTitle(life != null && life.stock() ? "Data preparazione stock" : "Data apertura concentrato");'''
if old not in s: raise SystemExit('v0.3.6 date picker marker missing')
s=s.replace(old,new,1)

# Product details: use only the operational duration and auto-calculated expiry;
# ignore the legacy custom expiry field without deleting it from saved data.
pat=re.compile(r'''    private void showProductDetails\(String name\) \{.*?\n    \}\n\n    private void showEditProductDialog''',re.S)
rep=r'''    private void showProductDetails(String name) {
        Product p = findProduct(name);
        if (p == null) return;
        long opened = prefs.getLong("opened_" + key(name), 0L);
        OperationalLifeInfo life = operationalLife(p.name);
        StringBuilder msg = new StringBuilder();
        if (opened > 0) {
            msg.append(operationalDateTitle(life)).append(": ")
                    .append(new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY).format(new Date(opened)));
        } else {
            msg.append(operationalDateTitle(life)).append(": non impostata");
        }
        if (life != null) {
            msg.append("\n\n").append(operationalDurationTitle(life)).append(":\n")
                    .append(cleanTechnicalText(life.text));
            msg.append("\n\n").append(operationalExpiryTitle(life)).append(": ")
                    .append(operationalExpiryValue(life, opened));
        }
        String technical = chemicalTechnicalSummaryIt(p.name);
        if (!technical.isEmpty()) msg.append("\n\nSCHEDA TECNICA\n").append(technical);
        msg.append("\n\n").append(reuseDescription(p));
        appendStoredBathStatus(msg, p);

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle(name)
                .setMessage(msg.toString())
                .setNegativeButton("CHIUDI", null)
                .setNeutralButton("MODIFICA", (d, w) -> showEditProductDialog(name))
                .setPositiveButton("ELIMINA", (d, w) -> {
                    removeFromInventory(name);
                    showProducts();
                })
                .create();
        dialog.show();
    }

    private void showEditProductDialog'''
s,n=pat.subn(lambda _m:rep,s,count=1)
if n!=1: raise SystemExit('v0.3.6 product details replacement failed')

# Edit screen: dynamic date title, read-only operational duration and expiry,
# then the technical card. Remove the old custom-expiry input completely.
old='''        EditText date = edit(opened > 0 ? df.format(new Date(opened)) : "",
                InputType.TYPE_CLASS_DATETIME);
        box.addView(fieldBlock("DATA APERTURA / PREPARAZIONE", date));'''
new='''        OperationalLifeInfo lifeInfo = operationalLife(p.name);
        EditText date = edit(opened > 0 ? df.format(new Date(opened)) : "",
                InputType.TYPE_CLASS_DATETIME);
        box.addView(fieldBlock(operationalDateTitle(lifeInfo), date));

        if (lifeInfo != null) {
            TextView durationView = label(cleanTechnicalText(lifeInfo.text), 14, WHITE, false);
            durationView.setPadding(dp(10), dp(10), dp(10), dp(10));
            durationView.setBackground(bg(CARD, 10, BORDER, 1));
            box.addView(fieldBlock(operationalDurationTitle(lifeInfo), durationView));

            TextView expiryView = label(operationalExpiryValue(lifeInfo, opened), 15, WHITE, true);
            expiryView.setPadding(dp(10), dp(10), dp(10), dp(10));
            expiryView.setBackground(bg(CARD, 10, BORDER, 1));
            box.addView(fieldBlock(operationalExpiryTitle(lifeInfo), expiryView));
        }'''
if old not in s: raise SystemExit('v0.3.6 edit date marker missing')
s=s.replace(old,new,1)

pat=re.compile(r'''\n        EditText expiry = edit\(p\.expiryDays > 0 \? String\.valueOf\(p\.expiryDays\) : "",\n                InputType\.TYPE_CLASS_NUMBER\);\n        box\.addView\(fieldBlock\("SCADENZA LOCALE PERSONALIZZATA \(giorni\)", expiry\)\);''')
s,n=pat.subn('',s,count=1)
if n!=1: raise SystemExit('v0.3.6 custom expiry field removal failed')

old='''                    int exp = parseIntOrMinus(expiry.getText().toString());'''
new='''                    int exp = p.expiryDays; // legacy value preserved but no longer used for operational expiry'''
if old not in s: raise SystemExit('v0.3.6 expiry save marker missing')
s=s.replace(old,new,1)

# Force the corrected operational schema to be recopied on upgrade.
m=Path('combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
ms=m.read_text(encoding='utf-8')
if 'mdc_offline_darkroom_v035.sqlite' not in ms: raise SystemExit('v0.3.6 expected v035 DB filename')
ms=ms.replace('mdc_offline_darkroom_v035.sqlite','mdc_offline_darkroom_v036.sqlite',1)
m.write_text(ms,encoding='utf-8')

# Acceptance guards.
for forbidden in ('SCADENZA LOCALE PERSONALIZZATA (giorni)','DURATA DOPO APERTURA (giorni)'):
    if forbidden in s: raise SystemExit('legacy expiry UI still present: '+forbidden)
for required in ('DURATA STOCK · BOTTIGLIA PIENA','DURATA CONCENTRATO APERTO · BOTTIGLIA PIENA',
                 'SCADENZA STOCK','SCADENZA CONCENTRATO','operationalExpiryValue','operational_life_kind'):
    if required not in s: raise SystemExit('v0.3.6 required marker missing: '+required)
if 'Durata soluzione di lavoro' in s[s.index('private String chemicalTechnicalSummaryIt'):s.index('private String chemicalTechnicalPreparationIt')]:
    raise SystemExit('1+X working duration still visible in operational technical summary')

p.write_text(s,encoding='utf-8')
print('v0.3.6 full-bottle stock/concentrate automatic expiry UI applied')
