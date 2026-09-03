#!/usr/bin/env python3
"""Darkroom 0.6.4: coherent filled Home navigation and chemical inventory UI."""

from pathlib import Path


HOME = Path("combined/src/main/java/it/darkroom/timer/home/HomeActivity.java")
ASSISTANT = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")


def rep(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)
    if found != count:
        raise SystemExit(f"v0.6.4 {label}: expected {count}, found {found}")
    return text.replace(old, new)


def between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    start_count = text.count(start)
    end_count = text.count(end)
    if start_count != 1 or end_count < 1:
        raise SystemExit(
            f"v0.6.4 {label}: start={start_count}, end={end_count}"
        )
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[:i] + replacement + text[j:]


home = HOME.read_text(encoding="utf-8")
assistant = ASSISTANT.read_text(encoding="utf-8")

if "HOME_VISUAL_064" in home and "INVENTORY_VISUAL_064" in assistant:
    print("home_inventory_064=ALREADY_APPLIED")
    raise SystemExit(0)
if "UI_POLISH_063" not in Path(
    "combined/src/main/java/it/darkroom/timer/MainActivity.java"
).read_text(encoding="utf-8"):
    raise SystemExit("v0.6.4: exact v0.6.3 source not recognized")
if 'new HomeCard("PRODOTTI CHIMICI", ICON_CHEM, false)' not in home:
    raise SystemExit("v0.6.4: expected v0.6.3 Home not recognized")
if 'private void showProducts()' not in assistant or 'setTitle("Aggiungi prodotto")' not in assistant:
    raise SystemExit("v0.6.4: expected v0.6.3 inventory not recognized")

home_before = home
assistant_before = assistant

# ---------------------------------------------------------------------------
# HOME — every navigation card is a filled, uniquely coloured action.
# ---------------------------------------------------------------------------

home = rep(
    home,
    "public final class HomeActivity extends Activity {\n",
    "public final class HomeActivity extends Activity {\n"
    "    // HOME_VISUAL_064 — filled, colour-coded navigation; destinations unchanged.\n",
    "Home marker",
)
home = rep(
    home,
    "    private static final int BORDER = Color.rgb(164, 139, 105);\n",
    "    private static final int BORDER = Color.rgb(164, 139, 105);\n"
    "    private static final int HOME_CHEMICAL = Color.rgb(116, 49, 55);\n"
    "    private static final int HOME_FILM = Color.rgb(43, 91, 106);\n"
    "    private static final int HOME_LARGE_FORMAT = Color.rgb(91, 70, 113);\n"
    "    private static final int HOME_PRINT_BATHS = Color.rgb(45, 99, 72);\n"
    "    private static final int HOME_TIMER = Color.rgb(118, 84, 48);\n"
    "    private static final int HOME_MAINTENANCE = Color.rgb(63, 70, 77);\n",
    "Home colours",
)
home = rep(
    home,
    'new HomeCard("PRODOTTI CHIMICI", ICON_CHEM, false)',
    'new HomeCard("PRODOTTI CHIMICI", ICON_CHEM, HOME_CHEMICAL, false)',
    "chemical Home action",
)
home = rep(
    home,
    'new HomeCard("SVILUPPO PELLICOLA", ICON_FILM, false)',
    'new HomeCard("SVILUPPO PELLICOLA", ICON_FILM, HOME_FILM, false)',
    "film Home action",
)
home = rep(
    home,
    'new HomeCard("GRANDE FORMATO", ICON_CHASSIS, false)',
    'new HomeCard("GRANDE FORMATO", ICON_CHASSIS, HOME_LARGE_FORMAT, false)',
    "large-format Home action",
)
home = rep(
    home,
    'new HomeCard("BAGNI STAMPA", ICON_TRAY, false)',
    'new HomeCard("BAGNI STAMPA", ICON_TRAY, HOME_PRINT_BATHS, false)',
    "print-baths Home action",
)
home = rep(
    home,
    'new HomeCard("TIMER STAMPA", ICON_TIMER, false)',
    'new HomeCard("TIMER STAMPA", ICON_TIMER, HOME_TIMER, false)',
    "Timer Home action",
)
home = rep(
    home,
    'new HomeCard("USO E MANUTENZIONE", ICON_WRENCH, true)',
    'new HomeCard("USO E MANUTENZIONE", ICON_WRENCH, HOME_MAINTENANCE, true)',
    "maintenance Home action",
)
home = rep(
    home,
    '''    private GradientDrawable cardBg(boolean secondary) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(secondary ? Color.rgb(15, 16, 17) : CARD);
        g.setCornerRadius(dp(13));
        g.setStroke(dp(1), BORDER);
        return g;
    }

    private final class HomeCard extends LinearLayout {
        HomeCard(String text, int icon, boolean secondary) {
''',
    '''    private GradientDrawable cardBg(int fill) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(dp(13));
        g.setStroke(dp(1), Color.argb(170, 235, 210, 174));
        return g;
    }

    private final class HomeCard extends LinearLayout {
        HomeCard(String text, int icon, int fill, boolean secondary) {
''',
    "Home filled-card helper",
)
home = rep(
    home,
    "            setBackground(cardBg(secondary));\n",
    "            setBackground(cardBg(fill));\n",
    "Home card fill",
)

