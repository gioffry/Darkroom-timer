from pathlib import Path
import re

# v0.3.5
# - selezione formato pellicola dai formati realmente presenti nel DB MDC (35/120)
# - database offline parallelo, curato, di bagni di arresto e fissaggi
# - nessuna ricerca web runtime
# - diluizione stop/fix scelta automaticamente in base al contesto film/carta

# ---------------------------------------------------------------------------
# 1) MdcOfflineStore: formati realmente disponibili per la pellicola.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
s = p.read_text(encoding='utf-8')
marker = '''    static boolean isKnownDeveloper(String name) {'''
helper = r'''    static String[] formatsForFilm(String filmName) {
        if (!isReady() || filmName == null) return new String[0];
        boolean has35 = false;
        boolean has120 = false;
        SQLiteDatabase db = helper.getReadableDatabase();
        try (Cursor c = db.rawQuery(
                "SELECT time35,time120 FROM times WHERE film_norm=?",
                new String[]{norm(stripFormat(filmName))})) {
            while (c.moveToNext()) {
                if (!has35 && hasTime(c.getString(0))) has35 = true;
                if (!has120 && hasTime(c.getString(1))) has120 = true;
                if (has35 && has120) break;
            }
        }
        List<String> out = new ArrayList<>();
        if (has35) out.add("35");
        if (has120) out.add("120");
        return out.toArray(new String[0]);
    }

'''
if marker not in s:
    raise SystemExit('MdcOfflineStore isKnownDeveloper marker missing')
s = s.replace(marker, helper + marker, 1)
p.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# 2) Activity: catalogo curato stop/fix + selezione formato.
# ---------------------------------------------------------------------------
p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

# Campo formato.
old = '''    private Spinner tankSpinner;
    private Spinner developerSpinner;'''
new = '''    private Spinner tankSpinner;
    private Spinner formatSpinner;
    private Spinner developerSpinner;'''
if old not in s:
    raise SystemExit('formatSpinner field marker missing')
s = s.replace(old, new, 1)

# Catalogo parallelo. I prodotti sono selezionati tra referenze correnti rilevate
# su MacoDirect/Fotomatica e dati tecnici da schede produttore/rivenditore.
insert_after = '''    private final FilmStock[] fallbackFilms = new FilmStock[]{'''
idx = s.find(insert_after)
if idx < 0:
    raise SystemExit('fallbackFilms marker missing')
