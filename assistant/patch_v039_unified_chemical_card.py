from pathlib import Path
import re

# v0.3.9
# - Massive Dev Chart resta autorita' esclusiva per combinazione film/dev
# - chemical_specs.sqlite aggiunge SOLO fatti tecnici del prodotto
# - MDC + scheda tecnica del rivelatore sono mostrati in UN SOLO RIQUADRO
# - preparazione in italiano disponibile anche durante l'aggiunta del prodotto

p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# Inizializza anche il DB tecnico offline, senza rendere il suo eventuale errore
# bloccante per il motore MDC.
needle = '        MdcOfflineStore.init(getApplicationContext());'
if needle not in s:
    raise SystemExit('MdcOfflineStore init marker missing')
if 'ChemicalTechnicalStore.init(getApplicationContext());' not in s:
    s = s.replace(needle, needle + '\n        ChemicalTechnicalStore.init(getApplicationContext());', 1)

# Preparazione prodotto: usa la scheda tecnica per mostrare istruzioni italiane
# verificate. Non modifica mai diluizioni o tempi MDC.
pattern = re.compile(r'''    private void startProductAddFlow\(Product p\) \{.*?\n    \}\n\n    private void askOpeningDate''', re.S)
replacement = r'''    private void startProductAddFlow(Product p) {
        ChemicalTechnicalStore.Sheet tech = ChemicalTechnicalStore.lookup(this, p.name);
        String instructions = tech != null && tech.hasTechnicalDetails()
                ? tech.preparationIt : "";
        boolean preparedProduct = p.stockPrep || isPowderPreparation(tech);

        if (!preparedProduct && (instructions == null || instructions.isEmpty())) {
            askOpeningDate(p);
            return;
        }

        String body = instructions != null && !instructions.isEmpty()
                ? instructions
                : (usefulInstruction(p.stockInstructions)
                ? p.stockInstructions
                : "Segui le istruzioni della confezione prima di confermare la preparazione.");
        if (tech != null && tech.hasTechnicalDetails() && !tech.sourceName.isEmpty()) {
            body += "\n\nFonte tecnica: " + tech.sourceName;
            if (!tech.sourceDate.isEmpty()) body += " · " + tech.sourceDate;
        }

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle(preparedProduct ? "Preparazione prodotto" : "Informazioni di preparazione")
                .setMessage(body)
                .setNegativeButton("ANNULLA", null)
                .setNeutralButton("APRI FONTE", null)
                .setPositiveButton(preparedProduct ? "PREPARATO" : "CONTINUA",
                        (d, w) -> askOpeningDate(p))
                .create();
        dialog.setOnShowListener(d -> {
            Button src = dialog.getButton(AlertDialog.BUTTON_NEUTRAL);
            String url = tech != null ? tech.sourceUrl : p.sourceUrl;
            if (url == null || url.isEmpty()) src.setVisibility(View.GONE);
            else src.setOnClickListener(v -> openUrl(url));
        });
        dialog.show();
    }

    private boolean isPowderPreparation(ChemicalTechnicalStore.Sheet tech) {
        return tech != null && tech.hasTechnicalDetails() &&
                tech.formIt.toLowerCase(Locale.ROOT).contains("polvere") &&
                tech.preparationIt != null && !tech.preparationIt.isEmpty();
    }

    private void askOpeningDate'''
s, n = pattern.subn(lambda _m: replacement, s, count=1)
if n != 1:
    raise SystemExit('startProductAddFlow replacement failed')

# Data picker: per i prodotti in polvere con preparazione verificata, la data e'
# correttamente presentata come data di preparazione anche se il vecchio Product
# non possiede il flag stockPrep.
old = '        picker.setTitle(p.stockPrep ? "Data preparazione stock" : "Data apertura");'
new = '''        ChemicalTechnicalStore.Sheet techDate = ChemicalTechnicalStore.lookup(this, p.name);
        picker.setTitle((p.stockPrep || isPowderPreparation(techDate))
                ? "Data preparazione" : "Data apertura");'''
if old not in s:
    raise SystemExit('date picker title marker missing')
s = s.replace(old, new, 1)

