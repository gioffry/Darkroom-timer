from pathlib import Path

# v0.3.6
# Il popup AGGIUNGI non usa piu' il dropdown AutoComplete Android.
# I risultati vengono mostrati come righe vere, sempre visibili e scrollabili
# dentro il popup. Questo evita il bug visto su dispositivo: conteggio corretto
# (es. 8 risultati) ma nessuna voce visualizzata.

p = Path('assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java')
s = p.read_text(encoding='utf-8')

start = s.find('    private void showAddProductDialog() {')
end = s.find('    private void enrichProductThenAdd(', start)
if start < 0 or end < 0:
    raise SystemExit('showAddProductDialog boundaries missing')

method = r'''    private void showAddProductDialog() {
        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setPadding(dp(18), dp(8), dp(18), 0);

        String[] typeLabels = new String[]{
                "Rivelatore pellicola", "Rivelatore carta", "Arresto", "Fissaggio"
        };
        final int[] typeRoles = new int[]{ROLE_FILM_DEV, ROLE_PAPER_DEV, ROLE_STOP, ROLE_FIX};
        Spinner typeSpinner = spinner(typeLabels);
        wrap.addView(fieldBlock("TIPO", typeSpinner));

        EditText search = edit("", InputType.TYPE_CLASS_TEXT);
        search.setHint("Scrivi almeno 3 lettere…");
        search.setSingleLine(true);
        wrap.addView(search);

        TextView status = label("Scegli il tipo e scrivi almeno 3 lettere.", 12, MUTED, false);
        status.setPadding(dp(4), dp(8), dp(4), dp(8));
        wrap.addView(status);

        LinearLayout resultsBox = new LinearLayout(this);
        resultsBox.setOrientation(LinearLayout.VERTICAL);
        ScrollView resultsScroll = new ScrollView(this);
        resultsScroll.setFillViewport(false);
        resultsScroll.addView(resultsBox);
        LinearLayout.LayoutParams resultsLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(300));
        resultsScroll.setLayoutParams(resultsLp);
        wrap.addView(resultsScroll);

        Map<String, OnlineCatalogSearch.SearchResult> mdc = new HashMap<>();
        final Runnable[] pending = new Runnable[1];
        final int[] generation = new int[]{0};
        final String[] chosen = new String[1];

        final java.util.function.Consumer<List<String>> renderResults = values -> {
            resultsBox.removeAllViews();
            if (values == null || values.isEmpty()) return;
            for (String value : values) {
                TextView item = row(value + "    ›");
                item.setOnClickListener(v -> {
                    chosen[0] = value;
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

                // Se l'utente ha appena toccato una riga, non rilanciare la ricerca
                // sul nome completo selezionato.
                if (chosen[0] != null && q.equals(chosen[0])) return;
                chosen[0] = null;
                mdc.clear();
                resultsBox.removeAllViews();

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

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Aggiungi prodotto")
                .setView(wrap)
                .setNegativeButton("ANNULLA", null)
                .setPositiveButton("AGGIUNGI", null)
                .create();

        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
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
                }));
        dialog.show();
    }

'''

s = s[:start] + method + s[end:]
p.write_text(s, encoding='utf-8')
print('v0.3.6 inline visible results patch applied')