curated = r'''    private final Product[] curatedAuxChemistry = new Product[]{
            // BAGNI DI ARRESTO (max 10)
            new Product("Adox Adostop ECO", ROLE_STOP, false,
                    new String[]{"1+19"}, new String[]{"1+19"}, "1+19", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, 3.0),
            new Product("Adox Adostop ECO P", ROLE_STOP, true,
                    new String[]{"stock"}, new String[]{"stock"}, "stock",
                    "Sciogli la confezione in acqua per preparare 5 litri di bagno di arresto pronto all'uso.",
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, 20, 3.0),
            new Product("Ilford Ilfostop", ROLE_STOP, false,
                    new String[]{"1+19"}, new String[]{"1+19"}, "1+19", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, 15, 3.0),
            new Product("Rollei RCS Citro Stop", ROLE_STOP, false,
                    new String[]{"1+19"}, new String[]{"1+19"}, "1+19", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("MACO Eco Citrostop", ROLE_STOP, false,
                    new String[]{"1+19"}, new String[]{"1+19"}, "1+19", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Compard Stop Bath 60%", ROLE_STOP, false,
                    new String[]{"1+19"}, new String[]{"1+19"}, "1+19", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Fomacitro", ROLE_STOP, false,
                    new String[]{"1+19"}, new String[]{"1+19"}, "1+19", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Bellini ECOSTOP", ROLE_STOP, false,
                    new String[]{"1+19"}, new String[]{"1+19"}, "1+19", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, 15, -1),
            new Product("Bellini INDEXSTOP", ROLE_STOP, false,
                    new String[]{"1+19"}, new String[]{"1+19"}, "1+19", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Bellini STOP (Acetic Acid)", ROLE_STOP, false,
                    new String[]{"1+19"}, new String[]{"1+19"}, "1+19", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),

            // FISSAGGI (max 10)
            new Product("Compard Fix Ag Plus", ROLE_FIX, false,
                    new String[]{"1+5"}, new String[]{"1+9"}, "1+5", null,
                    90, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Ilford Rapid Fixer", ROLE_FIX, false,
                    new String[]{"1+4"}, new String[]{"1+9"}, "1+4", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, 24, 4.0),
            new Product("Ilford Hypam", ROLE_FIX, false,
                    new String[]{"1+4"}, new String[]{"1+9"}, "1+4", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, 24, 4.0),
            new Product("Fomafix", ROLE_FIX, false,
                    new String[]{"1+5"}, new String[]{"1+5"}, "1+5", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, 17, -1),
            new Product("Adox Adofix Plus", ROLE_FIX, false,
                    new String[]{"1+4"}, new String[]{"1+9"}, "1+4", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Rollei RXA Fix Acid", ROLE_FIX, false,
                    new String[]{"1+7"}, new String[]{"1+9"}, "1+7", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Rollei RXN Fix Neutral", ROLE_FIX, false,
                    new String[]{"1+4"}, new String[]{"1+9"}, "1+4", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Bellini FX100", ROLE_FIX, false,
                    new String[]{"1+4"}, new String[]{"1+9"}, "1+4", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, 15, 2.5),
            new Product("MACO Ecofix", ROLE_FIX, false,
                    new String[]{"1+4"}, new String[]{"1+4"}, "1+4", null,
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Bellini FX5 Fixer & Hardener", ROLE_FIX, true,
                    new String[]{"stock"}, new String[0], "stock",
                    "Prepara le parti A+B con acqua fino a ottenere 1 litro di soluzione pronta all'uso, seguendo le quantità indicate sulla confezione.",
                    -1, "", ChemistrySpecEngine.REUSE_REUSABLE, 30, -1)
    };

'''
s = s[:idx] + curated + s[idx:]

# onCreate: riparazione leggera e sicura solo dei prodotti stop/fix già in magazzino.
old = '''        MdcOfflineStore.init(getApplicationContext());
        showHome();
        ensureOfflineDatabase();'''
new = '''        MdcOfflineStore.init(getApplicationContext());
        repairCuratedAuxInventory();
        showHome();
        ensureOfflineDatabase();'''
if old not in s:
    raise SystemExit('onCreate v035 marker missing')
s = s.replace(old, new, 1)

# Sostituisci interamente il popup AGGIUNGI: prima si sceglie il tipo, poi si cerca
# soltanto nel database pertinente.
start = s.find('    private void showAddProductDialog() {')
end = s.find('    private void enrichProductThenAdd(', start)
if start < 0 or end < 0:
    raise SystemExit('showAddProductDialog boundaries missing')
