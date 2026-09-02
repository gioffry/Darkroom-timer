package it.darkroom.assistant;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
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
import android.widget.AdapterView;
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

/**
 * Launcher funzionale del nuovo Darkroom Assistant.
 *
 * Nessun tempo di sviluppo è hardcoded: i tempi vengono cercati online
 * dal DevTimeEngine. Se la combinazione non esiste, l'app lo dice.
 */
public class AssistantActivity extends Activity {
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

    private final Handler handler = new Handler(Looper.getMainLooper());
    private SharedPreferences prefs;
    private int currentScreen = HOME;

    private final Product[] fallbackProducts = new Product[] {
            new Product("Foma Universal", ROLE_FILM_DEV | ROLE_PAPER_DEV, true,
                    new String[]{"1+3"}, new String[]{"1+3"}, null,
                    "Sciogli prima la parte A e poi la parte B in circa 800 ml d'acqua a 50–70 °C; porta infine a 1 litro.",
                    -1, ""),
            new Product("Fomadon R09", ROLE_FILM_DEV, false,
                    new String[]{"1+25", "1+50"}, new String[0], null, null, -1, ""),
            new Product("Fomadon Excel", ROLE_FILM_DEV, true,
                    new String[]{"stock", "1+1"}, new String[0], null,
                    "Prepara la soluzione stock seguendo le istruzioni del produttore.", -1, ""),
            new Product("Ilford ID-11", ROLE_FILM_DEV, true,
                    new String[]{"stock", "1+1", "1+3"}, new String[0], null,
                    "Prepara la soluzione stock seguendo le istruzioni del produttore.", -1, ""),
            new Product("Kodak D-76", ROLE_FILM_DEV, true,
                    new String[]{"stock", "1+1"}, new String[0], null,
                    "Prepara la soluzione stock seguendo le istruzioni del produttore.", -1, ""),
            new Product("Adox Adostop ECO", ROLE_STOP, false,
                    new String[0], new String[0], "1+19", null, -1, ""),
            new Product("Ilford Ilfostop", ROLE_STOP, false,
                    new String[0], new String[0], "1+19", null, -1, ""),
            new Product("Compard Fix Ag Plus", ROLE_FIX, false,
                    new String[0], new String[0], "1+9", null, -1, ""),
            new Product("Ilford Rapid Fixer", ROLE_FIX, false,
                    new String[0], new String[0], "1+4", null, -1, ""),
            new Product("Fomafix", ROLE_FIX, false,
                    new String[0], new String[0], "1+5", null, -1, "")
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

    private final Tank[] tanks = new Tank[] {
            new Tank("JOBO 1510", 140, 1, 0),
            new Tank("JOBO 1520", 240, 2, 2),
            new Tank("JOBO 2520", 270, 2, 2),
            new Tank("JOBO 1540", 470, 4, 2),
            new Tank("JOBO 1520 + 1530", 570, 5, 4)
    };

    private FilmStock selectedFilm;
    private Product selectedFilmDeveloper;
    private Product selectedStop;
    private Product selectedFix;

    private AutoCompleteTextView filmField;
    private TextView filmSearchStatus;
    private EditText isoField;
    private Spinner rollsSpinner;
    private Spinner tankSpinner;
    private Spinner developerSpinner;
    private Spinner dilutionSpinner;
    private EditText temperatureField;
    private Spinner stopSpinner;
    private Spinner fixSpinner;
    private LinearLayout filmResultBox;
    private List<Tank> compatibleTanks = new ArrayList<>();

    private Spinner paperDeveloperSpinner;
    private Spinner paperStopSpinner;
    private Spinner paperFixSpinner;
    private Spinner paperDeveloperDilutionSpinner;
    private EditText paperVolumeField;
    private LinearLayout paperResultBox;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Window w = getWindow();
        w.setStatusBarColor(BG);
        w.setNavigationBarColor(BG);
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

        List<String> names = new ArrayList<>(getInventory());
        Collections.sort(names, String::compareToIgnoreCase);
        if (names.isEmpty()) {
            TextView empty = label("Nessun prodotto in magazzino.", 15, MUTED, false);
            empty.setPadding(dp(4), dp(18), dp(4), dp(18));
            page.addView(empty);
        } else {
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
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this,
                android.R.layout.simple_dropdown_item_1line, suggestions);
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
                    List<OnlineCatalogSearch.SearchResult> results =
                            OnlineCatalogSearch.searchChemicals(q);
                    runOnUiThread(() -> {
                        if (myGen != generation[0]) return;
                        if (!q.equalsIgnoreCase(search.getText().toString().trim())) return;
                        LinkedHashSet<String> merged = new LinkedHashSet<>(localProductMatches(q));
                        online.clear();
                        for (OnlineCatalogSearch.SearchResult r : results) {
                            if (r.title == null || r.title.trim().length() < 3) continue;
                            merged.add(r.title);
                            online.put(r.title.toLowerCase(Locale.ROOT), r);
                        }
                        replaceSuggestions(adapter, new ArrayList<>(merged));
                        status.setText(results.isEmpty()
                                ? "Online: nessun risultato. Mostro i dati locali disponibili."
                                : "Online: " + results.size() + " risultati trovati.");
                        search.showDropDown();
                    });
                }).start();
                handler.postDelayed(pending[0], 350);
            }
        });

        final String[] chosen = new String[1];
        search.setOnItemClickListener((parent, view, position, id) ->
                chosen[0] = String.valueOf(parent.getItemAtPosition(position)));

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Aggiungi prodotto")
                .setView(wrap)
                .setNegativeButton("ANNULLA", null)
                .setPositiveButton("AGGIUNGI", null)
                .create();

        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String name = chosen[0] != null ? chosen[0] :
                            search.getText().toString().trim();
                    Product local = findProduct(name);
                    if (local != null) {
                        dialog.dismiss();
                        startProductAddFlow(local);
                        return;
                    }
                    OnlineCatalogSearch.SearchResult r =
                            online.get(name.toLowerCase(Locale.ROOT));
                    if (r == null) {
                        toast("Seleziona uno dei risultati proposti.");
                        return;
                    }
                    dialog.dismiss();
                    toast("Recupero la scheda online…");
                    new Thread(() -> {
                        OnlineCatalogSearch.ChemicalData data =
                                OnlineCatalogSearch.enrichChemical(r);
                        runOnUiThread(() -> {
                            Product p = new Product(
                                    cleanSearchTitle(data.name),
                                    data.roles,
                                    data.stockPrep,
                                    data.filmDilutions,
                                    data.paperDilutions,
                                    data.workingDilution,
                                    data.stockInstructions,
                                    data.expiryDays,
                                    data.sourceUrl
                            );
                            if (p.roles == 0) chooseProductTypeThenAdd(p);
                            else startProductAddFlow(p);
                        });
                    }).start();
                }));
        dialog.show();
    }

    private void chooseProductTypeThenAdd(Product p) {
        String[] types = new String[]{
                "Rivelatore pellicola",
                "Rivelatore carta",
                "Rivelatore pellicola + carta",
                "Arresto",
                "Fissaggio"
        };
        new AlertDialog.Builder(this)
                .setTitle("Tipo non riconosciuto")
                .setMessage("La fonte online non consente di classificare il prodotto con sufficiente sicurezza.")
                .setItems(types, (d, which) -> {
                    Product fixed = p.withRole(roleForType(which));
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
                },
                now.get(Calendar.YEAR),
                now.get(Calendar.MONTH),
                now.get(Calendar.DAY_OF_MONTH));
        picker.setTitle(p.stockPrep ? "Data preparazione stock" : "Data apertura");
        picker.show();
    }

    private void showProductDetails(String name) {
        Product p = findProduct(name);
        long opened = prefs.getLong("opened_" + key(name), 0L);
        String expiry = "Scadenza non determinabile";
        if (p != null && p.expiryDays > 0 && opened > 0) {
            long expires = opened + p.expiryDays * 86400000L;
            expiry = "Scadenza: " +
                    new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY).format(new Date(expires));
        }

        StringBuilder msg = new StringBuilder(expiry);
        if (p != null && p.sourceUrl != null && !p.sourceUrl.isEmpty()) {
            msg.append("\n\nFonte online disponibile");
        }

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
        dialog.setOnShowListener(d -> {
            if (p != null && p.sourceUrl != null && !p.sourceUrl.isEmpty()) {
                dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setOnLongClickListener(v -> {
                    openUrl(p.sourceUrl);
                    return true;
                });
            }
        });
        dialog.show();
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

        String[] types = new String[]{
                "Rivelatore pellicola",
                "Rivelatore carta",
                "Rivelatore pellicola + carta",
                "Arresto",
                "Fissaggio"
        };
        Spinner type = spinner(types);
        type.setSelection(typeIndexForRole(p.roles));
        box.addView(fieldBlock("TIPO", type));

        EditText filmDil = edit(join(p.filmDilutions), InputType.TYPE_CLASS_TEXT);
        box.addView(fieldBlock("DILUIZIONI PELLICOLA", filmDil));

        EditText paperDil = edit(join(p.paperDilutions), InputType.TYPE_CLASS_TEXT);
        box.addView(fieldBlock("DILUIZIONI CARTA", paperDil));

        EditText working = edit(p.workingDilution == null ? "" : p.workingDilution,
                InputType.TYPE_CLASS_TEXT);
        box.addView(fieldBlock("DILUIZIONE ARRESTO / FIX", working));

        CheckBox stock = new CheckBox(this);
        stock.setText("Richiede preparazione stock");
        stock.setTextColor(WHITE);
        stock.setChecked(p.stockPrep);
        box.addView(stock);
        box.addView(space(10));

        EditText date = edit(opened > 0 ? df.format(new Date(opened)) : "",
                InputType.TYPE_CLASS_DATETIME);
        box.addView(fieldBlock("DATA APERTURA / PREPARAZIONE", date));

        EditText expiryDays = edit(p.expiryDays > 0 ? String.valueOf(p.expiryDays) : "",
                InputType.TYPE_CLASS_NUMBER);
        box.addView(fieldBlock("DURATA DOPO APERTURA (giorni)", expiryDays));

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Modifica prodotto")
                .setView(scroll(box))
                .setNegativeButton("ANNULLA", null)
                .setPositiveButton("SALVA", null)
                .create();

        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String newName = name.getText().toString().trim();
                    if (newName.isEmpty()) {
                        toast("Inserisci il nome.");
                        return;
                    }
                    long newOpened = opened;
                    try {
                        if (!date.getText().toString().trim().isEmpty()) {
                            newOpened = df.parse(date.getText().toString().trim()).getTime();
                        }
                    } catch (Exception ex) {
                        toast("Data non valida.");
                        return;
                    }
                    int exp = -1;
                    try {
                        if (!expiryDays.getText().toString().trim().isEmpty()) {
                            exp = Integer.parseInt(expiryDays.getText().toString().trim());
                        }
                    } catch (Exception ex) {
                        toast("Durata non valida.");
                        return;
                    }

                    Product edited = new Product(
                            newName,
                            roleForType(type.getSelectedItemPosition()),
                            stock.isChecked(),
                            splitCsv(filmDil.getText().toString()),
                            splitCsv(paperDil.getText().toString()),
                            emptyToNull(working.getText().toString()),
                            p.stockInstructions,
                            exp,
                            p.sourceUrl
                    );
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

        LinearLayout page = page("Sviluppo pellicola",
                "Pellicola, chimica, tank e tempo JOBO CPE2.");

        filmField = new AutoCompleteTextView(this);
        filmField.setThreshold(3);
        filmField.setHint("Scrivi almeno 3 lettere…");
        styleInput(filmField);

        List<String> suggestions = new ArrayList<>();
        ArrayAdapter<String> filmAdapter = new ArrayAdapter<>(this,
                android.R.layout.simple_dropdown_item_1line, suggestions);
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

        rollsSpinner = spinner(new String[]{"1", "2", "3", "4", "5"});
        page.addView(fieldBlock("NUMERO RULLI", rollsSpinner));

        tankSpinner = spinner(new String[]{"Seleziona prima la pellicola"});
        page.addView(fieldBlock("TANK JOBO", tankSpinner));

        List<Product> developers = inventoryProductsByRole(ROLE_FILM_DEV);
        developerSpinner = productSpinner(developers,
                "Nessun rivelatore in magazzino");
        page.addView(fieldBlock("RIVELATORE", developerSpinner));

        dilutionSpinner = spinner(new String[]{"—"});
        page.addView(fieldBlock("DILUIZIONE", dilutionSpinner));

        temperatureField = new EditText(this);
        temperatureField.setInputType(InputType.TYPE_CLASS_NUMBER |
                InputType.TYPE_NUMBER_FLAG_DECIMAL);
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
                String[] ds = selectedFilmDeveloper == null ||
                        selectedFilmDeveloper.filmDilutions.length == 0
                        ? new String[]{"—"}
                        : selectedFilmDeveloper.filmDilutions;
                setSpinnerItems(dilutionSpinner, ds);
            }
        });

        stopSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                selectedStop = productAt(stops, position);
            }
        });

        fixSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                selectedFix = productAt(fixes, position);
            }
        });

        rollsSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                updateCompatibleTanks();
            }
        });

        wireFilmSearch(filmField, filmAdapter, onlineFilms);
        filmField.setOnItemClickListener((parent, view, position, id) -> {
            String display = String.valueOf(parent.getItemAtPosition(position));
            FilmStock local = findFilm(display);
            if (local != null) {
                selectFilm(local);
                return;
            }

            OnlineCatalogSearch.SearchResult r =
                    onlineFilms.get(display.toLowerCase(Locale.ROOT));
            if (r == null) return;

            selectedFilm = null;
            isoField.setText("");
            filmSearchStatus.setText("Recupero ISO e formato dalla fonte online…");
            new Thread(() -> {
                OnlineCatalogSearch.FilmData fd = OnlineCatalogSearch.enrichFilm(r);
                runOnUiThread(() -> finishOnlineFilmSelection(fd));
            }).start();
        });

        Button calc = actionButton("CALCOLA", BURGUNDY);
        calc.setOnClickListener(v -> calculateFilmOnline());
        page.addView(space(6));
        page.addView(calc);
        page.addView(space(16));

        filmResultBox = new LinearLayout(this);
        filmResultBox.setOrientation(LinearLayout.VERTICAL);
        page.addView(filmResultBox);
        page.addView(space(80));

        setContentView(scroll(page));
    }

    private void wireFilmSearch(AutoCompleteTextView field,
                                ArrayAdapter<String> adapter,
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
                    if (filmSearchStatus != null) {
                        filmSearchStatus.setText("Ricerca online dopo 3 lettere.");
                    }
                    return;
                }

                replaceSuggestions(adapter, localFilmMatches(q));
                if (filmSearchStatus != null) filmSearchStatus.setText("Cerco online…");

                pending[0] = () -> new Thread(() -> {
                    List<OnlineCatalogSearch.SearchResult> results =
                            OnlineCatalogSearch.searchFilms(q);
                    runOnUiThread(() -> {
                        if (myGen != generation[0]) return;
                        if (!q.equalsIgnoreCase(field.getText().toString().trim())) return;

                        LinkedHashSet<String> merged =
                                new LinkedHashSet<>(localFilmMatches(q));
                        online.clear();
                        for (OnlineCatalogSearch.SearchResult r : results) {
                            merged.add(r.title);
                            online.put(r.title.toLowerCase(Locale.ROOT), r);
                        }
                        replaceSuggestions(adapter, new ArrayList<>(merged));

                        if (filmSearchStatus != null) {
                            filmSearchStatus.setText(results.isEmpty()
                                    ? "Online: nessun risultato. Mostro i dati locali disponibili."
                                    : "Online: " + results.size() + " risultati trovati.");
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
        String name = cleanSearchTitle(fd.name);

        if (fd.format == null) {
            new AlertDialog.Builder(this)
                    .setTitle(name)
                    .setMessage("La fonte non indica il formato in modo univoco. Scegli il formato del rullo.")
                    .setItems(new String[]{"35 mm", "120"}, (d, which) -> {
                        FilmStock f = new FilmStock(
                                name + (which == 0 ? " — 35 mm" : " — 120"),
                                fd.iso,
                                which == 0 ? "35" : "120",
                                fd.sourceUrl);
                        selectFilm(f);
                    })
                    .show();
        } else {
            String suffix = fd.format.equals("35") ? " — 35 mm" : " — 120";
            FilmStock f = new FilmStock(
                    hasFormatSuffix(name) ? name : name + suffix,
                    fd.iso,
                    fd.format,
                    fd.sourceUrl);
            selectFilm(f);
        }
    }

    private void selectFilm(FilmStock f) {
        selectedFilm = f;
        filmField.setText(f.name, false);
        isoField.setText(f.nominalIso > 0 ? String.valueOf(f.nominalIso) : "");
        filmSearchStatus.setText(f.sourceUrl == null || f.sourceUrl.isEmpty()
                ? "Scheda locale; il tempo verrà comunque cercato online."
                : "Scheda pellicola recuperata online.");
        updateCompatibleTanks();
    }

    private void updateCompatibleTanks() {
        if (tankSpinner == null) return;
        compatibleTanks.clear();

        if (selectedFilm == null) {
            setSpinnerItems(tankSpinner, new String[]{"Seleziona prima la pellicola"});
            return;
        }

        int rolls = 1;
        try {
            rolls = Integer.parseInt(String.valueOf(rollsSpinner.getSelectedItem()));
        } catch (Exception ignored) {}

        for (Tank t : tanks) {
            int cap = "120".equals(selectedFilm.format) ? t.max120 : t.max35;
            if (cap >= rolls && t.rotaryMl <= 600) compatibleTanks.add(t);
        }

        if (compatibleTanks.isEmpty()) {
            setSpinnerItems(tankSpinner, new String[]{"Nessuna tank CPE2 compatibile"});
            return;
        }

        List<String> labels = new ArrayList<>();
        int defaultIndex = 0;
        for (int i = 0; i < compatibleTanks.size(); i++) {
            Tank t = compatibleTanks.get(i);
            labels.add(t.name + " — " + t.rotaryMl + " ml");
            if ("JOBO 2520".equals(t.name)) defaultIndex = i;
        }
        setSpinnerItems(tankSpinner, labels.toArray(new String[0]));
        tankSpinner.setSelection(defaultIndex);
    }

    private Tank selectedTank() {
        if (compatibleTanks.isEmpty()) return null;
        int i = tankSpinner.getSelectedItemPosition();
        if (i < 0 || i >= compatibleTanks.size()) return null;
        return compatibleTanks.get(i);
    }

    private void calculateFilmOnline() {
        if (selectedFilm == null) {
            selectedFilm = findFilm(filmField.getText().toString().trim());
        }
        if (selectedFilm == null) {
            toast("Seleziona una pellicola dai suggerimenti.");
            return;
        }
        if (selectedFilmDeveloper == null) {
            toast("Aggiungi e seleziona un rivelatore dal magazzino.");
            return;
        }
        if (selectedStop == null || selectedFix == null) {
            toast("Aggiungi arresto e fissaggio al magazzino.");
            return;
        }

        Tank tank = selectedTank();
        if (tank == null) {
            resultFilmError("Nessuna tank compatibile con questa configurazione.");
            return;
        }

        int iso;
        double temp;
        try {
            iso = Integer.parseInt(isoField.getText().toString().trim());
            temp = Double.parseDouble(
                    temperatureField.getText().toString().trim().replace(',', '.'));
        } catch (Exception e) {
            toast("Controlla ISO e temperatura.");
            return;
        }

        String dilution = String.valueOf(dilutionSpinner.getSelectedItem());
        if ("—".equals(dilution)) {
            toast("La diluizione del rivelatore non è disponibile. Modifica la scheda prodotto.");
            return;
        }

        double[] devMix = mix(tank.rotaryMl, dilution);
        double[] stopMix = mix(tank.rotaryMl, selectedStop.workingDilution);
        double[] fixMix = mix(tank.rotaryMl, selectedFix.workingDilution);
        if (devMix == null || stopMix == null || fixMix == null) {
            resultFilmError("Una diluizione non è calcolabile. Correggi la scheda del prodotto.");
            return;
        }

        filmResultBox.removeAllViews();
        resultLine(filmResultBox, "RICERCA TEMPO", "Cerco online la combinazione esatta…");
        resultLine(filmResultBox, "TANK", tank.name + " · rotazione " + tank.rotaryMl + " ml");
        resultLine(filmResultBox, "RIVELATORE", formatMix(devMix, tank.rotaryMl));
        resultLine(filmResultBox, "ARRESTO", formatMix(stopMix, tank.rotaryMl));
        resultLine(filmResultBox, "FISSAGGIO", formatMix(fixMix, tank.rotaryMl));

        final String filmName = selectedFilm.name;
        final String format = selectedFilm.format;
        final String filmSource = selectedFilm.sourceUrl;
        final String developerName = selectedFilmDeveloper.name;
        final String developerSource = selectedFilmDeveloper.sourceUrl;

        new Thread(() -> {
            DevTimeEngine.Result result = DevTimeEngine.lookup(
                    filmName,
                    format,
                    developerName,
                    dilution,
                    iso,
                    temp,
                    filmSource,
                    developerSource
            );
            runOnUiThread(() -> showDevelopmentResult(
                    result, tank, devMix, stopMix, fixMix));
        }).start();
    }

    private void showDevelopmentResult(DevTimeEngine.Result result,
                                       Tank tank,
                                       double[] devMix,
                                       double[] stopMix,
                                       double[] fixMix) {
        filmResultBox.removeAllViews();

        if (!result.found) {
            resultLine(filmResultBox, "TEMPO JOBO CPE2", "Tempo non disponibile");
            TextView why = label(result.diagnostic, 13, MUTED, false);
            why.setPadding(dp(4), dp(8), dp(4), dp(18));
            filmResultBox.addView(why);
        } else {
            resultLine(filmResultBox, "TEMPO JOBO CPE2", result.finalDisplay());
            resultLine(filmResultBox, "DATO ORIGINALE",
                    result.baseDisplay() + " @ " + fmtTemp(result.baseTemperature) +
                            " · ISO " + result.sourceIso + " · " +
                            ("120".equals(result.format) ? "120" : "35 mm"));

            String conversion = result.temperatureConverted
                    ? "Temperatura: compensazione Ilford → " +
                    fmtTemp(result.targetTemperature) + "\n"
                    : "Temperatura: dato usato alla temperatura originale\n";
            conversion += "JOBO CPE2: rotazione continua, adattamento −15%";
            resultLine(filmResultBox, "ADATTAMENTI", conversion);

            TextView src = label(
                    "Fonte: " + result.sourceName + "\n" +
                            result.sourceFilm + " · " +
                            result.sourceDeveloper + " · " +
                            result.sourceDilution + "\n" +
                            result.diagnostic,
                    13, MUTED, false);
            src.setPadding(dp(4), dp(8), dp(4), dp(12));
            filmResultBox.addView(src);

            if (result.sourceUrl != null && !result.sourceUrl.isEmpty()) {
                Button open = smallButton("APRI FONTE");
                open.setOnClickListener(v -> openUrl(result.sourceUrl));
                filmResultBox.addView(open);
                filmResultBox.addView(space(10));
            }

            if (result.warning != null && !result.warning.isEmpty()) {
                TextView warn = label(result.warning, 13, WHITE, true);
                warn.setPadding(dp(14), dp(12), dp(14), dp(12));
                warn.setBackground(bg(BURGUNDY, 12, 0, 0));
                filmResultBox.addView(warn);
                filmResultBox.addView(space(10));
            }
        }

        resultLine(filmResultBox, "TANK",
                tank.name + " · volume rotazione " + tank.rotaryMl + " ml");
        resultLine(filmResultBox, "RIVELATORE", formatMix(devMix, tank.rotaryMl));
        resultLine(filmResultBox, "ARRESTO", formatMix(stopMix, tank.rotaryMl));
        resultLine(filmResultBox, "FISSAGGIO", formatMix(fixMix, tank.rotaryMl));
    }

    private void showPaper() {
        currentScreen = PAPER;
        LinearLayout page = page("Stampa carta", "Prepara i bagni per la stampa.");

        List<Product> developers = inventoryProductsByRole(ROLE_PAPER_DEV);
        List<Product> stops = inventoryProductsByRole(ROLE_STOP);
        List<Product> fixes = inventoryProductsByRole(ROLE_FIX);

        paperDeveloperSpinner = productSpinner(developers,
                "Nessun rivelatore carta in magazzino");
        paperStopSpinner = productSpinner(stops, "Nessun arresto in magazzino");
        paperFixSpinner = productSpinner(fixes, "Nessun fissaggio in magazzino");
        paperDeveloperDilutionSpinner = spinner(new String[]{"—"});

        page.addView(fieldBlock("RIVELATORE CARTA", paperDeveloperSpinner));
        page.addView(fieldBlock("DILUIZIONE RIVELATORE", paperDeveloperDilutionSpinner));
        page.addView(fieldBlock("ARRESTO", paperStopSpinner));
        page.addView(fieldBlock("FISSAGGIO", paperFixSpinner));

        paperDeveloperSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                Product p = productAt(developers, position);
                String[] ds = p == null || p.paperDilutions.length == 0
                        ? new String[]{"—"} : p.paperDilutions;
                setSpinnerItems(paperDeveloperDilutionSpinner, ds);
            }
        });

        paperVolumeField = new EditText(this);
        paperVolumeField.setInputType(InputType.TYPE_CLASS_NUMBER |
                InputType.TYPE_NUMBER_FLAG_DECIMAL);
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

    private void calculatePaper(List<Product> developers,
                                List<Product> stops,
                                List<Product> fixes) {
        Product dev = productAt(developers,
                paperDeveloperSpinner.getSelectedItemPosition());
        Product stop = productAt(stops,
                paperStopSpinner.getSelectedItemPosition());
        Product fix = productAt(fixes,
                paperFixSpinner.getSelectedItemPosition());

        if (dev == null || stop == null || fix == null) {
            toast("Aggiungi rivelatore carta, arresto e fissaggio al magazzino.");
            return;
        }

        double volume;
        try {
            volume = Double.parseDouble(
                    paperVolumeField.getText().toString().trim().replace(',', '.'));
            if (volume <= 0) throw new NumberFormatException();
        } catch (Exception e) {
            toast("Inserisci un volume valido.");
            return;
        }

        String devDilution = String.valueOf(
                paperDeveloperDilutionSpinner.getSelectedItem());
        if ("—".equals(devDilution)) {
            toast("Diluizione rivelatore carta non disponibile: modifica la scheda.");
            return;
        }

        double[] devMix = mix(volume, devDilution);
        double[] stopMix = mix(volume, stop.workingDilution);
        double[] fixMix = mix(volume, fix.workingDilution);

        if (devMix == null || stopMix == null || fixMix == null) {
            toast("Una diluizione non è calcolabile: modifica la scheda del prodotto.");
            return;
        }

        paperResultBox.removeAllViews();
        resultLine(paperResultBox, "RIVELATORE",
                devDilution + " · " + formatMix(devMix, volume));
        resultLine(paperResultBox, "ARRESTO",
                stop.workingDilution + " · " + formatMix(stopMix, volume));
        resultLine(paperResultBox, "FISSAGGIO",
                fix.workingDilution + " · " + formatMix(fixMix, volume));
    }

    private Set<String> getInventory() {
        return new HashSet<>(prefs.getStringSet("inventory", new HashSet<>()));
    }

    private void addToInventory(Product p, long openedMillis) {
        saveProductMetadata(p);
        Set<String> set = getInventory();
        set.add(p.name);
        prefs.edit()
                .putStringSet("inventory", set)
                .putLong("opened_" + key(p.name), openedMillis)
                .apply();
    }

    private void replaceInventoryProduct(String oldName,
                                         Product p,
                                         long openedMillis) {
        Set<String> set = getInventory();
        set.remove(oldName);
        set.add(p.name);

        SharedPreferences.Editor ed = prefs.edit()
                .putStringSet("inventory", set)
                .remove("opened_" + key(oldName))
                .putLong("opened_" + key(p.name), openedMillis);
        ed.apply();

        if (!oldName.equalsIgnoreCase(p.name)) deleteProductMetadata(oldName);
        saveProductMetadata(p);
    }

    private void removeFromInventory(String name) {
        Set<String> set = getInventory();
        set.remove(name);
        prefs.edit()
                .putStringSet("inventory", set)
                .remove("opened_" + key(name))
                .apply();
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
                .putString("prod_working_" + k,
                        p.workingDilution == null ? "" : p.workingDilution)
                .putString("prod_instructions_" + k,
                        p.stockInstructions == null ? "" : p.stockInstructions)
                .putInt("prod_expiry_" + k, p.expiryDays)
                .putString("prod_source_" + k,
                        p.sourceUrl == null ? "" : p.sourceUrl)
                .apply();
    }

    private void deleteProductMetadata(String name) {
        String k = key(name);
        prefs.edit()
                .remove("prod_saved_" + k)
                .remove("prod_name_" + k)
                .remove("prod_roles_" + k)
                .remove("prod_stock_" + k)
                .remove("prod_film_" + k)
                .remove("prod_paper_" + k)
                .remove("prod_working_" + k)
                .remove("prod_instructions_" + k)
                .remove("prod_expiry_" + k)
                .remove("prod_source_" + k)
                .apply();
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

    private Product findProduct(String name) {
        if (name == null) return null;
        Product saved = loadSavedProduct(name.trim());
        if (saved != null) return saved;
        for (Product p : fallbackProducts) {
            if (p.name.equalsIgnoreCase(name.trim())) return p;
        }
        return null;
    }

    private FilmStock findFilm(String name) {
        if (name == null) return null;
        for (FilmStock f : fallbackFilms) {
            if (f.name.equalsIgnoreCase(name.trim())) return f;
        }
        return null;
    }

    private Product productAt(List<Product> list, int position) {
        if (list == null || list.isEmpty() ||
                position < 0 || position >= list.size()) return null;
        return list.get(position);
    }

    private List<String> localProductMatches(String q) {
        String needle = q.toLowerCase(Locale.ROOT);
        LinkedHashSet<String> out = new LinkedHashSet<>();
        for (Product p : fallbackProducts) {
            if (p.name.toLowerCase(Locale.ROOT).contains(needle)) out.add(p.name);
        }
        for (String name : getInventory()) {
            if (name.toLowerCase(Locale.ROOT).contains(needle)) out.add(name);
        }
        return new ArrayList<>(out);
    }

    private List<String> localFilmMatches(String q) {
        String needle = q.toLowerCase(Locale.ROOT);
        List<String> out = new ArrayList<>();
        for (FilmStock f : fallbackFilms) {
            if (f.name.toLowerCase(Locale.ROOT).contains(needle)) out.add(f.name);
        }
        return out;
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

        Product(String name,
                int roles,
                boolean stockPrep,
                String[] filmDilutions,
                String[] paperDilutions,
                String workingDilution,
                String stockInstructions,
                int expiryDays,
                String sourceUrl) {
            this.name = name;
            this.roles = roles;
            this.stockPrep = stockPrep;
            this.filmDilutions = filmDilutions == null ?
                    new String[0] : filmDilutions;
            this.paperDilutions = paperDilutions == null ?
                    new String[0] : paperDilutions;
            this.workingDilution = workingDilution;
            this.stockInstructions = stockInstructions;
            this.expiryDays = expiryDays;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
        }

        Product withRole(int role) {
            return new Product(name, role, stockPrep,
                    filmDilutions, paperDilutions, workingDilution,
                    stockInstructions, expiryDays, sourceUrl);
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

    private static final class Tank {
        final String name;
        final int rotaryMl;
        final int max35;
        final int max120;

        Tank(String name, int rotaryMl, int max35, int max120) {
            this.name = name;
            this.rotaryMl = rotaryMl;
            this.max35 = max35;
            this.max120 = max120;
        }
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
        TextView card = label(text + "                                  ›",
                23, WHITE, true);
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
        if (products.isEmpty()) names.add(emptyLabel);
        else for (Product p : products) names.add(p.name);
        return spinner(names.toArray(new String[0]));
    }

    private void setSpinnerItems(Spinner spinner, String[] items) {
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(
                this, android.R.layout.simple_spinner_item, items) {
            @Override
            public View getView(int position, View convertView, ViewGroup parent) {
                TextView t = (TextView) super.getView(position, convertView, parent);
                t.setTextColor(WHITE);
                t.setTextSize(16);
                t.setPadding(dp(10), dp(10), dp(10), dp(10));
                return t;
            }
        };
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);
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

    private Button smallButton(String text) {
        Button b = actionButton(text, CARD_2);
        b.setMinHeight(dp(48));
        b.setTextSize(14);
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
        LinearLayout r = new LinearLayout(this);
        r.setOrientation(LinearLayout.VERTICAL);
        r.setPadding(dp(18), dp(14), dp(18), dp(14));
        r.setBackground(bg(CARD, 13, BORDER, 1));
        r.addView(label(labelText, 12, MUTED, false));
        r.addView(space(5));
        r.addView(label(value, 18, WHITE, true));
        parent.addView(r);
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
        t.setTypeface(Typeface.DEFAULT,
                bold ? Typeface.BOLD : Typeface.NORMAL);
        return t;
    }

    private View space(int value) {
        View v = new View(this);
        v.setLayoutParams(new LinearLayout.LayoutParams(1, dp(value)));
        return v;
    }

    private GradientDrawable bg(int color, int radiusDp,
                                int strokeColor, int strokeDp) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(radiusDp));
        if (strokeDp > 0) g.setStroke(dp(strokeDp), strokeColor);
        return g;
    }

    private void replaceSuggestions(ArrayAdapter<String> adapter,
                                    List<String> values) {
        adapter.clear();
        adapter.addAll(values);
        adapter.notifyDataSetChanged();
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
        } catch (Exception e) {
            return null;
        }
    }

    private String formatMix(double[] m, double total) {
        return fmt(m[0]) + " ml + " + fmt(m[1]) +
                " ml acqua · totale " + fmt(total) + " ml";
    }

    private String fmt(double value) {
        if (Math.abs(value - Math.rint(value)) < 0.01) {
            return String.format(Locale.ITALY, "%.0f", value);
        }
        return String.format(Locale.ITALY, "%.1f", value);
    }

    private String fmtTemp(double value) {
        if (Math.abs(value - Math.rint(value)) < 0.01) {
            return String.format(Locale.ITALY, "%.0f °C", value);
        }
        return String.format(Locale.ITALY, "%.1f °C", value);
    }

    private String key(String s) {
        return s.toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9]+", "_");
    }

    private String[] splitCsv(String text) {
        if (text == null || text.trim().isEmpty()) return new String[0];
        String[] raw = text.split("[,;]");
        List<String> out = new ArrayList<>();
        for (String s : raw) {
            if (!s.trim().isEmpty()) out.add(s.trim());
        }
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
        if ((role & ROLE_FILM_DEV) != 0 &&
                (role & ROLE_PAPER_DEV) != 0) return 2;
        if ((role & ROLE_PAPER_DEV) != 0) return 1;
        if ((role & ROLE_STOP) != 0) return 3;
        if ((role & ROLE_FIX) != 0) return 4;
        return 0;
    }

    private boolean hasFormatSuffix(String s) {
        String x = s.toLowerCase(Locale.ROOT).trim();
        return x.endsWith("35 mm") || x.endsWith("120");
    }

    private String cleanSearchTitle(String s) {
        if (s == null) return "";
        String out = s.replaceAll("\\s*[-–—|]\\s*(official|product|developer|film|fotoimpex|amazon).*$", "");
        return out.trim();
    }

    private void openUrl(String url) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (Exception e) {
            toast("Impossibile aprire la fonte.");
        }
    }

    private void resultFilmError(String message) {
        if (filmResultBox == null) return;
        filmResultBox.removeAllViews();
        TextView t = label(message, 15, WHITE, true);
        t.setPadding(dp(16), dp(16), dp(16), dp(16));
        t.setBackground(bg(BURGUNDY, 14, 0, 0));
        filmResultBox.addView(t);
    }

    private void toast(String s) {
        Toast.makeText(this, s, Toast.LENGTH_SHORT).show();
    }

    private int dp(float v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }

    private abstract class SimpleItemSelectedListener
            implements AdapterView.OnItemSelectedListener {
        @Override
        public void onItemSelected(AdapterView<?> parent,
                                   View view,
                                   int position,
                                   long id) {
            selected(position);
        }

        @Override
        public void onNothingSelected(AdapterView<?> parent) {}

        public abstract void selected(int position);
    }
}