# ---------------------------------------------------------------------------
# CHEMICAL INVENTORY — custom, coherent dialogs and action/information hierarchy.
# ---------------------------------------------------------------------------

assistant = rep(
    assistant,
    "import android.app.DatePickerDialog;\n",
    "import android.app.DatePickerDialog;\nimport android.app.Dialog;\n",
    "Dialog import",
)
assistant = rep(
    assistant,
    "public class AssistantActivityV2 extends Activity {\n",
    "public class AssistantActivityV2 extends Activity {\n"
    "    // INVENTORY_VISUAL_064 — chemical-family UI only; inventory behaviour unchanged.\n",
    "inventory marker",
)
assistant = rep(
    assistant,
    "    private static final int BORDER = Color.rgb(67, 67, 67);\n",
    "    private static final int BORDER = Color.rgb(67, 67, 67);\n"
    "    private static final int CHEM_ACCENT = Color.rgb(151, 64, 70);\n"
    "    private static final int CHEM_FILL = Color.rgb(78, 32, 36);\n"
    "    private static final int CHEM_BORDER = Color.rgb(181, 103, 108);\n"
    "    private static final int DELETE_ACCENT = Color.rgb(135, 47, 47);\n"
    "    private static final int NEUTRAL_ACTION = Color.rgb(58, 62, 66);\n",
    "inventory colours",
)

show_products = '''    private void showProducts() {
        currentScreen = PRODUCTS;
        LinearLayout page = page("Prodotti chimici", "Gestisci il tuo magazzino.");

        Button add = chemicalButton("＋  AGGIUNGI PRODOTTO", CHEM_ACCENT);
        add.setOnClickListener(v -> showAddProductDialog());
        page.addView(add);
        page.addView(space(24));
        TextView inventoryHeading = label("MAGAZZINO", 16, CHEM_ACCENT, true);
        page.addView(inventoryHeading);
        page.addView(space(10));

        List<String> names = new ArrayList<>(getInventory());
        Collections.sort(names, String::compareToIgnoreCase);
        if (names.isEmpty()) {
            page.addView(chemicalInformationCard(
                    "MAGAZZINO", "Nessun prodotto in magazzino."));
        } else {
            for (String name : names) {
                LinearLayout row = inventoryRow(name);
                row.setOnClickListener(v -> showProductDetails(name));
                page.addView(row);
                page.addView(space(9));
            }
        }
        page.addView(space(80));
        setContentView(scroll(page));
    }

'''
assistant = between(
    assistant,
    "    private void showProducts() {",
    "    private void showAddProductDialog() {",
    show_products,
    "products screen",
)