new_dialog = r'''    private void showAddProductDialog() {
        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setPadding(dp(18), dp(8), dp(18), 0);

        String[] typeLabels = new String[]{
                "Rivelatore pellicola", "Rivelatore carta", "Arresto", "Fissaggio"
        };
        final int[] typeRoles = new int[]{ROLE_FILM_DEV, ROLE_PAPER_DEV, ROLE_STOP, ROLE_FIX};
        Spinner typeSpinner = spinner(typeLabels);
        wrap.addView(fieldBlock("TIPO", typeSpinner));

        AutoCompleteTextView search = new AutoCompleteTextView(this);
        search.setThreshold(3);
        search.setHint("Scrivi almeno 3 lettere…");
        search.setSingleLine(true);
        styleInput(search);
        wrap.addView(search);

        TextView status = label("Scegli il tipo e scrivi almeno 3 lettere.", 12, MUTED, false);
        status.setPadding(dp(4), dp(8), dp(4), 0);
        wrap.addView(status);

        List<String> suggestions = new ArrayList<>();
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this,
                android.R.layout.simple_dropdown_item_1line, suggestions);
        search.setAdapter(adapter);
        Map<String, OnlineCatalogSearch.SearchResult> mdc = new HashMap<>();
        final Runnable[] pending = new Runnable[1];
        final int[] generation = new int[]{0};
        final String[] chosen = new String[1];

        Runnable reset = () -> {
            generation[0]++;
            if (pending[0] != null) handler.removeCallbacks(pending[0]);
            chosen[0] = null;
            mdc.clear();
            adapter.clear();
            search.setText("", false);
            status.setText("Scrivi almeno 3 lettere.");
        };
        typeSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) { reset.run(); }
        });

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int st, int c, int a) {}
            @Override public void onTextChanged(CharSequence s, int st, int before, int count) {}
            @Override public void afterTextChanged(Editable e) {
                String q = e.toString().trim();
                generation[0]++;
                int g = generation[0];
                if (pending[0] != null) handler.removeCallbacks(pending[0]);
                chosen[0] = null;
                mdc.clear();
                if (q.length() < 3) {
                    adapter.clear();
                    status.setText("Scrivi almeno 3 lettere.");
                    return;
                }
                int role = typeRoles[Math.max(0, Math.min(typeSpinner.getSelectedItemPosition(), typeRoles.length - 1))];
                if (role != ROLE_FILM_DEV) {
                    List<String> local = localProductMatchesForRole(q, role);
                    replaceSuggestions(adapter, local);
                    status.setText(local.isEmpty() ? "Nessun prodotto trovato." :
                            local.size() + " prodotti trovati. Tocca un prodotto.");
                    if (!local.isEmpty()) search.showDropDown();
                    return;
                }

                status.setText("Cerco nel database Digitaltruth…");
                pending[0] = () -> new Thread(() -> {
                    List<OnlineCatalogSearch.SearchResult> results = OnlineCatalogSearch.searchChemicals(q);
                    runOnUiThread(() -> {
                        if (g != generation[0] ||
                                !q.equalsIgnoreCase(search.getText().toString().trim())) return;
                        List<String> names = new ArrayList<>();
                        mdc.clear();
                        for (OnlineCatalogSearch.SearchResult r : results) {
                            if (r.title == null || r.title.trim().length() < 3) continue;
                            names.add(r.title);
                            mdc.put(r.title.toLowerCase(Locale.ROOT), r);
                        }
                        replaceSuggestions(adapter, names);
                        status.setText(names.isEmpty() ? "Nessun rivelatore trovato." :
                                names.size() + " rivelatori trovati. Tocca un prodotto.");
                        if (!names.isEmpty()) search.showDropDown();
                    });
                }).start();
                handler.postDelayed(pending[0], 250);
            }
        });

        search.setOnItemClickListener((parent, view, position, id) ->
                chosen[0] = String.valueOf(parent.getItemAtPosition(position)));

        ScrollView addProductScroll = new ScrollView(this);
        addProductScroll.setFillViewport(false);
        addProductScroll.addView(wrap);
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Aggiungi prodotto")
                .setView(addProductScroll)
                .setNegativeButton("ANNULLA", null)
                .setPositiveButton("AGGIUNGI", null)
                .create();

        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String name = chosen[0];
                    if (name == null || name.trim().isEmpty()) {
                        toast("Seleziona uno dei prodotti proposti.");
                        return;
                    }
                    int role = typeRoles[Math.max(0, Math.min(typeSpinner.getSelectedItemPosition(), typeRoles.length - 1))];
                    Product local = findProduct(name);
                    OnlineCatalogSearch.SearchResult r = mdc.get(name.toLowerCase(Locale.ROOT));
                    if (role == ROLE_FILM_DEV) {
                        if (local == null && r == null) {
                            toast("Seleziona un rivelatore dal database.");
                            return;
                        }
                        dialog.dismiss();
                        enrichProductThenAdd(local, r);
                        return;
                    }
                    if (local == null || (local.roles & role) == 0) {
                        toast("Seleziona un prodotto della categoria scelta.");
                        return;
                    }
                    dialog.dismiss();
                    startProductAddFlow(local);
                }));
        dialog.show();
    }

'''
s = s[:start] + new_dialog + s[end:]

# Nel flusso pellicola aggiungi FORMATO subito dopo la ricerca pellicola.
needle = '''        page.addView(filmSearchStatus);

        isoField = edit("", InputType.TYPE_CLASS_NUMBER);'''
repl = '''        page.addView(filmSearchStatus);

        formatSpinner = spinner(new String[]{"Seleziona prima la pellicola"});
        page.addView(fieldBlock("FORMATO", formatSpinner));

        isoField = edit("", InputType.TYPE_CLASS_NUMBER);'''