# Scheda prodotto: mostra i dati tecnici ufficiali in italiano. L'eventuale
# expiryDays storico/manuale resta chiaramente marcato come dato locale e non
# viene confuso con la durata ufficiale.
pattern = re.compile(r'''    private void showProductDetails\(String name\) \{.*?\n    \}\n\n    private void showEditProductDialog''', re.S)
replacement = r'''    private void showProductDetails(String name) {
        Product p = findProduct(name);
        if (p == null) return;
        long opened = prefs.getLong("opened_" + key(name), 0L);
        StringBuilder msg = new StringBuilder();
        if (opened > 0) {
            msg.append("Data apertura/preparazione: ")
                    .append(new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY)
                            .format(new Date(opened)));
        }
        if (p.expiryDays > 0 && opened > 0) {
            long expires = opened + p.expiryDays * 86400000L;
            msg.append("\nScadenza locale modificabile: ")
                    .append(new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY)
                            .format(new Date(expires)));
        }

        ChemicalTechnicalStore.Sheet tech = ChemicalTechnicalStore.lookup(this, p.name);
        if (tech != null && tech.hasTechnicalDetails()) {
            appendTechnicalText(msg, tech);
        } else {
            msg.append("\n\nSCHEDA TECNICA\n")
                    .append("Dati tecnici italiani non ancora verificati per questo prodotto. ")
                    .append("Nessun dato viene inventato.");
        }

        msg.append("\n\nRIUTILIZZO NELL'APP\n").append(reuseDescription(p));
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

    private void appendTechnicalText(StringBuilder msg, ChemicalTechnicalStore.Sheet t) {
        msg.append("\n\nSCHEDA TECNICA · fonte produttore");
        appendTextField(msg, "Produttore", t.manufacturer);
        appendTextField(msg, "Tipo", t.productTypeIt);
        appendTextField(msg, "Forma", t.formIt);
        appendTextField(msg, "Preparazione", t.preparationIt);
        appendTextField(msg, "Durata confezione", t.shelfUnopenedIt);
        appendTextField(msg, "Dopo apertura", t.shelfOpenedIt);
        appendTextField(msg, "Durata stock", t.shelfStockIt);
        appendTextField(msg, "Durata soluzione di lavoro", t.shelfWorkingIt);
        appendTextField(msg, "Conservazione", t.storageIt);
        appendTextField(msg, "Capacità", t.capacityIt);
        appendTextField(msg, "Note", t.notesIt);
        String source = t.sourceName;
        if (!t.sourceDate.isEmpty()) source += (source.isEmpty() ? "" : " · ") + t.sourceDate;
        appendTextField(msg, "Fonte tecnica", source);
    }

    private void appendTextField(StringBuilder msg, String labelText, String value) {
        if (value == null || value.trim().isEmpty()) return;
        msg.append("\n\n").append(labelText).append(":\n").append(value.trim());
    }

    private void showEditProductDialog'''
s, n = pattern.subn(lambda _m: replacement, s, count=1)
if n != 1:
    raise SystemExit('showProductDetails replacement failed')