show_add = '''    private void showAddProductDialog() {
        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);

        String[] typeLabels = new String[]{
                "Rivelatore pellicola", "Rivelatore carta", "Arresto", "Fissaggio",
                "Imbibente", "Aiuto lavaggio", "Altra chimica"
        };
        final int[] typeRoles = new int[]{ROLE_FILM_DEV, ROLE_PAPER_DEV, ROLE_STOP, ROLE_FIX,
                ROLE_WETTING, ROLE_WASHING, ROLE_CHEMISTRY};
        Spinner typeSpinner = spinner(typeLabels);
        wrap.addView(chemicalFieldBlock("TIPO", typeSpinner));

        EditText search = edit("", InputType.TYPE_CLASS_TEXT);
        search.setHint("Scrivi almeno 3 lettere…");
        search.setSingleLine(true);
        wrap.addView(chemicalFieldBlock("CERCA PRODOTTO", search));

        TextView status = label("Scegli il tipo e scrivi almeno 3 lettere.", 12, MUTED, false);
        status.setPadding(dp(12), dp(10), dp(12), dp(10));
        status.setBackground(bg(BG, 10, CHEM_BORDER, 1));
        wrap.addView(status);
        wrap.addView(space(8));

        LinearLayout resultsBox = new LinearLayout(this);
        resultsBox.setOrientation(LinearLayout.VERTICAL);
        ScrollView resultsScroll = new ScrollView(this);
        resultsScroll.setFillViewport(false);
        resultsScroll.addView(resultsBox);
        resultsScroll.setVisibility(View.GONE);
        LinearLayout.LayoutParams resultsLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(250));
        resultsScroll.setLayoutParams(resultsLp);
        wrap.addView(resultsScroll);

        Map<String, OnlineCatalogSearch.SearchResult> mdc = new HashMap<>();
        final Runnable[] pending = new Runnable[1];
        final int[] generation = new int[]{0};
        final String[] chosen = new String[1];

        final java.util.function.Consumer<List<String>> renderResults = values -> {
            resultsBox.removeAllViews();
            if (values == null || values.isEmpty()) {
                resultsScroll.setVisibility(View.GONE);
                return;
            }
            resultsScroll.setVisibility(View.VISIBLE);
            for (String value : values) {
                LinearLayout item = inventoryRow(value);
                item.setTag("chemical-result");
                item.setOnClickListener(v -> {
                    chosen[0] = value;
                    markSelectedChemicalResult(resultsBox, item);
                    search.setText(value);
                    search.setSelection(search.getText().length());
                    status.setText("Selezionato: " + value);
                });
                resultsBox.addView(item);
                resultsBox.addView(space(8));
            }
        };

        Runnable reset = () -> {
            generation[0]++;
            if (pending[0] != null) handler.removeCallbacks(pending[0]);
            chosen[0] = null;
            mdc.clear();
            resultsBox.removeAllViews();
            resultsScroll.setVisibility(View.GONE);
            search.setText("");
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

                if (chosen[0] != null && q.equals(chosen[0])) return;
                chosen[0] = null;
                mdc.clear();
                resultsBox.removeAllViews();
                resultsScroll.setVisibility(View.GONE);

                if (q.length() < 3) {
                    status.setText("Scrivi almeno 3 lettere.");
                    return;
                }

                int role = typeRoles[Math.max(0,
                        Math.min(typeSpinner.getSelectedItemPosition(), typeRoles.length - 1))];

                if (role != ROLE_FILM_DEV) {
                    List<String> local = localProductMatchesForRole(q, role);
                    renderResults.accept(local);
                    status.setText(local.isEmpty()
                            ? "Nessun prodotto trovato."
                            : local.size() + " prodotti trovati. Tocca un prodotto.");
                    return;
                }

                status.setText("Cerco nel database Digitaltruth…");
                pending[0] = () -> new Thread(() -> {
                    List<OnlineCatalogSearch.SearchResult> results =
                            OnlineCatalogSearch.searchChemicals(q);
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
                        renderResults.accept(names);
                        status.setText(names.isEmpty()
                                ? "Nessun rivelatore trovato."
                                : names.size() + " rivelatori trovati. Tocca un prodotto.");
                    });
                }).start();
                handler.postDelayed(pending[0], 180);
            }
        });

        LinearLayout panel = chemicalDialogPanel("AGGIUNGI PRODOTTO");
        panel.addView(wrap, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        Button cancel = chemicalButton("ANNULLA", NEUTRAL_ACTION);
        Button confirm = chemicalButton("AGGIUNGI", CHEM_ACCENT);
        panel.addView(chemicalActionRow(cancel, confirm));
        Dialog dialog = presentChemicalDialog(panel, false);
        cancel.setOnClickListener(v -> dialog.dismiss());
        confirm.setOnClickListener(v -> {
            String name = chosen[0];
            if (name == null || name.trim().isEmpty()) {
                toast("Tocca prima uno dei prodotti nell'elenco.");
                return;
            }
            int role = typeRoles[Math.max(0,
                    Math.min(typeSpinner.getSelectedItemPosition(), typeRoles.length - 1))];
            Product local = findProduct(name);
            OnlineCatalogSearch.SearchResult r =
                    mdc.get(name.toLowerCase(Locale.ROOT));
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
        });
    }

'''
assistant = between(
    assistant,
    "    private void showAddProductDialog() {",
    "    private void enrichProductThenAdd(",
    show_add,
    "add-product dialog",
)