if needle not in s:
    raise SystemExit('film format insertion marker missing')
s = s.replace(needle, repl, 1)

# Listener formato: aggiorna la pellicola selezionata e le tank compatibili.
needle = '''        rollsSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) { updateCompatibleTanks(); }
        });'''
repl = '''        formatSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                if (selectedFilm == null || formatSpinner.getSelectedItem() == null) return;
                String label = String.valueOf(formatSpinner.getSelectedItem());
                String f = label.startsWith("120") ? "120" : label.startsWith("35") ? "35" : "";
                if (f.isEmpty()) return;
                selectedFilm = new FilmStock(selectedFilm.name, selectedFilm.nominalIso, f, selectedFilm.sourceUrl);
                updateCompatibleTanks();
            }
        });
        rollsSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) { updateCompatibleTanks(); }
        });'''
if needle not in s:
    raise SystemExit('format listener marker missing')
s = s.replace(needle, repl, 1)

# La selezione della pellicola non apre più un dialog 35/120: popola lo spinner dai dati DB.
pattern = re.compile(r'''    private void finishOnlineFilmSelection\(OnlineCatalogSearch\.FilmData fd\) \{.*?\n    \}\n\n    private void selectFilm\(FilmStock f\) \{.*?\n    \}\n\n    private void updateCompatibleTanks\(\) \{''', re.S)
replacement = r'''    private void finishOnlineFilmSelection(OnlineCatalogSearch.FilmData fd) {
        if (fd == null) return;
        String name = cleanSearchTitle(fd.name);
        selectFilm(new FilmStock(name, fd.iso, "", fd.sourceUrl));
    }

    private void selectFilm(FilmStock f) {
        selectedFilm = f;
        filmField.setText(f.name, false);
        isoField.setText(f.nominalIso > 0 ? String.valueOf(f.nominalIso) : "");
        filmSearchStatus.setText("Pellicola presente nel database offline.");

        String[] formats = MdcOfflineStore.formatsForFilm(f.name);
        if (formats.length == 0) {
            setSpinnerItems(formatSpinner, new String[]{"Formato non disponibile"});
            selectedFilm = new FilmStock(f.name, f.nominalIso, "", f.sourceUrl);
            updateCompatibleTanks();
            return;
        }
        List<String> labels = new ArrayList<>();
        int selected = 0;
        for (int i = 0; i < formats.length; i++) {
            String x = formats[i];
            labels.add("120".equals(x) ? "120" : "35 mm");
            if (x.equals(f.format)) selected = i;
        }
        setSpinnerItems(formatSpinner, labels.toArray(new String[0]));
        formatSpinner.setSelection(selected);
        String chosenFormat = formats[selected];
        selectedFilm = new FilmStock(f.name, f.nominalIso, chosenFormat, f.sourceUrl);
        updateCompatibleTanks();
    }

    private void updateCompatibleTanks() {'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('finish/select film replacement failed')

# Tank: senza formato non si procede.
needle = '''        if (selectedFilm == null) {
            setSpinnerItems(tankSpinner, new String[]{"Seleziona prima la pellicola"});
            return;
        }'''
repl = '''        if (selectedFilm == null) {
            setSpinnerItems(tankSpinner, new String[]{"Seleziona prima la pellicola"});
            return;
        }
        if (selectedFilm.format == null || selectedFilm.format.isEmpty()) {
            setSpinnerItems(tankSpinner, new String[]{"Seleziona il formato"});
            return;
        }'''
if needle not in s:
    raise SystemExit('tank format guard marker missing')
s = s.replace(needle, repl, 1)

# Diluizione stop/fix contestuale, film e carta.
s = s.replace('''        double[] stopMix = mix(tank.rotaryMl, selectedStop.workingDilution);
        double[] fixMix = mix(tank.rotaryMl, selectedFix.workingDilution);''',
'''        String stopDilution = filmAuxDilution(selectedStop);
        String fixDilution = filmAuxDilution(selectedFix);
        double[] stopMix = mix(tank.rotaryMl, stopDilution);
        double[] fixMix = mix(tank.rotaryMl, fixDilution);''', 1)

s = s.replace('''        double[] stopMix = mix(volume, stop.workingDilution);
        double[] fixMix = mix(volume, fix.workingDilution);''',
'''        String stopDilution = paperAuxDilution(stop);
        String fixDilution = paperAuxDilution(fix);
        double[] stopMix = mix(volume, stopDilution);
        double[] fixMix = mix(volume, fixDilution);''', 1)
s = s.replace('''        resultLine(paperResultBox, "ARRESTO", stop.workingDilution + " · " + formatMix(stopMix, volume));
        resultLine(paperResultBox, "FISSAGGIO", fix.workingDilution + " · " + formatMix(fixMix, volume));''',
'''        resultLine(paperResultBox, "ARRESTO", stopDilution + " · " + formatMix(stopMix, volume));
        resultLine(paperResultBox, "FISSAGGIO", fixDilution + " · " + formatMix(fixMix, volume));''', 1)

# Helper catalogo / diluizioni / riparazione magazzino prima della sezione persistenza.
marker = '''    // ---------------------------------------------------------------------
    // PERSISTENZA MAGAZZINO
    // ---------------------------------------------------------------------'''
