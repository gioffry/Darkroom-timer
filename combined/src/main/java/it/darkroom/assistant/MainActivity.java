package it.darkroom.assistant;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

public class MainActivity extends Activity {
    private static final int HOME = 0;
    private static final int PRODUCTS = 1;
    private static final int FILM = 2;
    private static final int PAPER = 3;

    private static final int ROLE_FILM_DEV = 1;
    private static final int ROLE_PAPER_DEV = 2;
    private static final int ROLE_STOP = 4;
    private static final int ROLE_FIX = 8;

    private static final int BG = Color.rgb(0, 0, 0);
    private static final int WHITE = Color.rgb(246, 243, 238);
    private static final int MUTED = Color.rgb(170, 166, 162);
    private static final int BURGUNDY = Color.rgb(124, 31, 31);
    private static final int BURGUNDY_BRIGHT = Color.rgb(167, 43, 38);
    private static final int CARD = Color.rgb(24, 24, 24);
    private static final int CARD_2 = Color.rgb(39, 39, 39);
    private static final int TAUPE = Color.rgb(103, 95, 88);
    private static final int BORDER = Color.rgb(67, 67, 67);

    private final Product[] fallbackProducts = new Product[] {
            new Product("Foma Universal", ROLE_FILM_DEV | ROLE_PAPER_DEV, true,
                    new String[]{"1+3"}, new String[]{"1+3"}, null,
                    "Sciogli prima la parte A e poi la parte B in circa 800 ml d'acqua a 50–70 °C; porta infine a 1 litro.", -1, ""),
            new Product("Fomadon R09", ROLE_FILM_DEV, false,
                    new String[]{"1+25", "1+50"}, new String[]{}, null, null, -1, ""),
            new Product("Fomadon Excel", ROLE_FILM_DEV, true,
                    new String[]{"stock", "1+1"}, new String[]{}, null,
                    "Prepara la soluzione stock seguendo le istruzioni della confezione.", -1, ""),
            new Product("Ilford ID-11", ROLE_FILM_DEV, true,
                    new String[]{"stock", "1+1", "1+3"}, new String[]{}, null,
                    "Prepara la soluzione stock seguendo le istruzioni della confezione.", -1, ""),
            new Product("Kodak D-76", ROLE_FILM_DEV, true,
                    new String[]{"stock", "1+1"}, new String[]{}, null,
                    "Prepara la soluzione stock seguendo le istruzioni della confezione.", -1, ""),
            new Product("Adox Adostop ECO", ROLE_STOP, false,
                    new String[]{}, new String[]{}, "1+19", null, -1, ""),
            new Product("Ilford Ilfostop", ROLE_STOP, false,
                    new String[]{}, new String[]{}, "1+19", null, -1, ""),
            new Product("Compard Fix Ag Plus", ROLE_FIX, false,
                    new String[]{}, new String[]{}, "1+9", null, -1, ""),
            new Product("Ilford Rapid Fixer", ROLE_FIX, false,
                    new String[]{}, new String[]{}, "1+4", null, -1, ""),
            new Product("Fomafix", ROLE_FIX, false,
                    new String[]{}, new String[]{}, "1+5", null, -1, "")
    };

    private final FilmStock[] fallbackFilms = new FilmStock[] {
            new FilmStock("Ilford HP5 Plus 400 — 35 mm", 400, "35", ""),
            new FilmStock("Ilford HP5 Plus 400 — 120", 400, "120", ""),
            new FilmStock("Ilford FP4 Plus 125 — 35 mm", 125, "35", ""),
            new FilmStock("Ilford FP4 Plus 125 — 120", 125, "120", ""),
            new FilmStock("Fomapan 100 Classic — 35 mm", 100, "35", ""),
            new FilmStock("Fomapan 100 Classic — 120", 100, "120", ""),
            new FilmStock("Fomapan 200 Creative — 35 mm", 200, "35", ""),
            new FilmStock("Fomapan 200 Creative — 120", 200, "120", ""),
            new FilmStock("Fomapan 400 Action — 35 mm", 400, "35", ""),
            new FilmStock("Fomapan 400 Action — 120", 400, "120", ""),
            new FilmStock("Kodak Tri-X 400 — 35 mm", 400, "35", ""),
            new FilmStock("Kodak Tri-X 400 — 120", 400, "120", ""),
            new FilmStock("Kentmere Pan 100 — 35 mm", 100, "35", ""),
            new FilmStock("Kentmere Pan 400 — 35 mm", 400, "35", "")
    };

    private SharedPreferences prefs;
    private int currentScreen = HOME;
    private final Handler handler = new Handler(Looper.getMainLooper());

    private FilmStock selectedFilm;
    private Product selectedFilmDeveloper;
    private Product selectedStop;
    private Product selectedFix;

    private AutoCompleteTextView filmField;
    private EditText isoField;
    private Spinner rollsSpinner;
    private Spinner tankSpinner;
    private Spinner developerSpinner;
    private Spinner dilutionSpinner;
    private EditText temperatureField;
    private Spinner stopSpinner;
    private Spinner fixSpinner;
    private LinearLayout filmResultBox;
    private TextView filmSearchStatus;