choose_type = '''    private void chooseProductTypeThenAdd(Product p) {
        String[] types = new String[]{
                "Rivelatore pellicola", "Rivelatore carta",
                "Rivelatore pellicola + carta", "Arresto", "Fissaggio"
        };
        LinearLayout panel = chemicalDialogPanel("TIPO NON RICONOSCIUTO");
        panel.addView(chemicalInformationCard("CLASSIFICAZIONE",
                "La fonte non consente di classificare il prodotto con sicurezza."));
        panel.addView(space(10));
        Dialog dialog = new Dialog(this);
        for (int i = 0; i < types.length; i++) {
            final int which = i;
            Button option = chemicalButton(types[i].toUpperCase(Locale.ITALY), CHEM_FILL);
            option.setOnClickListener(v -> {
                dialog.dismiss();
                startProductAddFlow(p.withRole(roleForType(which)));
            });
            panel.addView(option);
            panel.addView(space(7));
        }
        Button cancel = chemicalButton("ANNULLA", NEUTRAL_ACTION);
        cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel);
        presentChemicalDialog(dialog, panel, false);
    }

'''
assistant = between(
    assistant,
    "    private void chooseProductTypeThenAdd(Product p) {",
    "    private void startProductAddFlow(Product p) {",
    choose_type,
    "unknown-type dialog",
)

start_add_flow = '''    private void startProductAddFlow(Product p) {
        if (!p.stockPrep) {
            askOpeningDate(p);
            return;
        }

        String body;
        if (usefulInstruction(p.stockInstructions)) {
            body = p.stockInstructions;
        } else {
            body = "Il catalogo offline non contiene istruzioni di preparazione abbastanza dettagliate. " +
                    "Apri la fonte e verifica la confezione prima di confermare la preparazione.";
        }
        if (p.sourceUrl != null && !p.sourceUrl.isEmpty()) {
            body += "\\n\\nFonte tecnica registrata disponibile.";
        }

        LinearLayout panel = chemicalDialogPanel("PREPARAZIONE STOCK");
        panel.addView(chemicalInformationCard("ISTRUZIONI", body));
        panel.addView(space(10));
        Button cancel = chemicalButton("ANNULLA", NEUTRAL_ACTION);
        Button prepared = chemicalButton("STOCK PREPARATO", CHEM_ACCENT);
        Dialog dialog = new Dialog(this);
        if (p.sourceUrl != null && !p.sourceUrl.isEmpty()) {
            Button source = chemicalButton("APRI FONTE", CHEM_FILL);
            source.setOnClickListener(v -> openUrl(p.sourceUrl));
            panel.addView(source);
            panel.addView(space(7));
        }
        panel.addView(chemicalActionRow(cancel, prepared));
        cancel.setOnClickListener(v -> dialog.dismiss());
        prepared.setOnClickListener(v -> {
            dialog.dismiss();
            askOpeningDate(p);
        });
        presentChemicalDialog(dialog, panel, false);
    }

'''
assistant = between(
    assistant,
    "    private void startProductAddFlow(Product p) {",
    "    private void askOpeningDate(Product p) {",
    start_add_flow,
    "stock-preparation dialog",
)