helpers = r'''    private List<String> localProductMatchesForRole(String q, int role) {
        String needle = q == null ? "" : q.toLowerCase(Locale.ROOT).trim();
        LinkedHashSet<String> out = new LinkedHashSet<>();
        for (Product p : curatedAuxChemistry) {
            if ((p.roles & role) != 0 && p.name.toLowerCase(Locale.ROOT).contains(needle)) out.add(p.name);
        }
        for (Product p : fallbackProducts) {
            if ((p.roles & role) != 0 && p.name.toLowerCase(Locale.ROOT).contains(needle)) out.add(p.name);
        }
        return new ArrayList<>(out);
    }

    private Product curatedAuxByName(String name) {
        if (name == null) return null;
        for (Product p : curatedAuxChemistry)
            if (p.name.equalsIgnoreCase(name.trim())) return p;
        return null;
    }

    private String filmAuxDilution(Product p) {
        if (p == null) return null;
        if (p.filmDilutions != null && p.filmDilutions.length > 0) return p.filmDilutions[0];
        return p.workingDilution;
    }

    private String paperAuxDilution(Product p) {
        if (p == null) return null;
        if (p.paperDilutions != null && p.paperDilutions.length > 0) return p.paperDilutions[0];
        return p.workingDilution;
    }

    private void repairCuratedAuxInventory() {
        Set<String> inv = getInventory();
        if (inv.isEmpty()) return;
        for (String name : inv) {
            Product curated = curatedAuxByName(name);
            if (curated == null) continue;
            saveProductMetadata(curated);
        }
    }

'''
if marker not in s:
    raise SystemExit('persistence helper marker missing')
s = s.replace(marker, helpers + marker, 1)

# findProduct: dopo il riconoscimento MDC, usa catalogo curato prima dei vecchi metadati.
needle = '''        String canonical = MdcOfflineStore.canonicalDeveloperName(name.trim());
        if (canonical != null) return offlineDeveloperProduct(canonical);
        Product saved = loadSavedProduct(name.trim());'''
repl = '''        String canonical = MdcOfflineStore.canonicalDeveloperName(name.trim());
        if (canonical != null) return offlineDeveloperProduct(canonical);
        Product curated = curatedAuxByName(name.trim());
        if (curated != null) {
            Product savedCurated = loadSavedProduct(curated.name);
            return savedCurated != null ? savedCurated : curated;
        }
        Product saved = loadSavedProduct(name.trim());'''
if needle not in s:
    raise SystemExit('findProduct curated marker missing')
s = s.replace(needle, repl, 1)

# Testo finale coerente: nessuna ricerca online.
s = s.replace('Ricerca online dopo 3 lettere.', 'Cerca nel database dopo 3 lettere.')
s = s.replace('Cerco online…', 'Cerco nel database…')
s = s.replace('Recupero dati, preparazione e capacità online…', 'Recupero dati dal database…')
s = s.replace('Cerco online la combinazione esatta…', 'Cerco la combinazione nel database…')

p.write_text(s, encoding='utf-8')
print('v0.3.5 format selector + curated stop/fix database applied')