# Sostituisce l'intero rendering del risultato sviluppo. Il dato MDC e la
# scheda tecnica non sono due card: sono due SEZIONI dentro lo stesso riquadro.
pattern = re.compile(r'''    private void showDevelopmentResult\(DevTimeEngine\.Result result,.*?\n    \}\n\n    private void renderFilmCapacity''', re.S)
replacement = r'''    private void showDevelopmentResult(DevTimeEngine.Result result,
                                       Tank tank, int rolls,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix) {
        filmResultBox.removeAllViews();

        LinearLayout unified = new LinearLayout(this);
        unified.setOrientation(LinearLayout.VERTICAL);
        unified.setPadding(dp(18), dp(16), dp(18), dp(16));
        unified.setBackground(bg(CARD, 13, BORDER, 1));
        unified.addView(label("RIVELATORE · RICETTA + SCHEDA TECNICA", 15, WHITE, true));
        unified.addView(space(12));

        // SEZIONE 1: combinazione. Fonte esclusiva: Massive Dev Chart / motore tempi.
        unified.addView(label("COMBINAZIONE DI SVILUPPO", 12, MUTED, true));
        unified.addView(space(5));
        if (!result.found) {
            addUnifiedField(unified, "TEMPO JOBO CPE2", "Tempo non disponibile");
            addUnifiedField(unified, "MASSIVE DEV CHART", result.diagnostic);
        } else {
            addUnifiedField(unified, "TEMPO JOBO CPE2", result.finalDisplay());
            addUnifiedField(unified, "DATO MDC ORIGINALE",
                    result.baseDisplay() + " @ " + fmtTemp(result.baseTemperature) +
                            " · ISO " + result.sourceIso + " · " +
                            ("120".equals(result.format) ? "120" : "35 mm"));
            String conversion = result.temperatureConverted
                    ? "Temperatura compensata a " + fmtTemp(result.targetTemperature)
                    : "Temperatura: dato originale";
            conversion += "\nJOBO CPE2: rotazione continua, adattamento −15%";
            addUnifiedField(unified, "ADATTAMENTI", conversion);
            addUnifiedField(unified, "FONTE COMBINAZIONE",
                    result.sourceName + "\n" + result.sourceFilm + " · " +
                            result.sourceDeveloper + " · " + result.sourceDilution);
            if (result.warning != null && !result.warning.isEmpty())
                addUnifiedField(unified, "ATTENZIONE", result.warning);
        }
        addUnifiedField(unified, "BAGNO RIVELATORE",
                dev.name + "\n" + formatMix(devMix, tank.rotaryMl));

        // SEZIONE 2: fatti generali del prodotto. DB separato, mai usato per
        // cambiare tempo/ISO/diluizione della combinazione sopra.
        unified.addView(space(8));
        unified.addView(label("SCHEDA TECNICA DEL RIVELATORE", 12, MUTED, true));
        unified.addView(space(5));
        ChemicalTechnicalStore.Sheet tech = ChemicalTechnicalStore.lookup(this, dev.name);
        if (tech == null || !tech.hasTechnicalDetails()) {
            addUnifiedField(unified, "DATI TECNICI",
                    "Scheda italiana non ancora verificata. Nessun dato tecnico viene inventato.");
        } else {
            addUnifiedTechField(unified, "PRODUTTORE", tech.manufacturer);
            addUnifiedTechField(unified, "TIPO / FORMA", joinNonEmpty(tech.productTypeIt, tech.formIt));
            addUnifiedTechField(unified, "PREPARAZIONE", tech.preparationIt);
            addUnifiedTechField(unified, "DURATA CONFEZIONE", tech.shelfUnopenedIt);
            addUnifiedTechField(unified, "DOPO APERTURA", tech.shelfOpenedIt);
            addUnifiedTechField(unified, "DURATA STOCK", tech.shelfStockIt);
            addUnifiedTechField(unified, "DURATA SOLUZIONE DI LAVORO", tech.shelfWorkingIt);
            addUnifiedTechField(unified, "CONSERVAZIONE", tech.storageIt);
            addUnifiedTechField(unified, "CAPACITÀ", tech.capacityIt);
            addUnifiedTechField(unified, "NOTE", tech.notesIt);
            String techSource = tech.sourceName;
            if (!tech.sourceDate.isEmpty())
                techSource += (techSource.isEmpty() ? "" : " · ") + tech.sourceDate;
            addUnifiedTechField(unified, "FONTE TECNICA", techSource);
        }
        filmResultBox.addView(unified);
        filmResultBox.addView(space(10));

        // Gli altri bagni restano operativi ma NON duplicano la card del rivelatore.
        resultLine(filmResultBox, "TANK", tank.name + " · volume rotazione " + tank.rotaryMl + " ml");
        resultLine(filmResultBox, "ARRESTO", formatMix(stopMix, tank.rotaryMl));
        resultLine(filmResultBox, "FISSAGGIO", formatMix(fixMix, tank.rotaryMl));

        filmCapacityBox = new LinearLayout(this);
        filmCapacityBox.setOrientation(LinearLayout.VERTICAL);
        filmResultBox.addView(label("RIUTILIZZO BAGNI", 15, WHITE, true));
        filmResultBox.addView(space(8));
        filmResultBox.addView(filmCapacityBox);
        renderFilmCapacity(dev, stop, fix, tank.rotaryMl);

        Button register = actionButton("REGISTRA UTILIZZO BAGNI", BURGUNDY);
        register.setOnClickListener(v -> {
            registerFilmUse(dev, tank.rotaryMl, rolls);
            registerFilmUse(stop, tank.rotaryMl, rolls);
            registerFilmUse(fix, tank.rotaryMl, rolls);
            renderFilmCapacity(dev, stop, fix, tank.rotaryMl);
            toast(rolls + (rolls == 1
                    ? " rullo aggiunto ai contatori dei bagni."
                    : " rulli aggiunti ai contatori dei bagni."));
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

    private void addUnifiedField(LinearLayout parent, String title, String value) {
        if (value == null || value.trim().isEmpty()) return;
        TextView h = label(title, 11, MUTED, true);
        h.setPadding(0, dp(8), 0, dp(3));
        parent.addView(h);
        parent.addView(label(value.trim(), 15, WHITE, false));
    }

    private void addUnifiedTechField(LinearLayout parent, String title, String value) {
        addUnifiedField(parent, title, value);
    }

    private String joinNonEmpty(String a, String b) {
        boolean ha = a != null && !a.trim().isEmpty();
        boolean hb = b != null && !b.trim().isEmpty();
        if (ha && hb) return a.trim() + "\n" + b.trim();
        if (ha) return a.trim();
        return hb ? b.trim() : "";
    }

    private void renderFilmCapacity'''
s, n = pattern.subn(lambda _m: replacement, s, count=1)
if n != 1:
    raise SystemExit('showDevelopmentResult unified-card replacement failed')

p.write_text(s, encoding='utf-8')
print('v0.3.9 unified MDC + technical chemical card applied')