show_details = '''    private void showProductDetails(String name) {
        Product p = findProduct(name);
        if (p == null) return;
        long opened = prefs.getLong("opened_" + key(name), 0L);
        OperationalLifeInfo life = operationalLife(p.name);

        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        String dateValue = opened > 0
                ? new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY).format(new Date(opened))
                : "Non impostata";
        body.addView(chemicalInformationCard(operationalDateTitle(life), dateValue));
        body.addView(space(9));
        if (life != null) {
            body.addView(chemicalInformationCard(
                    operationalDurationTitle(life), safeItalianTechnical(life.text)));
            body.addView(space(9));
            body.addView(chemicalInformationCard(
                    operationalExpiryTitle(life), operationalExpiryValue(life, opened)));
            body.addView(space(9));
        }
        String technical = chemicalTechnicalSummaryIt(p.name);
        if (!technical.isEmpty()) {
            body.addView(chemicalInformationCard("SCHEDA TECNICA", technical));
            body.addView(space(9));
        }
        StringBuilder reuse = new StringBuilder(reuseDescription(p));
        appendStoredBathStatus(reuse, p);
        body.addView(chemicalInformationCard("RIUTILIZZO E BAGNI", reuse.toString()));

        ScrollView content = new ScrollView(this);
        content.setFillViewport(false);
        content.addView(body);
        LinearLayout panel = chemicalDialogPanel(name.toUpperCase(Locale.ITALY));
        panel.addView(content, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        Button edit = chemicalButton("MODIFICA", CHEM_ACCENT);
        Button delete = chemicalButton("ELIMINA", DELETE_ACCENT);
        panel.addView(chemicalActionRow(edit, delete));
        panel.addView(space(7));
        Button close = chemicalButton("CHIUDI", NEUTRAL_ACTION);
        panel.addView(close);

        Dialog dialog = presentChemicalDialog(panel, true);
        close.setOnClickListener(v -> dialog.dismiss());
        edit.setOnClickListener(v -> {
            dialog.dismiss();
            showEditProductDialog(name);
        });
        delete.setOnClickListener(v -> {
            dialog.dismiss();
            removeFromInventory(name);
            showProducts();
        });
    }

'''
assistant = between(
    assistant,
    "    private void showProductDetails(String name) {",
    "    private void showEditProductDialog(String oldName) {",
    show_details,
    "product-detail dialog",
)