    private Spinner paperDeveloperSpinner;
    private Spinner paperStopSpinner;
    private Spinner paperFixSpinner;
    private EditText paperVolumeField;
    private LinearLayout paperResultBox;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Window window = getWindow();
        window.setStatusBarColor(BG);
        window.setNavigationBarColor(BG);
        prefs = getSharedPreferences("darkroom_assistant", MODE_PRIVATE);
        showHome();
    }

    @Override
    public void onBackPressed() {
        if (currentScreen != HOME) {
            showHome();
            return;
        }
        super.onBackPressed();
    }

    private void showHome() {
        currentScreen = HOME;
        LinearLayout page = page("Darkroom Assistant", "Camera oscura, semplice.");
        page.addView(homeCard("PRODOTTI\nCHIMICI", BURGUNDY, v -> showProducts()));
        page.addView(space(18));
        page.addView(homeCard("SVILUPPO\nPELLICOLA", CARD_2, v -> showFilm()));
        page.addView(space(18));
        page.addView(homeCard("STAMPA\nCARTA", TAUPE, v -> showPaper()));
        setContentView(scroll(page));
    }

    private void showProducts() {
        currentScreen = PRODUCTS;
        LinearLayout page = page("Prodotti chimici", "Gestisci il tuo magazzino.");

        Button add = actionButton("＋  AGGIUNGI", BURGUNDY);
        add.setOnClickListener(v -> showAddProductDialog());
        page.addView(add);
        page.addView(space(28));

        page.addView(label("MAGAZZINO", 17, WHITE, true));
        page.addView(space(10));

        Set<String> inventory = getInventory();
        if (inventory.isEmpty()) {
            TextView empty = label("Nessun prodotto in magazzino.", 15, MUTED, false);
            empty.setPadding(dp(4), dp(18), dp(4), dp(18));
            page.addView(empty);
        } else {
            List<String> names = new ArrayList<>(inventory);
            Collections.sort(names);
            for (String name : names) {
                TextView row = row(name + "    ›");
                row.setOnClickListener(v -> showProductDetails(name));
                page.addView(row);
                page.addView(space(9));
            }
        }
        page.addView(space(80));
        setContentView(scroll(page));
    }

    private void showAddProductDialog() {
        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setPadding(dp(18), dp(8), dp(18), 0);

        AutoCompleteTextView search = new AutoCompleteTextView(this);
        search.setThreshold(3);
        search.setHint("Scrivi almeno 3 lettere…");
        search.setSingleLine(true);
        styleInput(search);
        wrap.addView(search);

        TextView status = label("La ricerca parte online dopo 3 lettere.", 12, MUTED, false);
        status.setPadding(dp(4), dp(8), dp(4), 0);
        wrap.addView(status);

        List<String> suggestions = new ArrayList<>();
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_dropdown_item_1line, suggestions);
        search.setAdapter(adapter);
        Map<String, OnlineCatalogSearch.SearchResult> online = new HashMap<>();
        final Runnable[] pending = new Runnable[1];
        final int[] generation = new int[]{0};

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int st, int c, int a) {}
            @Override public void onTextChanged(CharSequence s, int st, int before, int count) {}
            @Override public void afterTextChanged(Editable e) {
                String q = e.toString().trim();
                generation[0]++;
                int myGen = generation[0];
                if (pending[0] != null) handler.removeCallbacks(pending[0]);
                if (q.length() < 3) {
                    adapter.clear();
                    online.clear();
                    status.setText("La ricerca parte online dopo 3 lettere.");
                    return;
                }
                List<String> local = localProductMatches(q);
                replaceSuggestions(adapter, local);
                status.setText("Cerco online…");
                pending[0] = () -> new Thread(() -> {
                    List<OnlineCatalogSearch.SearchResult> results = OnlineCatalogSearch.searchChemicals(q);
                    runOnUiThread(() -> {
                        if (myGen != generation[0] || !q.equalsIgnoreCase(search.getText().toString().trim())) return;
                        LinkedHashSet<String> merged = new LinkedHashSet<>(localProductMatches(q));
                        online.clear();
                        for (OnlineCatalogSearch.SearchResult r : results) {
                            String display = r.title;
                            if (display == null || display.length() < 3) continue;
                            merged.add(display);
                            online.put(display.toLowerCase(Locale.ROOT), r);
                        }
                        replaceSuggestions(adapter, new ArrayList<>(merged));
                        if (results.isEmpty()) status.setText("Online: nessun risultato. Mostro solo i dati locali disponibili.");
                        else status.setText("Online: " + results.size() + " risultati trovati.");
                        search.showDropDown();
                    });
                }).start();
                handler.postDelayed(pending[0], 350);
            }
        });

        final String[] selected = new String[1];
        search.setOnItemClickListener((parent, view, position, id) -> selected[0] = String.valueOf(parent.getItemAtPosition(position)));

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Aggiungi prodotto")
                .setView(wrap)
                .setNegativeButton("ANNULLA", null)
                .setPositiveButton("AGGIUNGI", null)
                .create();

        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            String name = selected[0] != null ? selected[0] : search.getText().toString().trim();
            Product local = findProduct(name);
            if (local != null) {
                dialog.dismiss();
                startProductAddFlow(local);
                return;
            }
            OnlineCatalogSearch.SearchResult r = online.get(name.toLowerCase(Locale.ROOT));
            if (r == null) {
                toast("Seleziona uno dei risultati proposti.");
                return;
            }
            dialog.dismiss();
            toast("Recupero la scheda online…");
            new Thread(() -> {
                OnlineCatalogSearch.ChemicalData data = OnlineCatalogSearch.enrichChemical(r);
                runOnUiThread(() -> {
                    Product p = new Product(data.name, data.roles, data.stockPrep,
                            data.filmDilutions, data.paperDilutions, data.workingDilution,
                            data.stockInstructions, data.expiryDays, data.sourceUrl);
                    if (p.roles == 0) chooseProductTypeThenAdd(p);
                    else startProductAddFlow(p);
                });
            }).start();
        }));
        dialog.show();
    }

    private void chooseProductTypeThenAdd(Product p) {
        String[] types = new String[]{"Rivelatore pellicola", "Rivelatore carta", "Rivelatore pellicola + carta", "Arresto", "Fissaggio"};
        new AlertDialog.Builder(this)
                .setTitle("Tipo non riconosciuto automaticamente")
                .setMessage("La fonte online non consente di classificare il prodotto con sicurezza. Correggi solo questo dato.")
                .setItems(types, (d, which) -> {
                    int role = roleForType(which);
                    Product fixed = new Product(p.name, role, p.stockPrep, p.filmDilutions, p.paperDilutions,
                            p.workingDilution, p.stockInstructions, p.expiryDays, p.sourceUrl);
                    startProductAddFlow(fixed);
                })
                .show();
    }

    private void startProductAddFlow(Product p) {
        saveProductMetadata(p);
        if (p.stockPrep) {
            String body = p.stockInstructions != null ? p.stockInstructions :
                    "Questo prodotto deve essere preparato come soluzione stock prima di entrare in magazzino.";
            new AlertDialog.Builder(this)
                    .setTitle("Preparazione stock richiesta")
                    .setMessage(body)
                    .setNegativeButton("ANNULLA", null)
                    .setPositiveButton("STOCK PREPARATO", (d, w) -> askOpeningDate(p))
                    .show();
        } else {
            askOpeningDate(p);
        }
    }

    private void askOpeningDate(Product p) {
        Calendar now = Calendar.getInstance();
        DatePickerDialog picker = new DatePickerDialog(this,
                (view, year, month, day) -> {
                    Calendar selected = Calendar.getInstance();
                    selected.set(year, month, day, 12, 0, 0);
                    addToInventory(p, selected.getTimeInMillis());
                    toast(p.name + " aggiunto al magazzino.");
                    showProducts();
                }, now.get(Calendar.YEAR), now.get(Calendar.MONTH), now.get(Calendar.DAY_OF_MONTH));
        picker.setTitle(p.stockPrep ? "Data preparazione stock" : "Data apertura");
        picker.show();
    }

    private void showProductDetails(String name) {
        Product p = findProduct(name);
        long opened = prefs.getLong("opened_" + key(name), 0L);
        String expiry = "Scadenza non determinabile";
        if (p != null && p.expiryDays > 0 && opened > 0) {
            long expires = opened + p.expiryDays * 86400000L;
            expiry = "Scadenza: " + new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY).format(new Date(expires));
        }
        new AlertDialog.Builder(this)
                .setTitle(name)
                .setMessage(expiry)
                .setNegativeButton("CHIUDI", null)
                .setNeutralButton("MODIFICA", (d, w) -> showEditProductDialog(name))
                .setPositiveButton("ELIMINA", (d, w) -> {
                    removeFromInventory(name);
                    showProducts();
                })
                .show();
    }

    private void showEditProductDialog(String oldName) {
        Product p = findProduct(oldName);
        if (p == null) return;
        long opened = prefs.getLong("opened_" + key(oldName), 0L);
        SimpleDateFormat df = new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY);
        df.setLenient(false);

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(18), dp(8), dp(18), 0);

        EditText name = edit(p.name, InputType.TYPE_CLASS_TEXT);
        box.addView(fieldBlock("NOME", name));

        String[] types = new String[]{"Rivelatore pellicola", "Rivelatore carta", "Rivelatore pellicola + carta", "Arresto", "Fissaggio"};
        Spinner type = spinner(types);
        type.setSelection(typeIndexForRole(p.roles));
        box.addView(fieldBlock("TIPO", type));

        EditText filmDil = edit(join(p.filmDilutions), InputType.TYPE_CLASS_TEXT);
        box.addView(fieldBlock("DILUIZIONI PELLICOLA (separate da virgola)", filmDil));
        EditText paperDil = edit(join(p.paperDilutions), InputType.TYPE_CLASS_TEXT);
        box.addView(fieldBlock("DILUIZIONI CARTA (separate da virgola)", paperDil));
        EditText working = edit(p.workingDilution == null ? "" : p.workingDilution, InputType.TYPE_CLASS_TEXT);
        box.addView(fieldBlock("DILUIZIONE ARRESTO/FIX", working));

        CheckBox stock = new CheckBox(this);
        stock.setText("Richiede preparazione stock");
        stock.setTextColor(WHITE);
        stock.setChecked(p.stockPrep);
        box.addView(stock);
        box.addView(space(10));

        EditText date = edit(opened > 0 ? df.format(new Date(opened)) : "", InputType.TYPE_CLASS_DATETIME);
        box.addView(fieldBlock("DATA APERTURA / PREPARAZIONE (gg/mm/aaaa)", date));
        EditText expiryDays = edit(p.expiryDays > 0 ? String.valueOf(p.expiryDays) : "", InputType.TYPE_CLASS_NUMBER);
        box.addView(fieldBlock("DURATA DOPO APERTURA (giorni, opzionale)", expiryDays));

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Modifica prodotto")
                .setView(new ScrollView(this) {{ addView(box); }})
                .setNegativeButton("ANNULLA", null)
                .setPositiveButton("SALVA", null)
                .create();
        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            String newName = name.getText().toString().trim();
            if (newName.isEmpty()) { toast("Inserisci il nome."); return; }
            long newOpened = opened;
            try {
                if (!date.getText().toString().trim().isEmpty()) newOpened = df.parse(date.getText().toString().trim()).getTime();
            } catch (Exception ex) { toast("Data non valida."); return; }
            int exp = -1;
            try { if (!expiryDays.getText().toString().trim().isEmpty()) exp = Integer.parseInt(expiryDays.getText().toString().trim()); }
            catch (Exception ex) { toast("Durata non valida."); return; }

            int role = roleForType(type.getSelectedItemPosition());
            Product edited = new Product(newName, role, stock.isChecked(), splitCsv(filmDil.getText().toString()),
                    splitCsv(paperDil.getText().toString()), emptyToNull(working.getText().toString()),
                    p.stockInstructions, exp, p.sourceUrl);
            replaceInventoryProduct(oldName, edited, newOpened);
            dialog.dismiss();
            showProducts();
        }));
        dialog.show();
    }

    private void showFilm() {
        currentScreen = FILM;
        selectedFilm = null;
        selectedFilmDeveloper = null;
        selectedStop = null;
        selectedFix = null;

        LinearLayout page = page("Sviluppo pellicola", "Configura lo sviluppo in JOBO CPE2.");

        filmField = new AutoCompleteTextView(this);
        filmField.setThreshold(3);
        filmField.setHint("Pellicola — scrivi almeno 3 lettere");
        styleInput(filmField);
        List<String> suggestions = new ArrayList<>();
        ArrayAdapter<String> filmAdapter = new ArrayAdapter<>(this, android.R.layout.simple_dropdown_item_1line, suggestions);
        filmField.setAdapter(filmAdapter);
        Map<String, OnlineCatalogSearch.SearchResult> onlineFilms = new HashMap<>();
        page.addView(fieldBlock("PELLICOLA", filmField));
        filmSearchStatus = label("Ricerca online dopo 3 lettere.", 12, MUTED, false);
        filmSearchStatus.setPadding(dp(4), 0, dp(4), dp(10));
        page.addView(filmSearchStatus);

        isoField = new EditText(this);
        isoField.setInputType(InputType.TYPE_CLASS_NUMBER);
        isoField.setHint("ISO nominale");
        styleInput(isoField);
        page.addView(fieldBlock("ISO ESPOSTO", isoField));

        rollsSpinner = spinner(new String[]{"1", "2"});
        page.addView(fieldBlock("NUMERO RULLI", rollsSpinner));
        tankSpinner = spinner(new String[]{"JOBO 2520 — 270 ml"});
        page.addView(fieldBlock("TANK JOBO", tankSpinner));

        List<Product> developers = inventoryProductsByRole(ROLE_FILM_DEV);
        developerSpinner = productSpinner(developers, "Nessun rivelatore in magazzino");
        page.addView(fieldBlock("RIVELATORE", developerSpinner));
        dilutionSpinner = spinner(new String[]{"—"});
        page.addView(fieldBlock("DILUIZIONE", dilutionSpinner));

        temperatureField = new EditText(this);
        temperatureField.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        temperatureField.setText("20");
        styleInput(temperatureField);
        page.addView(fieldBlock("TEMPERATURA °C", temperatureField));

        List<Product> stops = inventoryProductsByRole(ROLE_STOP);
        stopSpinner = productSpinner(stops, "Nessun arresto in magazzino");
        page.addView(fieldBlock("ARRESTO", stopSpinner));
        List<Product> fixes = inventoryProductsByRole(ROLE_FIX);
        fixSpinner = productSpinner(fixes, "Nessun fissaggio in magazzino");
        page.addView(fieldBlock("FISSAGGIO", fixSpinner));

        developerSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                selectedFilmDeveloper = productAt(developers, position);
                String[] ds = selectedFilmDeveloper == null || selectedFilmDeveloper.filmDilutions.length == 0 ? new String[]{"—"} : selectedFilmDeveloper.filmDilutions;
                setSpinnerItems(dilutionSpinner, ds);
            }
        });
        stopSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) { selectedStop = productAt(stops, position); }
        });
        fixSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) { selectedFix = productAt(fixes, position); }
        });

        wireFilmSearch(filmField, filmAdapter, onlineFilms);
        filmField.setOnItemClickListener((parent, view, position, id) -> {
            String display = String.valueOf(parent.getItemAtPosition(position));
            FilmStock local = findFilm(display);
            if (local != null) {
                selectFilm(local);
                return;
            }
            OnlineCatalogSearch.SearchResult r = onlineFilms.get(display.toLowerCase(Locale.ROOT));
            if (r == null) return;
            selectedFilm = null;
            isoField.setText("");
            filmSearchStatus.setText("Recupero ISO e formato dalla fonte online…");
            new Thread(() -> {
                OnlineCatalogSearch.FilmData fd = OnlineCatalogSearch.enrichFilm(r);
                runOnUiThread(() -> finishOnlineFilmSelection(fd));
            }).start();
        });

        Button calc = actionButton("CALCOLA", CARD_2);
        calc.setOnClickListener(v -> calculateFilm());
        page.addView(space(6));
        page.addView(calc);
        page.addView(space(14));
        filmResultBox = new LinearLayout(this);
        filmResultBox.setOrientation(LinearLayout.VERTICAL);
        page.addView(filmResultBox);
        page.addView(space(80));
        setContentView(scroll(page));
    }

    private void wireFilmSearch(AutoCompleteTextView field, ArrayAdapter<String> adapter,
                                Map<String, OnlineCatalogSearch.SearchResult> online) {
        final Runnable[] pending = new Runnable[1];
        final int[] generation = new int[]{0};
        field.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int st, int c, int a) {}
            @Override public void onTextChanged(CharSequence s, int st, int before, int count) {}
            @Override public void afterTextChanged(Editable e) {
                String q = e.toString().trim();
                generation[0]++;
                int myGen = generation[0];
                if (pending[0] != null) handler.removeCallbacks(pending[0]);
                if (q.length() < 3) {
                    adapter.clear();
                    online.clear();
                    if (filmSearchStatus != null) filmSearchStatus.setText("Ricerca online dopo 3 lettere.");
                    return;
                }
                List<String> local = localFilmMatches(q);
                replaceSuggestions(adapter, local);
                if (filmSearchStatus != null) filmSearchStatus.setText("Cerco online…");
                pending[0] = () -> new Thread(() -> {
                    List<OnlineCatalogSearch.SearchResult> results = OnlineCatalogSearch.searchFilms(q);
                    runOnUiThread(() -> {
                        if (myGen != generation[0] || !q.equalsIgnoreCase(field.getText().toString().trim())) return;
                        LinkedHashSet<String> merged = new LinkedHashSet<>(localFilmMatches(q));
                        online.clear();
                        for (OnlineCatalogSearch.SearchResult r : results) {
                            merged.add(r.title);
                            online.put(r.title.toLowerCase(Locale.ROOT), r);
                        }
                        replaceSuggestions(adapter, new ArrayList<>(merged));
                        if (filmSearchStatus != null) {
                            filmSearchStatus.setText(results.isEmpty() ? "Online: nessun risultato. Mostro solo i dati locali disponibili." : "Online: " + results.size() + " risultati trovati.");
                        }
                        field.showDropDown();
                    });
                }).start();
                handler.postDelayed(pending[0], 350);
            }
        });
    }

    private void finishOnlineFilmSelection(OnlineCatalogSearch.FilmData fd) {
        if (fd == null) return;
        if (fd.format == null) {
            new AlertDialog.Builder(this)
                    .setTitle(fd.name)
                    .setMessage("Il formato non è indicato in modo univoco nella fonte. Scegli quello del rullo che stai sviluppando.")
                    .setItems(new String[]{"35 mm", "120"}, (d, which) -> selectFilm(new FilmStock(fd.name + (which == 0 ? " — 35 mm" : " — 120"), fd.iso, which == 0 ? "35" : "120", fd.sourceUrl)))
                    .show();
        } else {
            String suffix = fd.format.equals("35") ? " — 35 mm" : " — 120";
            selectFilm(new FilmStock(fd.name.contains("—") ? fd.name : fd.name + suffix, fd.iso, fd.format, fd.sourceUrl));
        }
    }

    private void selectFilm(FilmStock f) {
        selectedFilm = f;
        filmField.setText(f.name, false);
        if (f.nominalIso > 0) isoField.setText(String.valueOf(f.nominalIso));
        else isoField.setText("");
        if (filmSearchStatus != null) filmSearchStatus.setText(f.sourceUrl == null || f.sourceUrl.isEmpty() ? "Dati locali verificati." : "Dati recuperati online.");
    }

    private void calculateFilm() {
        if (selectedFilm == null) selectedFilm = findFilm(filmField.getText().toString().trim());
        if (selectedFilm == null) { toast("Seleziona una pellicola dai suggerimenti."); return; }
        if (selectedFilmDeveloper == null) { toast("Aggiungi e seleziona un rivelatore dal magazzino."); return; }
        if (selectedStop == null || selectedFix == null) { toast("Aggiungi arresto e fissaggio al magazzino."); return; }

        int rolls = Integer.parseInt(String.valueOf(rollsSpinner.getSelectedItem()));
        if ("120".equals(selectedFilm.format) && rolls > 1) { resultFilmError("JOBO 2520: in questa configurazione è ammesso 1 × 120."); return; }
        if ("35".equals(selectedFilm.format) && rolls > 2) { resultFilmError("JOBO 2520: massimo 2 rulli 35 mm."); return; }

        int iso;
        double temp;
        try {
            iso = Integer.parseInt(isoField.getText().toString().trim());
            temp = Double.parseDouble(temperatureField.getText().toString().trim().replace(',', '.'));
        } catch (Exception e) { toast("Controlla ISO e temperatura."); return; }

        String dilution = String.valueOf(dilutionSpinner.getSelectedItem());
        double[] devMix = mix(270, dilution);
        double[] stopMix = mix(270, selectedStop.workingDilution);
        double[] fixMix = mix(270, selectedFix.workingDilution);
        if (devMix == null || stopMix == null || fixMix == null) { resultFilmError("Impossibile calcolare una delle diluizioni selezionate."); return; }

        filmResultBox.removeAllViews();
        String time = computeJoboTime(selectedFilm, selectedFilmDeveloper, dilution, iso, temp);
        resultLine(filmResultBox, "TEMPO JOBO CPE2", time);
        resultLine(filmResultBox, "RIVELATORE", formatMix(devMix, 270));
        resultLine(filmResultBox, "ARRESTO", formatMix(stopMix, 270));
        resultLine(filmResultBox, "FISSAGGIO", formatMix(fixMix, 270));
        TextView source = label(time.startsWith("8 min 05 s") ?
                "Fonte tempo: Massive Dev Chart 9 min 30 s @20 °C; adattamento JOBO rotazione continua −15%." :
                "Tempo non ancora disponibile online per questa combinazione: nessuna stima inventata.", 12, MUTED, false);
        source.setPadding(dp(4), dp(14), dp(4), dp(18));
        filmResultBox.addView(source);
    }

    private String computeJoboTime(FilmStock film, Product dev, String dilution, int iso, double temp) {
        boolean hp5 = film.name.startsWith("Ilford HP5 Plus 400");
        if (hp5 && "Foma Universal".equalsIgnoreCase(dev.name) && "1+3".equals(dilution) && iso == 400 && Math.abs(temp - 20.0) < 0.01) {
            int seconds = (int) Math.round(9.5 * 60.0 * 0.85);
            return seconds / 60 + " min " + String.format(Locale.ITALY, "%02d", seconds % 60) + " s";
        }
        return "Tempo non determinabile con dati verificati";
    }

    private void resultFilmError(String message) {
        filmResultBox.removeAllViews();
        TextView t = label(message, 15, WHITE, true);
        t.setPadding(dp(16), dp(16), dp(16), dp(16));
        t.setBackground(bg(BURGUNDY, 14, 0, 0));
        filmResultBox.addView(t);
    }

    private void showPaper() {
        currentScreen = PAPER;
        LinearLayout page = page("Stampa carta", "Prepara i bagni per la stampa.");
        List<Product> developers = inventoryProductsByRole(ROLE_PAPER_DEV);
        List<Product> stops = inventoryProductsByRole(ROLE_STOP);
        List<Product> fixes = inventoryProductsByRole(ROLE_FIX);

        paperDeveloperSpinner = productSpinner(developers, "Nessun rivelatore carta in magazzino");
        paperStopSpinner = productSpinner(stops, "Nessun arresto in magazzino");
        paperFixSpinner = productSpinner(fixes, "Nessun fissaggio in magazzino");
        page.addView(fieldBlock("RIVELATORE CARTA", paperDeveloperSpinner));
        page.addView(fieldBlock("ARRESTO", paperStopSpinner));
        page.addView(fieldBlock("FISSAGGIO", paperFixSpinner));

        paperVolumeField = new EditText(this);
        paperVolumeField.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        paperVolumeField.setText("1000");
        styleInput(paperVolumeField);
        page.addView(fieldBlock("VOLUME DA PREPARARE (ml)", paperVolumeField));

        Button calc = actionButton("CALCOLA", BURGUNDY);
        calc.setOnClickListener(v -> calculatePaper(developers, stops, fixes));
        page.addView(space(6));
        page.addView(calc);
        page.addView(space(16));
        paperResultBox = new LinearLayout(this);
        paperResultBox.setOrientation(LinearLayout.VERTICAL);
        page.addView(paperResultBox);
        page.addView(space(80));
        setContentView(scroll(page));
    }

    private void calculatePaper(List<Product> developers, List<Product> stops, List<Product> fixes) {
        Product dev = productAt(developers, paperDeveloperSpinner.getSelectedItemPosition());
        Product stop = productAt(stops, paperStopSpinner.getSelectedItemPosition());
        Product fix = productAt(fixes, paperFixSpinner.getSelectedItemPosition());
        if (dev == null || stop == null || fix == null) { toast("Aggiungi rivelatore carta, arresto e fissaggio al magazzino."); return; }
        double volume;
        try {
            volume = Double.parseDouble(paperVolumeField.getText().toString().trim().replace(',', '.'));
            if (volume <= 0) throw new NumberFormatException();
        } catch (Exception e) { toast("Inserisci un volume valido."); return; }

        String devDilution = dev.paperDilutions.length > 0 ? dev.paperDilutions[0] : null;
        double[] devMix = mix(volume, devDilution);
        double[] stopMix = mix(volume, stop.workingDilution);
        double[] fixMix = mix(volume, fix.workingDilution);
        if (devMix == null || stopMix == null || fixMix == null) { toast("Diluizione non disponibile: modifica il prodotto in magazzino e correggila."); return; }

        paperResultBox.removeAllViews();
        resultLine(paperResultBox, "RIVELATORE", formatMix(devMix, volume));
        resultLine(paperResultBox, "ARRESTO", formatMix(stopMix, volume));
        resultLine(paperResultBox, "FISSAGGIO", formatMix(fixMix, volume));
    }

    private List<String> localProductMatches(String q) {
        List<String> out = new ArrayList<>();
        String needle = q.toLowerCase(Locale.ROOT);
        for (Product p : fallbackProducts) if (p.name.toLowerCase(Locale.ROOT).contains(needle)) out.add(p.name);
        for (String name : getInventory()) if (name.toLowerCase(Locale.ROOT).contains(needle) && !out.contains(name)) out.add(name);
        return out;
    }

    private List<String> localFilmMatches(String q) {
        List<String> out = new ArrayList<>();
        String needle = q.toLowerCase(Locale.ROOT);
        for (FilmStock f : fallbackFilms) if (f.name.toLowerCase(Locale.ROOT).contains(needle)) out.add(f.name);
        return out;
    }

    private void replaceSuggestions(ArrayAdapter<String> adapter, List<String> values) {
        adapter.clear();
        adapter.addAll(values);
        adapter.notifyDataSetChanged();
    }

    private LinearLayout page(String title, String subtitle) {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(18), dp(28), dp(18), dp(24));
        page.setBackgroundColor(BG);
        TextView home = label("☰", 28, WHITE, false);
        home.setPadding(0, 0, 0, dp(18));
        home.setOnClickListener(v -> showHome());
        page.addView(home);
        TextView h = label(title, 34, WHITE, true);
        h.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
        page.addView(h);
        page.addView(space(12));
        page.addView(label(subtitle, 17, MUTED, false));
        page.addView(space(22));
        View accent = new View(this);
        accent.setLayoutParams(new LinearLayout.LayoutParams(dp(34), dp(3)));
        accent.setBackground(bg(BURGUNDY_BRIGHT, 3, 0, 0));
        page.addView(accent);
        page.addView(space(28));
        return page;
    }

    private View homeCard(String text, int color, View.OnClickListener listener) {
        TextView card = label(text + "                                  ›", 23, WHITE, true);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(30), dp(26), dp(24), dp(26));
        card.setMinHeight(dp(142));
        card.setBackground(bg(color, 18, 0, 0));
        card.setOnClickListener(listener);
        return card;
    }

    private LinearLayout fieldBlock(String labelText, View field) {
        LinearLayout block = new LinearLayout(this);
        block.setOrientation(LinearLayout.VERTICAL);
        block.setPadding(0, 0, 0, dp(12));
        TextView l = label(labelText, 12, MUTED, true);
        l.setPadding(dp(4), 0, 0, dp(6));
        block.addView(l);
        block.addView(field);
        return block;
    }

    private void styleInput(TextView v) {
        v.setTextColor(WHITE);
        v.setHintTextColor(MUTED);
        v.setTextSize(16);
        v.setPadding(dp(14), dp(13), dp(14), dp(13));
        v.setBackground(bg(CARD, 13, BORDER, 1));
        v.setMinHeight(dp(52));
    }

    private EditText edit(String value, int inputType) {
        EditText e = new EditText(this);
        e.setInputType(inputType);
        e.setText(value == null ? "" : value);
        styleInput(e);
        return e;
    }

    private Spinner spinner(String[] items) {
        Spinner s = new Spinner(this);
        setSpinnerItems(s, items);
        s.setPadding(dp(8), dp(4), dp(8), dp(4));
        s.setBackground(bg(CARD, 13, BORDER, 1));
        s.setMinimumHeight(dp(52));
        return s;
    }

    private Spinner productSpinner(List<Product> products, String emptyLabel) {
        List<String> names = new ArrayList<>();
        if (products.isEmpty()) names.add(emptyLabel); else for (Product p : products) names.add(p.name);
        return spinner(names.toArray(new String[0]));
    }

    private void setSpinnerItems(Spinner spinner, String[] items) {
        ArrayAdapter<String> a = new ArrayAdapter<String>(this, android.R.layout.simple_spinner_item, items) {
            @Override public View getView(int position, View convertView, ViewGroup parent) {
                TextView t = (TextView) super.getView(position, convertView, parent);
                t.setTextColor(WHITE);
                t.setTextSize(16);
                t.setPadding(dp(10), dp(10), dp(10), dp(10));
                return t;
            }
        };
        a.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(a);
    }

    private Button actionButton(String text, int color) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(WHITE);
        b.setTextSize(18);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setAllCaps(false);
        b.setMinHeight(dp(60));
        b.setBackground(bg(color, 16, 0, 0));
        return b;
    }

    private TextView row(String text) {
        TextView v = label(text, 17, WHITE, true);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setPadding(dp(18), dp(16), dp(18), dp(16));
        v.setMinHeight(dp(62));
        v.setBackground(bg(CARD, 13, BORDER, 1));
        return v;
    }

    private void resultLine(LinearLayout parent, String labelText, String value) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.VERTICAL);
        row.setPadding(dp(18), dp(14), dp(18), dp(14));
        row.setBackground(bg(CARD, 13, BORDER, 1));
        row.addView(label(labelText, 12, MUTED, false));
        row.addView(space(5));
        row.addView(label(value, 18, WHITE, true));
        parent.addView(row);
        parent.addView(space(9));
    }

    private ScrollView scroll(View content) {
        ScrollView s = new ScrollView(this);
        s.setFillViewport(true);
        s.setBackgroundColor(BG);
        s.addView(content);
        return s;
    }

    private TextView label(String text, float size, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextSize(size);
        t.setTextColor(color);
        t.setTypeface(Typeface.DEFAULT, bold ? Typeface.BOLD : Typeface.NORMAL);
        return t;
    }

    private View space(int value) {
        View v = new View(this);
        v.setLayoutParams(new LinearLayout.LayoutParams(1, dp(value)));
        return v;
    }

    private GradientDrawable bg(int color, int radiusDp, int strokeColor, int strokeDp) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(radiusDp));
        if (strokeDp > 0) g.setStroke(dp(strokeDp), strokeColor);
        return g;
    }

    private Set<String> getInventory() {
        return new HashSet<>(prefs.getStringSet("inventory", new HashSet<>()));
    }

    private void addToInventory(Product p, long openedMillis) {
        saveProductMetadata(p);
        Set<String> set = getInventory();
        set.add(p.name);
        prefs.edit().putStringSet("inventory", set).putLong("opened_" + key(p.name), openedMillis).apply();
    }

    private void replaceInventoryProduct(String oldName, Product p, long openedMillis) {
        Set<String> set = getInventory();
        set.remove(oldName);
        set.add(p.name);
        SharedPreferences.Editor ed = prefs.edit().putStringSet("inventory", set).remove("opened_" + key(oldName));
        ed.putLong("opened_" + key(p.name), openedMillis).apply();
        if (!oldName.equalsIgnoreCase(p.name)) deleteProductMetadata(oldName);
        saveProductMetadata(p);
    }

    private void removeFromInventory(String name) {
        Set<String> set = getInventory();
        set.remove(name);
        prefs.edit().putStringSet("inventory", set).remove("opened_" + key(name)).apply();
        deleteProductMetadata(name);
    }

    private void saveProductMetadata(Product p) {
        String k = key(p.name);
        prefs.edit()
                .putBoolean("prod_saved_" + k, true)
                .putString("prod_name_" + k, p.name)
                .putInt("prod_roles_" + k, p.roles)
                .putBoolean("prod_stock_" + k, p.stockPrep)
                .putString("prod_film_" + k, join(p.filmDilutions))
                .putString("prod_paper_" + k, join(p.paperDilutions))
                .putString("prod_working_" + k, p.workingDilution == null ? "" : p.workingDilution)
                .putString("prod_instructions_" + k, p.stockInstructions == null ? "" : p.stockInstructions)
                .putInt("prod_expiry_" + k, p.expiryDays)
                .putString("prod_source_" + k, p.sourceUrl == null ? "" : p.sourceUrl)
                .apply();
    }

    private void deleteProductMetadata(String name) {
        String k = key(name);
        prefs.edit().remove("prod_saved_" + k).remove("prod_name_" + k).remove("prod_roles_" + k)
                .remove("prod_stock_" + k).remove("prod_film_" + k).remove("prod_paper_" + k)
                .remove("prod_working_" + k).remove("prod_instructions_" + k).remove("prod_expiry_" + k)
                .remove("prod_source_" + k).apply();
    }

    private Product loadSavedProduct(String name) {
        String k = key(name);
        if (!prefs.getBoolean("prod_saved_" + k, false)) return null;
        return new Product(
                prefs.getString("prod_name_" + k, name),
                prefs.getInt("prod_roles_" + k, 0),
                prefs.getBoolean("prod_stock_" + k, false),
                splitCsv(prefs.getString("prod_film_" + k, "")),
                splitCsv(prefs.getString("prod_paper_" + k, "")),
                emptyToNull(prefs.getString("prod_working_" + k, "")),
                emptyToNull(prefs.getString("prod_instructions_" + k, "")),
                prefs.getInt("prod_expiry_" + k, -1),
                prefs.getString("prod_source_" + k, "")
        );
    }

    private List<Product> inventoryProductsByRole(int role) {
        List<Product> out = new ArrayList<>();
        for (String name : getInventory()) {
            Product p = findProduct(name);
            if (p != null && (p.roles & role) != 0) out.add(p);
        }
        Collections.sort(out, (a, b) -> a.name.compareToIgnoreCase(b.name));
        return out;
    }

    private Product productAt(List<Product> products, int position) {
        if (products == null || products.isEmpty() || position < 0 || position >= products.size()) return null;
        return products.get(position);
    }

    private Product findProduct(String name) {
        if (name == null) return null;
        Product saved = loadSavedProduct(name.trim());
        if (saved != null) return saved;
        for (Product p : fallbackProducts) if (p.name.equalsIgnoreCase(name.trim())) return p;
        return null;
    }

    private FilmStock findFilm(String name) {
        if (name == null) return null;
        for (FilmStock f : fallbackFilms) if (f.name.equalsIgnoreCase(name.trim())) return f;
        return null;
    }

    private double[] mix(double total, String dilution) {
        if (dilution == null) return null;
        String d = dilution.trim().toLowerCase(Locale.ROOT);
        if ("stock".equals(d)) return new double[]{total, 0};
        String[] parts = d.split("\\+");
        if (parts.length != 2) return null;
        try {
            double a = Double.parseDouble(parts[0].trim());
            double b = Double.parseDouble(parts[1].trim());
            if (a <= 0 || b < 0) return null;
            double concentrate = total * a / (a + b);
            return new double[]{concentrate, total - concentrate};
        } catch (Exception e) { return null; }
    }

    private String formatMix(double[] m, double total) {
        return fmt(m[0]) + " ml + " + fmt(m[1]) + " ml acqua  ·  totale " + fmt(total) + " ml";
    }

    private String fmt(double value) {
        if (Math.abs(value - Math.rint(value)) < 0.01) return String.format(Locale.ITALY, "%.0f", value);
        return String.format(Locale.ITALY, "%.1f", value);
    }

    private String key(String s) {
        return s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", "_");
    }

    private String[] splitCsv(String text) {
        if (text == null || text.trim().isEmpty()) return new String[0];
        String[] raw = text.split("[,;]");
        List<String> out = new ArrayList<>();
        for (String s : raw) if (!s.trim().isEmpty()) out.add(s.trim());
        return out.toArray(new String[0]);
    }

    private String join(String[] values) {
        if (values == null || values.length == 0) return "";
        StringBuilder b = new StringBuilder();
        for (String v : values) {
            if (v == null || v.trim().isEmpty()) continue;
            if (b.length() > 0) b.append(", ");
            b.append(v.trim());
        }
        return b.toString();
    }

    private String emptyToNull(String s) {
        if (s == null || s.trim().isEmpty()) return null;
        return s.trim();
    }

    private int roleForType(int which) {
        switch (which) {
            case 0: return ROLE_FILM_DEV;
            case 1: return ROLE_PAPER_DEV;
            case 2: return ROLE_FILM_DEV | ROLE_PAPER_DEV;
            case 3: return ROLE_STOP;
            case 4: return ROLE_FIX;
            default: return ROLE_FILM_DEV;
        }
    }

    private int typeIndexForRole(int role) {
        if ((role & ROLE_FILM_DEV) != 0 && (role & ROLE_PAPER_DEV) != 0) return 2;
        if ((role & ROLE_PAPER_DEV) != 0) return 1;
        if ((role & ROLE_STOP) != 0) return 3;
        if ((role & ROLE_FIX) != 0) return 4;
        return 0;
    }

    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_SHORT).show(); }
    private int dp(float v) { return (int) (v * getResources().getDisplayMetrics().density + 0.5f); }

    private abstract class SimpleItemSelectedListener implements android.widget.AdapterView.OnItemSelectedListener {
        @Override public void onItemSelected(android.widget.AdapterView<?> parent, View view, int position, long id) { selected(position); }
        @Override public void onNothingSelected(android.widget.AdapterView<?> parent) {}
        public abstract void selected(int position);
    }

    private static final class Product {
        final String name;
        final int roles;
        final boolean stockPrep;
        final String[] filmDilutions;
        final String[] paperDilutions;
        final String workingDilution;
        final String stockInstructions;
        final int expiryDays;
        final String sourceUrl;

        Product(String name, int roles, boolean stockPrep, String[] filmDilutions, String[] paperDilutions,
                String workingDilution, String stockInstructions, int expiryDays, String sourceUrl) {
            this.name = name;
            this.roles = roles;
            this.stockPrep = stockPrep;
            this.filmDilutions = filmDilutions == null ? new String[0] : filmDilutions;
            this.paperDilutions = paperDilutions == null ? new String[0] : paperDilutions;
            this.workingDilution = workingDilution;
            this.stockInstructions = stockInstructions;
            this.expiryDays = expiryDays;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
    }

    private static final class FilmStock {
        final String name;
        final int nominalIso;
        final String format;
        final String sourceUrl;

        FilmStock(String name, int nominalIso, String format, String sourceUrl) {
            this.name = name;
            this.nominalIso = nominalIso;
            this.format = format;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }
    }
}