show_edit = '''    private void showEditProductDialog(String oldName) {
        Product p = findProduct(oldName);
        if (p == null) return;
        long opened = prefs.getLong("opened_" + key(oldName), 0L);
        SimpleDateFormat df = new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY);
        df.setLenient(false);

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);

        EditText name = edit(p.name, InputType.TYPE_CLASS_TEXT);
        box.addView(chemicalFieldBlock("NOME", name));
        String[] types = new String[]{"Rivelatore pellicola", "Rivelatore carta",
                "Rivelatore pellicola + carta", "Arresto", "Fissaggio",
                "Imbibente", "Aiuto lavaggio", "Altra chimica"};
        Spinner type = spinner(types);
        type.setSelection(typeIndexForRole(p.roles));
        box.addView(chemicalFieldBlock("TIPO", type));

        EditText filmDil = edit(join(p.filmDilutions), InputType.TYPE_CLASS_TEXT);
        box.addView(chemicalFieldBlock("DILUIZIONI PELLICOLA", filmDil));
        EditText paperDil = edit(join(p.paperDilutions), InputType.TYPE_CLASS_TEXT);
        box.addView(chemicalFieldBlock("DILUIZIONI CARTA", paperDil));
        EditText working = edit(p.workingDilution == null ? "" : p.workingDilution,
                InputType.TYPE_CLASS_TEXT);
        box.addView(chemicalFieldBlock("DILUIZIONE ARRESTO / FIX", working));

        String[] reuseLabels = new String[]{"Non determinato", "Monouso", "Riutilizzabile", "Soluzione fresca consigliata"};
        Spinner reuse = spinner(reuseLabels);
        reuse.setSelection(p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT ? 1 :
                p.reuseMode == ChemistrySpecEngine.REUSE_REUSABLE ? 2 :
                p.reuseMode == REUSE_FRESH_RECOMMENDED ? 3 : 0);
        box.addView(chemicalFieldBlock("RIUTILIZZO", reuse));

        EditText filmCap = edit(p.filmCapacityPerLiter > 0 ? fmt(p.filmCapacityPerLiter) : "",
                InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        box.addView(chemicalFieldBlock("CAPACITÀ PELLICOLA (rulli per litro)", filmCap));
        EditText paperCap = edit(p.paperCapacitySqMPerLiter > 0 ? fmt(p.paperCapacitySqMPerLiter) : "",
                InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        box.addView(chemicalFieldBlock("CAPACITÀ CARTA (m² per litro)", paperCap));

        String prepForDisplay = cleanTechnicalText(p.stockInstructions);
        String prepItForDisplay = chemicalTechnicalPreparationIt(p.name);
        String prepRawForDisplay = chemicalTechnicalRawPreparation(p.name);
        if (!prepItForDisplay.isEmpty() &&
                (prepForDisplay.isEmpty() || sameTechnicalText(prepForDisplay, prepRawForDisplay) ||
                        containsEnglishTechnical(prepForDisplay))) {
            prepForDisplay = prepItForDisplay;
        }
        EditText instructions = edit(prepForDisplay,
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        instructions.setMinLines(3);
        box.addView(chemicalFieldBlock("PREPARAZIONE / SOLUZIONE STOCK", instructions));

        OperationalLifeInfo lifeInfo = operationalLife(p.name);
        EditText date = edit(opened > 0 ? df.format(new Date(opened)) : "",
                InputType.TYPE_CLASS_DATETIME);
        box.addView(chemicalFieldBlock(operationalDateTitle(lifeInfo), date));

        if (lifeInfo != null) {
            box.addView(chemicalInformationCard(
                    operationalDurationTitle(lifeInfo), safeItalianTechnical(lifeInfo.text)));
            box.addView(space(9));
            box.addView(chemicalInformationCard(
                    operationalExpiryTitle(lifeInfo), operationalExpiryValue(lifeInfo, opened)));
            box.addView(space(9));
        }
        String technical = chemicalTechnicalSummaryIt(p.name);
        if (!technical.isEmpty()) {
            box.addView(chemicalInformationCard("SCHEDA TECNICA · PRODUTTORE", technical));
            box.addView(space(9));
        }

        ScrollView content = new ScrollView(this);
        content.setFillViewport(false);
        content.addView(box);
        LinearLayout panel = chemicalDialogPanel("MODIFICA PRODOTTO");
        panel.addView(content, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        Button cancel = chemicalButton("ANNULLA", NEUTRAL_ACTION);
        Button save = chemicalButton("SALVA", CHEM_ACCENT);
        panel.addView(chemicalActionRow(cancel, save));
        Dialog dialog = presentChemicalDialog(panel, true);

        cancel.setOnClickListener(v -> dialog.dismiss());
        save.setOnClickListener(v -> {
            String newName = name.getText().toString().trim();
            if (newName.isEmpty()) { toast("Inserisci il nome."); return; }
            long newOpened = opened;
            try {
                if (!date.getText().toString().trim().isEmpty())
                    newOpened = df.parse(date.getText().toString().trim()).getTime();
            } catch (Exception e) { toast("Data non valida."); return; }
            int exp = p.expiryDays;
            double fc = parseDoubleOrMinus(filmCap.getText().toString());
            double pc = parseDoubleOrMinus(paperCap.getText().toString());
            int reuseMode = reuse.getSelectedItemPosition() == 1
                    ? ChemistrySpecEngine.REUSE_ONE_SHOT
                    : reuse.getSelectedItemPosition() == 2
                    ? ChemistrySpecEngine.REUSE_REUSABLE
                    : reuse.getSelectedItemPosition() == 3
                    ? REUSE_FRESH_RECOMMENDED
                    : ChemistrySpecEngine.REUSE_UNKNOWN;
            Product edited = new Product(newName,
                    roleForType(type.getSelectedItemPosition()),
                    !instructions.getText().toString().trim().isEmpty() || p.stockPrep,
                    splitCsv(filmDil.getText().toString()),
                    splitCsv(paperDil.getText().toString()),
                    emptyToNull(working.getText().toString()),
                    emptyToNull(instructions.getText().toString()),
                    exp, p.sourceUrl, reuseMode, fc, pc);
            replaceInventoryProduct(oldName, edited, newOpened);
            dialog.dismiss();
            showProducts();
        });
    }

'''
assistant = between(
    assistant,
    "    private void showEditProductDialog(String oldName) {",
    "    // ---------------------------------------------------------------------\n    // SVILUPPO PELLICOLA",
    show_edit,
    "edit-product dialog",
)

# Product pages use the same serif/ivory title language as Home and Timer.
page_method = '''    private LinearLayout page(String title, String subtitle) {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(16), dp(14), dp(16), dp(28));
        page.setBackgroundColor(BG);
        boolean chemicalPage = "Prodotti chimici".equalsIgnoreCase(title);

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);

        TextView home = label("⌂", 25, chemicalPage ? WHITE : WHITE, true);
        home.setGravity(Gravity.CENTER);
        home.setContentDescription("Torna alla Home");
        home.setOnClickListener(v -> {
            saveCurrentUiState();
            finish();
        });
        top.addView(home, new LinearLayout.LayoutParams(dp(46), dp(46)));

        TextView h = label(title.toUpperCase(Locale.ITALY), 24, WHITE, true);
        h.setGravity(Gravity.CENTER);
        if (chemicalPage) h.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
        top.addView(h, new LinearLayout.LayoutParams(0, dp(46), 1f));

        View spacer = new View(this);
        top.addView(spacer, new LinearLayout.LayoutParams(dp(46), dp(46)));
        page.addView(top, new LinearLayout.LayoutParams(-1, dp(46)));

        if (subtitle != null && !subtitle.trim().isEmpty()) {
            TextView sub = label(subtitle, 13, MUTED, false);
            sub.setGravity(Gravity.CENTER);
            sub.setPadding(dp(8), dp(5), dp(8), dp(8));
            page.addView(sub);
        }

        View accent = new View(this);
        LinearLayout.LayoutParams ap = new LinearLayout.LayoutParams(dp(34), dp(2));
        ap.gravity = Gravity.CENTER_HORIZONTAL;
        ap.setMargins(0, dp(3), 0, dp(20));
        accent.setLayoutParams(ap);
        accent.setBackground(bg(chemicalPage ? CHEM_ACCENT : BURGUNDY_BRIGHT, 2, 0, 0));
        page.addView(accent);
        return page;
    }

'''
assistant = between(
    assistant,
    "    private LinearLayout page(String title, String subtitle) {",
    "    private View homeCard(",
    page_method,
    "chemical page header",
)

inventory_helpers = '''    private LinearLayout chemicalDialogPanel(String title) {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(16), dp(15), dp(16), dp(16));
        panel.setBackground(bg(CARD_2, 16, CHEM_BORDER, 1));
        TextView heading = label(title, 21, CHEM_ACCENT, true);
        heading.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
        heading.setPadding(dp(2), 0, dp(2), dp(13));
        panel.addView(heading);
        return panel;
    }

    private Dialog presentChemicalDialog(LinearLayout panel, boolean tall) {
        return presentChemicalDialog(new Dialog(this), panel, tall);
    }

    private Dialog presentChemicalDialog(Dialog dialog, LinearLayout panel, boolean tall) {
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        dialog.setContentView(panel);
        Window window = dialog.getWindow();
        if (window != null) window.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        window = dialog.getWindow();
        if (window != null) {
            int width = (int) (getResources().getDisplayMetrics().widthPixels * 0.94f);
            int height = tall
                    ? (int) (getResources().getDisplayMetrics().heightPixels * 0.90f)
                    : ViewGroup.LayoutParams.WRAP_CONTENT;
            window.setLayout(width, height);
        }
        return dialog;
    }

    private Button chemicalButton(String text, int color) {
        Button button = actionButton(text, color);
        button.setTextColor(WHITE);
        button.setBackground(bg(color, 10, 0, 0));
        button.setAllCaps(false);
        return button;
    }

    private LinearLayout chemicalActionRow(Button... buttons) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setPadding(0, dp(12), 0, 0);
        for (int i = 0; i < buttons.length; i++) {
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, dp(52), 1f);
            if (i > 0) params.setMargins(dp(7), 0, 0, 0);
            row.addView(buttons[i], params);
        }
        return row;
    }

    private LinearLayout chemicalFieldBlock(String labelText, View field) {
        LinearLayout block = new LinearLayout(this);
        block.setOrientation(LinearLayout.VERTICAL);
        block.setPadding(0, 0, 0, dp(12));
        TextView label = label(labelText, 12, CHEM_ACCENT, true);
        label.setPadding(dp(4), 0, 0, dp(6));
        block.addView(label);
        field.setBackground(bg(CARD, 10, CHEM_BORDER, 1));
        block.addView(field);
        return block;
    }

    private LinearLayout chemicalInformationCard(String heading, String value) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(13), dp(11), dp(13), dp(12));
        card.setBackground(bg(BG, 11, CHEM_BORDER, 1));
        TextView title = label(heading, 12, CHEM_ACCENT, true);
        card.addView(title);
        card.addView(space(5));
        TextView body = label(value == null || value.trim().isEmpty() ? "—" : value,
                14, WHITE, false);
        body.setLineSpacing(0, 1.06f);
        card.addView(body);
        return card;
    }

    private LinearLayout inventoryRow(String name) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(15), dp(10), dp(12), dp(10));
        row.setMinimumHeight(dp(58));
        row.setBackground(bg(CHEM_FILL, 10, CHEM_BORDER, 1));
        TextView product = label(name, 16, WHITE, true);
        product.setGravity(Gravity.CENTER_VERTICAL);
        row.addView(product, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        TextView arrow = label("›", 25, WHITE, false);
        arrow.setGravity(Gravity.CENTER);
        row.addView(arrow, new LinearLayout.LayoutParams(dp(28), dp(38)));
        row.setClickable(true);
        row.setFocusable(true);
        return row;
    }

    private void markSelectedChemicalResult(LinearLayout results, View selected) {
        for (int i = 0; i < results.getChildCount(); i++) {
            View child = results.getChildAt(i);
            if (!"chemical-result".equals(child.getTag())) continue;
            child.setBackground(bg(child == selected ? CHEM_ACCENT : CHEM_FILL,
                    10, CHEM_BORDER, 1));
        }
    }

'''
assistant = rep(
    assistant,
    "    private LinearLayout page(String title, String subtitle) {\n",
    inventory_helpers + "    private LinearLayout page(String title, String subtitle) {\n",
    "inventory UI helpers",
)

if home == home_before or assistant == assistant_before:
    raise SystemExit("v0.6.4: no source changed")

HOME.write_text(home, encoding="utf-8")
ASSISTANT.write_text(assistant, encoding="utf-8")

print("home_inventory_064=APPLIED")
print("home_navigation=FILLED_UNIQUE_COLOURS")
print("inventory_family=BURGUNDY")
print("inventory_actions=FILLED")
print("inventory_information=OUTLINED")
print("inventory_dialogs=CUSTOM_DARKROOM_UI")
print("inventory_process_changes=ZERO")
