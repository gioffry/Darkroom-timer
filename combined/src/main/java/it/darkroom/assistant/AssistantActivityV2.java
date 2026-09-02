package it.darkroom.assistant;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DatePickerDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
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
 * Darkroom Assistant funzionale.
 * - catalogo prodotti/pellicole con ricerca online
 * - preparazione stock recuperata dalla fonte quando possibile
 * - magazzino modificabile
 * - motore tempi online + adattamento JOBO CPE2
 * - diluizioni dev/stop/fix
 * - capacità e riutilizzo dei bagni con registro uso
 */
public class AssistantActivityV2 extends Activity {
    private static final int HOME = 0;
    private static final int PRODUCTS = 1;
    private static final int FILM = 2;
    private static final int PAPER = 3;

    private static final int ROLE_FILM_DEV = 1;
    private static final int ROLE_PAPER_DEV = 2;
    private static final int ROLE_STOP = 4;
    private static final int ROLE_FIX = 8;
    private static final int ROLE_WETTING = 16;
    private static final int ROLE_WASHING = 32;
    private static final int ROLE_CHEMISTRY = 64;
    private static final int REUSE_FRESH_RECOMMENDED = 3;

    private static final int BG = Color.rgb(0, 0, 0);
    private static final int WHITE = Color.rgb(246, 243, 238);
    private static final int MUTED = Color.rgb(170, 166, 162);
    private static final int BURGUNDY = Color.rgb(124, 31, 31);
    private static final int BURGUNDY_BRIGHT = Color.rgb(167, 43, 38);
    private static final int CARD = Color.rgb(24, 24, 24);
    private static final int CARD_2 = Color.rgb(32, 32, 32);
    private static final int TAUPE = Color.rgb(48, 44, 41);
    private static final int BORDER = Color.rgb(67, 67, 67);

    private final Handler handler = new Handler(Looper.getMainLooper());
    private SharedPreferences prefs;
    private int currentScreen = HOME;

    private final Product[] fallbackProducts = new Product[]{
            new Product("Foma Universal", ROLE_FILM_DEV | ROLE_PAPER_DEV, true,
                    new String[]{"1+3"}, new String[]{"1+3"}, null,
                    "Sciogli prima la parte A e poi la parte B in circa 800 ml d'acqua a 50–70 °C; porta infine a 1 litro.",
                    -1, "", ChemistrySpecEngine.REUSE_ONE_SHOT, -1, -1),
            new Product("Fomadon R09", ROLE_FILM_DEV, false,
                    new String[]{"1+25", "1+50"}, new String[0], null,
                    null, -1, "", ChemistrySpecEngine.REUSE_ONE_SHOT, -1, -1),
            new Product("Fomadon Excel", ROLE_FILM_DEV, true,
                    new String[]{"stock", "1+1"}, new String[0], null,
                    null, -1, "", ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1),
            new Product("Ilford ID-11", ROLE_FILM_DEV, true,
                    new String[]{"stock", "1+1", "1+3"}, new String[0], null,
                    null, -1, "", ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1),
            new Product("Kodak D-76", ROLE_FILM_DEV, true,
                    new String[]{"stock", "1+1"}, new String[0], null,
                    null, -1, "", ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1),
            new Product("Adox Adostop ECO", ROLE_STOP, false,
                    new String[0], new String[0], "1+19",
                    null, -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Ilford Ilfostop", ROLE_STOP, false,
                    new String[0], new String[0], "1+19",
                    null, -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Compard Fix Ag Plus", ROLE_FIX, false,
                    new String[0], new String[0], "1+9",
                    null, -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Ilford Rapid Fixer", ROLE_FIX, false,
                    new String[0], new String[0], "1+4",
                    null, -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1),
            new Product("Fomafix", ROLE_FIX, false,
                    new String[0], new String[0], "1+5",
                    null, -1, "", ChemistrySpecEngine.REUSE_REUSABLE, -1, -1)
    };

    private final Product[] curatedAuxChemistry = new Product[]{
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
                    new String[]{"1+4"}, new String[]{"1+9"}, "1+4", null,
                    90, "", ChemistrySpecEngine.REUSE_REUSABLE, 20, 2.1),
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

    private final FilmStock[] fallbackFilms = new FilmStock[]{
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

    private final Tank[] tanks = new Tank[]{
            // 4x5: la 2520 usa la spirale/loader 2509N, fino a 6 lastre in rotazione.
            new Tank("JOBO 2520", 270, 2, 1, 6),
            // La 2563 resta visibile per i formati a rullo, ma 850 ml supera il limite CPE2.
            new Tank("JOBO 2563", 850, 6, 8, 0)
    };

    private FilmStock selectedFilm;
    private Product selectedFilmDeveloper;
    private Product selectedStop;
    private Product selectedFix;
    private AutoCompleteTextView filmField;
    private TextView filmSearchStatus;
    private LinearLayout filmSuggestionsBox;
    private EditText isoField;
    private Spinner rollsSpinner;
    private TextView filmCountLabel;
    private Spinner tankSpinner;
    private Spinner formatSpinner;
    private Spinner developerSpinner;
    private Spinner dilutionSpinner;
    private EditText temperatureField;
    private Spinner stopSpinner;
    private Spinner fixSpinner;
    private LinearLayout filmResultBox;
    private LinearLayout filmCapacityBox;
    private final List<Tank> compatibleTanks = new ArrayList<>();
    private Tank lastFilmTank;
    private int lastFilmRolls;

    private Spinner paperDeveloperSpinner;
    private Spinner paperStopSpinner;
    private Spinner paperFixSpinner;
    private Spinner paperDeveloperDilutionSpinner;
    private EditText paperVolumeField;
    private EditText paperWidthField;
    private EditText paperHeightField;
    private EditText paperSheetsField;
    private LinearLayout paperResultBox;
    private LinearLayout paperCapacityBox;
    private Product lastPaperDeveloper;
    private Product lastPaperStop;
    private Product lastPaperFix;
    private double lastPaperVolume;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Window w = getWindow();
        w.setStatusBarColor(BG);
        w.setNavigationBarColor(BG);
        prefs = getSharedPreferences("darkroom_assistant", MODE_PRIVATE);
        MdcOfflineStore.init(getApplicationContext());
        repairCuratedAuxInventory();
        String target = getIntent().getStringExtra("darkroom_target");
        if ("products".equals(target)) showProducts();
        else if ("film".equals(target)) showFilm();
        else if ("paper".equals(target)) showPaper();
        else finish();
        ensureOfflineDatabase();
    }

    private void ensureOfflineDatabase() {
        if (MdcOfflineStore.isReady()) return;
        String detail = MdcOfflineStore.initError();
        new AlertDialog.Builder(this)
                .setTitle("Database offline non disponibile")
                .setMessage("L'app si è aperta, ma il database incluso non è leggibile." +
                        (detail == null || detail.isEmpty() ? "" : " - Dettaglio: " + detail))
                .setPositiveButton("CHIUDI", null)
                .show();
    }

    @Override
    public void onBackPressed() {
        saveCurrentUiState();
        finish();
    }

    @Override
    protected void onPause() {
        saveCurrentUiState();
        super.onPause();
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

    // ---------------------------------------------------------------------
    // PRODOTTI CHIMICI
    // ---------------------------------------------------------------------

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

        String[] typeLabels = new String[]{
                "Rivelatore pellicola", "Rivelatore carta", "Arresto", "Fissaggio",
                "Imbibente", "Aiuto lavaggio", "Altra chimica"
        };
        final int[] typeRoles = new int[]{ROLE_FILM_DEV, ROLE_PAPER_DEV, ROLE_STOP, ROLE_FIX,
                ROLE_WETTING, ROLE_WASHING, ROLE_CHEMISTRY};
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

    private void enrichProductThenAdd(Product local,
                                      OnlineCatalogSearch.SearchResult selectedResult) {
        new Thread(() -> {
            Product seed = local;
            OnlineCatalogSearch.SearchResult r = selectedResult;

            if (r == null && seed != null) {
                List<OnlineCatalogSearch.SearchResult> found =
                        OnlineCatalogSearch.searchChemicals(seed.name);
                r = pickBestResult(seed.name, found);
            }

            OnlineCatalogSearch.ChemicalData data = null;
            if (r != null) {
                try {
                    data = OnlineCatalogSearch.enrichChemical(r);
                } catch (Exception ignored) {}
            }

            if (seed == null && data != null) {
                seed = new Product(cleanSearchTitle(data.name), data.roles, data.stockPrep,
                        data.filmDilutions, data.paperDilutions, data.workingDilution,
                        data.stockInstructions, data.expiryDays, data.sourceUrl,
                        ChemistrySpecEngine.REUSE_UNKNOWN, -1, -1);
            }
            if (seed == null) return;

            if (r != null && MdcOfflineStore.isOfflineDeveloperResult(r)) {
                Product direct = seed;
                runOnUiThread(() -> startProductAddFlow(direct));
                return;
            }

            String source = data != null && data.sourceUrl != null && !data.sourceUrl.isEmpty()
                    ? data.sourceUrl : seed.sourceUrl;
            String fallbackInstructions = usefulInstruction(seed.stockInstructions)
                    ? seed.stockInstructions
                    : (data == null ? null : data.stockInstructions);
            ChemistrySpecEngine.Spec spec = ChemistrySpecEngine.enrich(
                    seed.name, source, fallbackInstructions);
            Product merged = mergeProduct(seed, data, spec);

            runOnUiThread(() -> {
                if (merged.roles == 0) chooseProductTypeThenAdd(merged);
                else startProductAddFlow(merged);
            });
        }).start();
    }

    private OnlineCatalogSearch.SearchResult pickBestResult(
            String name, List<OnlineCatalogSearch.SearchResult> results) {
        if (results == null || results.isEmpty()) return null;
        String n = normalize(name);
        for (OnlineCatalogSearch.SearchResult r : results) {
            if (normalize(r.title).contains(n) || n.contains(normalize(r.title))) return r;
        }
        return results.get(0);
    }

    private Product mergeProduct(Product seed,
                                 OnlineCatalogSearch.ChemicalData data,
                                 ChemistrySpecEngine.Spec spec) {
        int roles = data != null && data.roles != 0 ? data.roles : seed.roles;
        boolean stock = seed.stockPrep || (data != null && data.stockPrep);
        String[] film = data != null && data.filmDilutions != null &&
                data.filmDilutions.length > 0 ? data.filmDilutions : seed.filmDilutions;
        String[] paper = data != null && data.paperDilutions != null &&
                data.paperDilutions.length > 0 ? data.paperDilutions : seed.paperDilutions;
        String working = data != null && data.workingDilution != null
                ? data.workingDilution : seed.workingDilution;
        String instructions = spec.stockInstructions != null
                ? spec.stockInstructions
                : (usefulInstruction(seed.stockInstructions) ? seed.stockInstructions :
                (data == null ? null : data.stockInstructions));
        int expiry = data != null && data.expiryDays > 0 ? data.expiryDays : seed.expiryDays;
        String source = spec.sourceUrl != null && !spec.sourceUrl.isEmpty()
                ? spec.sourceUrl
                : (data != null && data.sourceUrl != null ? data.sourceUrl : seed.sourceUrl);
        int reuse = spec.reuseMode != ChemistrySpecEngine.REUSE_UNKNOWN
                ? spec.reuseMode : seed.reuseMode;
        double filmCap = spec.filmCapacityPerLiter > 0
                ? spec.filmCapacityPerLiter : seed.filmCapacityPerLiter;
        double paperCap = spec.paperCapacitySqMPerLiter > 0
                ? spec.paperCapacitySqMPerLiter : seed.paperCapacitySqMPerLiter;
        String productName = data != null && data.name != null && data.name.length() > 2
                ? cleanSearchTitle(data.name) : seed.name;
        return new Product(productName, roles, stock, film, paper, working,
                instructions, expiry, source, reuse, filmCap, paperCap);
    }

    private void chooseProductTypeThenAdd(Product p) {
        String[] types = new String[]{
                "Rivelatore pellicola", "Rivelatore carta",
                "Rivelatore pellicola + carta", "Arresto", "Fissaggio"
        };
        new AlertDialog.Builder(this)
                .setTitle("Tipo non riconosciuto")
                .setMessage("La fonte non consente di classificare il prodotto con sicurezza.")
                .setItems(types, (d, which) ->
                        startProductAddFlow(p.withRole(roleForType(which))))
                .show();
    }

    private void startProductAddFlow(Product p) {
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
            body += "\n\nFonte tecnica registrata disponibile.";
        }

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Preparazione stock")
                .setMessage(body)
                .setNegativeButton("ANNULLA", null)
                .setNeutralButton("APRI FONTE", null)
                .setPositiveButton("STOCK PREPARATO", (d, w) -> askOpeningDate(p))
                .create();
        dialog.setOnShowListener(d -> {
            Button src = dialog.getButton(AlertDialog.BUTTON_NEUTRAL);
            if (p.sourceUrl == null || p.sourceUrl.isEmpty()) src.setVisibility(View.GONE);
            else src.setOnClickListener(v -> openUrl(p.sourceUrl));
        });
        dialog.show();
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
                }, now.get(Calendar.YEAR), now.get(Calendar.MONTH),
                now.get(Calendar.DAY_OF_MONTH));
        OperationalLifeInfo life = operationalLife(p.name);
        picker.setTitle(life != null && life.stock() ? "Data preparazione stock" : "Data apertura concentrato");
        picker.show();
    }

    private void showProductDetails(String name) {
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
                    .append(safeItalianTechnical(life.text));
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
        String[] types = new String[]{"Rivelatore pellicola", "Rivelatore carta",
                "Rivelatore pellicola + carta", "Arresto", "Fissaggio",
                "Imbibente", "Aiuto lavaggio", "Altra chimica"};
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

        String[] reuseLabels = new String[]{"Non determinato", "Monouso", "Riutilizzabile", "Soluzione fresca consigliata"};
        Spinner reuse = spinner(reuseLabels);
        reuse.setSelection(p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT ? 1 :
                p.reuseMode == ChemistrySpecEngine.REUSE_REUSABLE ? 2 :
                p.reuseMode == REUSE_FRESH_RECOMMENDED ? 3 : 0);
        box.addView(fieldBlock("RIUTILIZZO", reuse));

        EditText filmCap = edit(p.filmCapacityPerLiter > 0 ? fmt(p.filmCapacityPerLiter) : "",
                InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        box.addView(fieldBlock("CAPACITÀ PELLICOLA (rulli per litro)", filmCap));
        EditText paperCap = edit(p.paperCapacitySqMPerLiter > 0 ? fmt(p.paperCapacitySqMPerLiter) : "",
                InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        box.addView(fieldBlock("CAPACITÀ CARTA (m² per litro)", paperCap));

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
        box.addView(fieldBlock("PREPARAZIONE / SOLUZIONE STOCK", instructions));

        OperationalLifeInfo lifeInfo = operationalLife(p.name);
        EditText date = edit(opened > 0 ? df.format(new Date(opened)) : "",
                InputType.TYPE_CLASS_DATETIME);
        box.addView(fieldBlock(operationalDateTitle(lifeInfo), date));

        if (lifeInfo != null) {
            TextView durationView = label(safeItalianTechnical(lifeInfo.text), 14, WHITE, false);
            durationView.setPadding(dp(10), dp(10), dp(10), dp(10));
            durationView.setBackground(bg(CARD, 10, BORDER, 1));
            box.addView(fieldBlock(operationalDurationTitle(lifeInfo), durationView));

            TextView expiryView = label(operationalExpiryValue(lifeInfo, opened), 15, WHITE, true);
            expiryView.setPadding(dp(10), dp(10), dp(10), dp(10));
            expiryView.setBackground(bg(CARD, 10, BORDER, 1));
            box.addView(fieldBlock(operationalExpiryTitle(lifeInfo), expiryView));
        }
        String technical = chemicalTechnicalSummaryIt(p.name);
        if (!technical.isEmpty()) {
            TextView technicalView = label(technical, 13, WHITE, false);
            technicalView.setPadding(dp(10), dp(10), dp(10), dp(10));
            technicalView.setBackground(bg(CARD, 10, BORDER, 1));
            box.addView(fieldBlock("SCHEDA TECNICA · PRODUTTORE", technicalView));
        }


        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("Modifica prodotto")
                .setView(scroll(box))
                .setNegativeButton("ANNULLA", null)
                .setPositiveButton("SALVA", null)
                .create();
        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String newName = name.getText().toString().trim();
                    if (newName.isEmpty()) { toast("Inserisci il nome."); return; }
                    long newOpened = opened;
                    try {
                        if (!date.getText().toString().trim().isEmpty())
                            newOpened = df.parse(date.getText().toString().trim()).getTime();
                    } catch (Exception e) { toast("Data non valida."); return; }
                    int exp = p.expiryDays; // legacy value preserved but no longer used for operational expiry
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
                }));
        dialog.show();
    }

    // ---------------------------------------------------------------------
    // SVILUPPO PELLICOLA
    // ---------------------------------------------------------------------

    private void showFilm() {
        currentScreen = FILM;
        selectedFilm = null;
        selectedFilmDeveloper = null;
        selectedStop = null;
        selectedFix = null;
        lastFilmTank = null;

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
        filmSearchStatus = label("Cerca nel database offline dopo 3 lettere.", 12, MUTED, false);
        filmSearchStatus.setPadding(dp(4), 0, dp(4), dp(10));
        page.addView(filmSearchStatus);
        filmSuggestionsBox = new LinearLayout(this);
        filmSuggestionsBox.setOrientation(LinearLayout.VERTICAL);
        page.addView(filmSuggestionsBox);

        formatSpinner = spinner(new String[]{"Seleziona prima la pellicola"});
page.addView(fieldBlock("FORMATO", formatSpinner));

isoField = edit("", InputType.TYPE_CLASS_NUMBER);
        isoField.setHint("ISO nominale");
        page.addView(fieldBlock("ISO ESPOSTO", isoField));
        rollsSpinner = spinner(new String[]{"1", "2", "3", "4", "5"});
        LinearLayout filmCountBlock = fieldBlock("NUMERO RULLI", rollsSpinner);
        filmCountLabel = (TextView) filmCountBlock.getChildAt(0);
        page.addView(filmCountBlock);
        tankSpinner = spinner(new String[]{"Seleziona prima la pellicola"});
        page.addView(fieldBlock("TANK JOBO", tankSpinner));

        List<Product> developers = inventoryProductsByRole(ROLE_FILM_DEV);
        developerSpinner = productSpinner(developers, "Nessun rivelatore in magazzino");
        page.addView(fieldBlock("RIVELATORE", developerSpinner));
        dilutionSpinner = spinner(new String[]{"—"});
        page.addView(fieldBlock("DILUIZIONE", dilutionSpinner));

        temperatureField = edit("20", InputType.TYPE_CLASS_NUMBER |
                InputType.TYPE_NUMBER_FLAG_DECIMAL);
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
                refreshFilmDilutions();
            }
        });
        stopSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) { selectedStop = productAt(stops, position); }
        });
        fixSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) { selectedFix = productAt(fixes, position); }
        });
        formatSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                if (selectedFilm == null || formatSpinner.getSelectedItem() == null) return;
                String label = String.valueOf(formatSpinner.getSelectedItem());
                String f = label.startsWith("4") ? "4x5" : label.startsWith("120") ? "120" : label.startsWith("35") ? "35" : "";
                if (f.isEmpty()) return;
                selectedFilm = new FilmStock(selectedFilm.name, selectedFilm.nominalIso, f, selectedFilm.sourceUrl);
                updateFilmCountControls(f);
                updateCompatibleTanks();
            }
        });
        rollsSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) { updateCompatibleTanks(); }
        });

        wireFilmSearch(filmField, filmAdapter, onlineFilms);
        filmField.setOnItemClickListener((parent, view, position, id) -> {
            if (filmSuggestionsBox != null) filmSuggestionsBox.removeAllViews();
            String display = String.valueOf(parent.getItemAtPosition(position));
            FilmStock local = findFilm(display);
            if (local != null) { selectFilm(local); return; }
            OnlineCatalogSearch.SearchResult r =
                    onlineFilms.get(display.toLowerCase(Locale.ROOT));
            if (r == null) return;
            filmSearchStatus.setText("Recupero dati pellicola…");
            new Thread(() -> {
                OnlineCatalogSearch.FilmData fd = OnlineCatalogSearch.enrichFilm(r);
                runOnUiThread(() -> finishOnlineFilmSelection(fd));
            }).start();
        });

        Button calc = actionButton("CALCOLA", BURGUNDY);
        calc.setOnClickListener(v -> {
            try {
                calculateFilmOnline();
            } catch (Throwable error) {
                showFilmCalculationFailure(error);
            }
        });
        page.addView(calc);
        page.addView(space(16));
        filmResultBox = new LinearLayout(this);
        filmResultBox.setOrientation(LinearLayout.VERTICAL);
        page.addView(filmResultBox);
        page.addView(space(80));
        setContentView(scroll(page));
        restoreFilmUiState();
    }

    private void refreshFilmDilutions() {
        if (dilutionSpinner == null) return;
        String previous = spinnerText(dilutionSpinner);
        String[] values = new String[0];
        if (selectedFilm != null && selectedFilmDeveloper != null) {
            values = MdcOfflineStore.dilutionsForCombination(
                    selectedFilm.name, selectedFilmDeveloper.name);
        }
        if (values.length == 0 && selectedFilmDeveloper != null &&
                selectedFilmDeveloper.filmDilutions.length > 0) {
            values = selectedFilmDeveloper.filmDilutions;
        }
        if (values.length == 0) values = new String[]{"—"};
        setSpinnerItems(dilutionSpinner, values);
        if (previous != null && !previous.isEmpty()) selectSpinnerText(dilutionSpinner, previous);
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
                int g = generation[0];
                if (pending[0] != null) handler.removeCallbacks(pending[0]);
                if (q.length() < 3) {
                    adapter.clear(); online.clear();
                    if (filmSuggestionsBox != null) filmSuggestionsBox.removeAllViews();
                    filmSearchStatus.setText("Cerca nel database offline dopo 3 lettere.");
                    return;
                }
                replaceSuggestions(adapter, localFilmMatches(q));
                filmSearchStatus.setText("Cerco nel database offline…");
                pending[0] = () -> new Thread(() -> {
                    List<OnlineCatalogSearch.SearchResult> results =
                            OnlineCatalogSearch.searchFilms(q);
                    runOnUiThread(() -> {
                        if (g != generation[0] ||
                                !q.equalsIgnoreCase(field.getText().toString().trim())) return;
                        LinkedHashSet<String> merged =
                                new LinkedHashSet<>(localFilmMatches(q));
                        online.clear();
                        for (OnlineCatalogSearch.SearchResult r : results) {
                            merged.add(r.title);
                            online.put(r.title.toLowerCase(Locale.ROOT), r);
                        }
                        List<String> visible = new ArrayList<>(merged);
                        replaceSuggestions(adapter, visible);
                        if (filmSuggestionsBox != null) {
                            filmSuggestionsBox.removeAllViews();
                            for (String item : visible) {
                                TextView option = row(item + "    ›");
                                option.setTextSize(15);
                                option.setOnClickListener(v -> {
                                    filmSuggestionsBox.removeAllViews();
                                    FilmStock local = findFilm(item);
                                    if (local != null) { selectFilm(local); return; }
                                    OnlineCatalogSearch.SearchResult rr = online.get(item.toLowerCase(Locale.ROOT));
                                    if (rr == null) return;
                                    filmSearchStatus.setText("Recupero dati pellicola…");
                                    field.setText(item, false);
                                    new Thread(() -> {
                                        OnlineCatalogSearch.FilmData fd = OnlineCatalogSearch.enrichFilm(rr);
                                        runOnUiThread(() -> finishOnlineFilmSelection(fd));
                                    }).start();
                                });
                                filmSuggestionsBox.addView(option);
                                filmSuggestionsBox.addView(space(5));
                            }
                        }
                        filmSearchStatus.setText(visible.isEmpty()
                                ? "Nessuna pellicola trovata."
                                : visible.size() + " pellicole trovate. Tocca una pellicola.");
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
            refreshFilmDilutions();
            refreshFilmDilutions();
        updateCompatibleTanks();
            return;
        }
        List<String> labels = new ArrayList<>();
        int selected = 0;
        for (int i = 0; i < formats.length; i++) {
            String x = formats[i];
            labels.add(formatDisplay(x));
            if (x.equals(f.format)) selected = i;
        }
        setSpinnerItems(formatSpinner, labels.toArray(new String[0]));
        formatSpinner.setSelection(selected);
        String chosenFormat = formats[selected];
        selectedFilm = new FilmStock(f.name, f.nominalIso, chosenFormat, f.sourceUrl);
        updateFilmCountControls(chosenFormat);
        refreshFilmDilutions();
        updateCompatibleTanks();
    }

    private void updateCompatibleTanks() {
        if (tankSpinner == null) return;
        compatibleTanks.clear();
        if (selectedFilm == null) {
            setSpinnerItems(tankSpinner, new String[]{"Seleziona prima la pellicola"});
            return;
        }
        if (selectedFilm.format == null || selectedFilm.format.isEmpty()) {
            setSpinnerItems(tankSpinner, new String[]{"Seleziona il formato"});
            return;
        }
        int rolls = 1;
        try { rolls = Integer.parseInt(String.valueOf(rollsSpinner.getSelectedItem())); }
        catch (Exception ignored) {}
        for (Tank t : tanks) {
            int cap = isSheetFormat(selectedFilm.format) ? t.maxSheet : ("120".equals(selectedFilm.format) ? t.max120 : t.max35);
            if (cap >= rolls) compatibleTanks.add(t);
        }
        if (compatibleTanks.isEmpty()) {
            setSpinnerItems(tankSpinner, new String[]{"Nessuna tank CPE2 compatibile"});
            return;
        }
        List<String> labels = new ArrayList<>();
        int defaultIndex = 0;
        for (int i = 0; i < compatibleTanks.size(); i++) {
            Tank t = compatibleTanks.get(i);
            labels.add(tankDisplayName(t, selectedFilm.format) + " — " + t.rotaryMl + " ml");
            if ("JOBO 2520".equals(t.name)) defaultIndex = i;
        }
        setSpinnerItems(tankSpinner, labels.toArray(new String[0]));
        tankSpinner.setSelection(defaultIndex);
    }

    private boolean isSheetFormat(String format) {
        return format != null && ("4x5".equalsIgnoreCase(format) || "sheet".equalsIgnoreCase(format));
    }

    private String formatDisplay(String format) {
        if (isSheetFormat(format)) return "4×5 / lastre";
        if ("120".equals(format)) return "120";
        return "35 mm";
    }

    private void updateFilmCountControls(String format) {
        if (rollsSpinner == null) return;
        if (isSheetFormat(format)) {
            if (filmCountLabel != null) filmCountLabel.setText("NUMERO LASTRE 4×5");
            setSpinnerItems(rollsSpinner, new String[]{"1", "2", "4"});
        } else {
            if (filmCountLabel != null) filmCountLabel.setText("NUMERO RULLI");
            setSpinnerItems(rollsSpinner, new String[]{"1", "2", "3", "4", "5"});
        }
        rollsSpinner.setSelection(0);
    }

    private String tankDisplayName(Tank tank, String format) {
        if (tank == null) return "—";
        if (isSheetFormat(format) && "JOBO 2520".equals(tank.name)) return "JOBO 2520 + 2509N";
        return tank.name;
    }

    private double filmCapacityUnits(int count, String format) {
        // Capacity sheets are converted only for chemistry-capacity bookkeeping:
        // four 4x5 sheets are about one 135-36/120 roll by emulsion area.
        return isSheetFormat(format) ? count / 4.0 : count;
    }

    private String developedUnitLabel(int count, String format) {
        if (isSheetFormat(format)) return count + (count == 1 ? " lastra 4×5" : " lastre 4×5");
        return count + (count == 1 ? " rullo" : " rulli");
    }

    private double chemicalMinimumForLoad(
            MdcOfflineStore.DeveloperMinimumVolume minimum, String format, int count) {
        if (minimum == null || count <= 0) return -1;
        if (!isSheetFormat(format)) return minimum.for500Cm2 * count;
        if (count == 1) return minimum.forOne4x5;
        if (count == 2) return minimum.forTwo4x5;
        if (count == 4) return minimum.for500Cm2;
        return -1;
    }

    private Tank selectedTank() {
        int i = tankSpinner == null ? -1 : tankSpinner.getSelectedItemPosition();
        if (i < 0 || i >= compatibleTanks.size()) return null;
        return compatibleTanks.get(i);
    }

    private void calculateFilmOnline() {
        if (selectedFilm == null) selectedFilm = findFilm(filmField.getText().toString().trim());
        if (selectedFilm == null) { toast("Seleziona una pellicola."); return; }
        if (selectedFilmDeveloper == null) { toast("Seleziona un rivelatore dal magazzino."); return; }
        if (selectedStop == null || selectedFix == null) {
            toast("Aggiungi arresto e fissaggio al magazzino."); return;
        }
        Tank tank = selectedTank();
        if (tank == null) { resultFilmError("Nessuna tank compatibile."); return; }

        int iso;
        double temp;
        int rolls;
        try {
            iso = Integer.parseInt(isoField.getText().toString().trim());
            temp = Double.parseDouble(temperatureField.getText().toString().trim().replace(',', '.'));
            rolls = Integer.parseInt(String.valueOf(rollsSpinner.getSelectedItem()));
        } catch (Exception e) {
            toast(isSheetFormat(selectedFilm.format)
                    ? "Controlla ISO, temperatura e numero lastre."
                    : "Controlla ISO, temperatura e rulli.");
            return;
        }

        String dilution = String.valueOf(dilutionSpinner.getSelectedItem());
        if ("—".equals(dilution)) { toast("Diluizione rivelatore non disponibile."); return; }
        MdcOfflineStore.DeveloperMinimumVolume minimum =
                MdcOfflineStore.minimumWorkingVolume(selectedFilmDeveloper.name, dilution);
        if (minimum == null) {
            resultFilmError("Rivelatore non incluso nel catalogo Maco Direct censito, " +
                    "oppure volume minimo non disponibile per " +
                    selectedFilmDeveloper.name + " " + dilution + ". Calcolo bloccato.");
            return;
        }
        double chemicalMinimumMl = chemicalMinimumForLoad(minimum, selectedFilm.format, rolls);
        if (chemicalMinimumMl <= 0) {
            resultFilmError("Numero di lastre non supportato. Seleziona 1, 2 oppure 4 lastre 4×5.");
            return;
        }
        double workingVolumeMl = Math.max(tank.rotaryMl, Math.ceil(chemicalMinimumMl));
        if (workingVolumeMl > 600) {
            resultFilmError("Servono " + fmt(workingVolumeMl) +
                    " ml: supera il limite 600 ml della JOBO CPE2 (minimo tank " +
                    tank.rotaryMl + " ml, minimo chimico " + fmt(chemicalMinimumMl) + " ml).");
            return;
        }

        double[] devMix = mix(workingVolumeMl, dilution);
        String stopDilution = filmAuxDilution(selectedStop);
        String fixDilution = filmAuxDilution(selectedFix);
        double[] stopMix = mix(workingVolumeMl, stopDilution);
        double[] fixMix = mix(workingVolumeMl, fixDilution);
        if (devMix == null || stopMix == null || fixMix == null) {
            resultFilmError("Una diluizione non è calcolabile: modifica la scheda prodotto.");
            return;
        }

        lastFilmTank = tank;
        lastFilmRolls = rolls;
        filmResultBox.removeAllViews();
        resultLine(filmResultBox, "RICERCA TEMPO", "Cerco la combinazione nel database offline…");
        final Product dev = selectedFilmDeveloper;
        final Product stop = selectedStop;
        final Product fix = selectedFix;
        new Thread(() -> {
            DevTimeEngine.Result exactResult = MdcOfflineStore.lookup(
                    selectedFilm.name, selectedFilm.format, dev.name, dilution, iso, temp);
            DevTimeEngine.Result result = exactResult != null
                    ? exactResult
                    : DevTimeEngine.Result.notFound(MdcOfflineStore.combinationDiagnostic(
                            selectedFilm.name, dev.name, dilution, iso));
            runOnUiThread(() -> showDevelopmentResultSafely(result, tank, rolls,
                    dev, stop, fix, devMix, stopMix, fixMix,
                    workingVolumeMl, chemicalMinimumMl, minimum, dilution));
        }).start();
    }

    private void showFilmCalculationFailure(Throwable error) {
        String type = error == null ? "Errore sconosciuto" : error.getClass().getSimpleName();
        String message = error == null || error.getMessage() == null
                ? "" : error.getMessage().trim();
        android.util.Log.e("DarkroomFilm", "Errore calcolo sviluppo", error);
        resultFilmError("Errore interno nel calcolo sviluppo: " + type +
                (message.isEmpty() ? "" : " · " + message) +
                ". L'app è rimasta aperta.");
    }

    private void showDevelopmentResultSafely(DevTimeEngine.Result result,
                                       Tank tank, int rolls,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix,
                                       double workingVolumeMl, double chemicalMinimumMl,
                                       MdcOfflineStore.DeveloperMinimumVolume minimum,
                                       String dilution) {
        try {
            showDevelopmentResult(result, tank, rolls, dev, stop, fix,
                    devMix, stopMix, fixMix, workingVolumeMl, chemicalMinimumMl,
                    minimum, dilution);
        } catch (Throwable primary) {
            android.util.Log.e("DarkroomFilm", "Errore scheda completa; uso risultato essenziale", primary);
            try {
                showDevelopmentResultEssential(result, tank, dev, stop, fix,
                        devMix, stopMix, fixMix, workingVolumeMl, chemicalMinimumMl,
                        minimum, dilution);
            } catch (Throwable fallback) {
                showFilmCalculationFailure(fallback);
            }
        }
    }

    private void showDevelopmentResultEssential(DevTimeEngine.Result result,
                                       Tank tank,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix,
                                       double workingVolumeMl, double chemicalMinimumMl,
                                       MdcOfflineStore.DeveloperMinimumVolume minimum,
                                       String dilution) {
        filmResultBox.removeAllViews();
        if (result == null || !result.found) {
            resultLine(filmResultBox, "TEMPO JOBO CPE2", "Tempo non disponibile");
            if (result != null && result.diagnostic != null && !result.diagnostic.isEmpty())
                resultLine(filmResultBox, "DIAGNOSTICA", result.diagnostic);
        } else {
            resultLine(filmResultBox, "TEMPO JOBO CPE2", result.finalDisplay());
            resultLine(filmResultBox, "DATO ORIGINALE",
                    result.baseDisplay() + " @ " + fmtTemp(result.baseTemperature));
        }
        resultLine(filmResultBox, "TANK",
                tank.name + " · minimo rotazione " + fmt(tank.rotaryMl) + " ml");
        resultLine(filmResultBox, "VOLUME DI LAVORO",
                fmt(workingVolumeMl) + " ml · minimo chimico " +
                        fmt(chemicalMinimumMl) + " ml");
        resultLine(filmResultBox, "RIVELATORE",
                dev.name + "\n" +
                        formatDeveloperMix(dev.name, dilution, devMix, workingVolumeMl));
        resultLine(filmResultBox, "ARRESTO", formatMix(stopMix, workingVolumeMl));
        resultLine(filmResultBox, "FISSAGGIO", formatMix(fixMix, workingVolumeMl));
        if (minimum != null && !minimum.sourceTitle.isEmpty())
            resultLine(filmResultBox, "FONTE / CRITERIO VOLUME", minimum.sourceTitle);
    }

    private void showDevelopmentResult(DevTimeEngine.Result result,
                                       Tank tank, int rolls,
                                       Product dev, Product stop, Product fix,
                                       double[] devMix, double[] stopMix, double[] fixMix,
                                       double workingVolumeMl, double chemicalMinimumMl,
                                       MdcOfflineStore.DeveloperMinimumVolume minimum,
                                       String dilution) {
        filmResultBox.removeAllViews();
        String loadFormat = selectedFilm != null ? selectedFilm.format
                : (result == null ? "35" : result.format);
        String filmName = selectedFilm == null ? "Pellicola" : selectedFilm.name;

        LinearLayout summary = new LinearLayout(this);
        summary.setOrientation(LinearLayout.VERTICAL);
        summary.setPadding(dp(18), dp(16), dp(18), dp(16));
        summary.setBackground(bg(CARD, 13, BORDER, 1));
        summary.addView(label("RISULTATO SVILUPPO", 15, WHITE, true));
        addUnifiedChemicalField(summary, "TEMPO JOBO CPE2",
                result != null && result.found ? result.finalDisplay() : "Tempo non disponibile");
        if (result != null && result.found && result.diagnostic != null &&
                result.diagnostic.startsWith("EQUIVALENTE_APPROVATO|")) {
            addUnifiedChemicalField(summary, "EQUIVALENZA CONTROLLATA",
                    dev.name + " " + dilution + " → " + result.sourceDeveloper + " " +
                            result.sourceDilution +
                            "\nUsata solo perché la corrispondenza esatta non è presente nel database offline.");
        }
        filmResultBox.addView(summary);
        filmResultBox.addView(space(10));

        LinearLayout preparation = new LinearLayout(this);
        preparation.setOrientation(LinearLayout.VERTICAL);
        preparation.setPadding(dp(18), dp(14), dp(18), dp(14));
        preparation.setBackground(bg(CARD, 13, BORDER, 1));
        preparation.addView(label("PREPARAZIONE BAGNI", 15, WHITE, true));
        addUnifiedChemicalField(preparation, "RIVELATORE · " + dev.name,
                formatDeveloperMix(dev.name, dilution, devMix, workingVolumeMl));
        addUnifiedChemicalField(preparation, "ARRESTO · " + stop.name,
                formatMix(stopMix, workingVolumeMl));
        addUnifiedChemicalField(preparation, "FISSAGGIO · " + fix.name,
                formatMix(fixMix, workingVolumeMl));
        filmResultBox.addView(preparation);
        filmResultBox.addView(space(10));

        LinearLayout calculation = accordionBody();
        addUnifiedChemicalField(calculation, "COMBINAZIONE",
                filmName + " · " + dev.name + " " + dilution);
        addUnifiedChemicalField(calculation, "TANK / VOLUME",
                tankDisplayName(tank, loadFormat) + " · " + fmt(workingVolumeMl) +
                        " ml (minimo tank " + fmt(tank.rotaryMl) + " ml)");
        if (result == null || !result.found) {
            addUnifiedChemicalField(calculation, "TEMPO NON DISPONIBILE",
                    result == null || result.diagnostic == null || result.diagnostic.isEmpty()
                            ? "Nessuna combinazione esatta trovata nel database."
                            : result.diagnostic);
        } else {
            addUnifiedChemicalField(calculation, "DATO MDC ORIGINALE",
                    result.baseDisplay() + " @ " + fmtTemp(result.baseTemperature) +
                            " · ISO " + result.sourceIso + " · " + formatDisplay(loadFormat));
            String conversion = result.temperatureConverted
                    ? "Temperatura compensata a " + fmtTemp(result.targetTemperature)
                    : "Temperatura: dato originale";
            conversion += "\nJOBO CPE2: rotazione continua, adattamento −15%";
            addUnifiedChemicalField(calculation, "ADATTAMENTI", conversion);
            addUnifiedChemicalField(calculation, "FONTE COMBINAZIONE",
                    result.sourceName + "\n" + result.sourceFilm + " · " +
                            result.sourceDeveloper + " · " + result.sourceDilution);
            if (result.warning != null && !result.warning.isEmpty())
                addUnifiedChemicalField(calculation, "ATTENZIONE", result.warning);
        }
        addUnifiedChemicalField(calculation, "MINIMO CHIMICO",
                fmt(chemicalMinimumMl) + " ml · volume utilizzato " +
                        fmt(workingVolumeMl) + " ml");
        if (minimum != null && !minimum.sourceTitle.isEmpty()) {
            String evidenceLabel = "CONSERVATIVE_OPERATIONAL".equals(minimum.evidenceKind)
                    ? "criterio operativo conservativo"
                    : "dato o ricetta del produttore";
            addUnifiedChemicalField(calculation, "FONTE / CRITERIO VOLUME",
                    minimum.sourceTitle + " · " + evidenceLabel);
            if (!minimum.sourceUrl.isEmpty()) {
                Button openMinimumSource = smallButton("APRI FONTE VOLUME");
                openMinimumSource.setOnClickListener(v -> openUrl(minimum.sourceUrl));
                calculation.addView(openMinimumSource);
            }
        }
        addFilmAccordion(filmResultBox, "DETTAGLI DEL CALCOLO",
                result != null && result.found ? "MDC · JOBO · minimo chimico" : "Tempo non disponibile",
                calculation);

        LinearLayout technicalBody = accordionBody();
        String technical = chemicalTechnicalSummaryIt(dev.name);
        addUnifiedChemicalField(technicalBody, dev.name,
                technical.isEmpty()
                        ? "Scheda tecnica non ancora verificata per questo prodotto."
                        : technical);
        addFilmAccordion(filmResultBox, "SCHEDA TECNICA RIVELATORE",
                "Preparazione · conservazione · capacità", technicalBody);

        LinearLayout reuseBody = accordionBody();
        filmCapacityBox = new LinearLayout(this);
        filmCapacityBox.setOrientation(LinearLayout.VERTICAL);
        reuseBody.addView(filmCapacityBox);
        renderFilmCapacityForFormat(dev, stop, fix, workingVolumeMl, loadFormat);
        addFilmAccordion(filmResultBox, "RIUTILIZZO BAGNI",
                filmReuseCompactSummary(dev, stop, fix, workingVolumeMl), reuseBody);

        Button register = actionButton("REGISTRA QUESTO SVILUPPO", BURGUNDY);
        register.setOnClickListener(v -> {
            double units = filmCapacityUnits(rolls, loadFormat);
            registerFilmUse(dev, workingVolumeMl, units);
            registerFilmUse(stop, workingVolumeMl, units);
            registerFilmUse(fix, workingVolumeMl, units);
            renderFilmCapacityForFormat(dev, stop, fix, workingVolumeMl, loadFormat);
            toast(developedUnitLabel(rolls, loadFormat) + " registrat" +
                    (rolls == 1 ? "a." : "e."));
        });
        filmResultBox.addView(register);
        filmResultBox.addView(space(9));

        Button fresh = smallButton("NUOVO BAGNO / AZZERA CONTATORE");
        fresh.setOnClickListener(v -> {
            resetFilmBath(dev, workingVolumeMl);
            resetFilmBath(stop, workingVolumeMl);
            resetFilmBath(fix, workingVolumeMl);
            renderFilmCapacityForFormat(dev, stop, fix, workingVolumeMl, loadFormat);
            toast("Contatori del bagno azzerati.");
        });
        filmResultBox.addView(fresh);
        filmResultBox.addView(space(20));
    }

    private void addUnifiedChemicalField(LinearLayout parent, String title, String value) {
        if (value == null || value.trim().isEmpty()) return;
        TextView heading = label(title, 11, MUTED, true);
        heading.setPadding(0, dp(8), 0, dp(3));
        parent.addView(heading);
        parent.addView(label(value.trim(), 15, WHITE, false));
    }

    private LinearLayout accordionBody() {
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(16), 0, dp(16), dp(14));
        return body;
    }

    private void addFilmAccordion(LinearLayout parent, String title,
                                  String compactSummary, LinearLayout body) {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setBackground(bg(CARD, 13, BORDER, 1));
        TextView header = label("▸ " + title + "\n" + compactSummary, 14, WHITE, true);
        header.setPadding(dp(16), dp(13), dp(16), dp(13));
        body.setVisibility(View.GONE);
        final boolean[] open = new boolean[]{false};
        header.setOnClickListener(v -> {
            open[0] = !open[0];
            body.setVisibility(open[0] ? View.VISIBLE : View.GONE);
            header.setText((open[0] ? "▾ " : "▸ ") + title + "\n" + compactSummary);
        });
        section.addView(header);
        section.addView(body);
        parent.addView(section);
        parent.addView(space(10));
    }

    private String filmReuseCompactSummary(Product dev, Product stop, Product fix,
                                           double volumeMl) {
        String developerState = dev != null &&
                dev.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT
                ? "rivelatore monouso" : "stato bagni disponibile";
        return developerState + " · apri per capacità e contatori";
    }

    private void renderFilmCapacityForFormat(Product dev, Product stop, Product fix,
                                             double volumeMl, String format) {
        renderFilmCapacity(dev, stop, fix, volumeMl);
        if (filmCapacityBox != null && isSheetFormat(format)) {
            resultLine(filmCapacityBox, "EQUIVALENZA CAPACITÀ",
                    "Per il solo contatore chimico: 4 lastre 4×5 ≈ 1 rullo 135-36 / 120 per superficie di emulsione.");
        }
    }

    private void renderFilmCapacity(Product dev, Product stop, Product fix, double volumeMl) {
        if (filmCapacityBox == null) return;
        filmCapacityBox.removeAllViews();
        resultLine(filmCapacityBox, "RIVELATORE", filmCapacityStatus(dev, volumeMl));
        resultLine(filmCapacityBox, "ARRESTO", filmCapacityStatus(stop, volumeMl));
        resultLine(filmCapacityBox, "FISSAGGIO", filmCapacityStatus(fix, volumeMl));
    }

    // ---------------------------------------------------------------------
    // STAMPA CARTA
    // ---------------------------------------------------------------------

    private void showPaper() {
        currentScreen = PAPER;
        LinearLayout page = page("Stampa carta", "Prepara i bagni per la stampa.");
        List<Product> developers = inventoryProductsByRole(ROLE_PAPER_DEV);
        List<Product> stops = inventoryProductsByRole(ROLE_STOP);
        List<Product> fixes = inventoryProductsByRole(ROLE_FIX);

        paperDeveloperSpinner = productSpinner(developers, "Nessun rivelatore carta in magazzino");
        paperDeveloperDilutionSpinner = spinner(new String[]{"—"});
        paperStopSpinner = productSpinner(stops, "Nessun arresto in magazzino");
        paperFixSpinner = productSpinner(fixes, "Nessun fissaggio in magazzino");
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

        paperVolumeField = edit("1000", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        page.addView(fieldBlock("VOLUME DA PREPARARE (ml)", paperVolumeField));
        page.addView(label("Per il contatore di riutilizzo", 14, WHITE, true));
        page.addView(space(8));
        paperWidthField = edit("24", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        page.addView(fieldBlock("LARGHEZZA CARTA (cm)", paperWidthField));
        paperHeightField = edit("30", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        page.addView(fieldBlock("ALTEZZA CARTA (cm)", paperHeightField));
        paperSheetsField = edit("1", InputType.TYPE_CLASS_NUMBER);
        page.addView(fieldBlock("NUMERO FOGLI", paperSheetsField));

        Button calc = actionButton("CALCOLA", BURGUNDY);
        calc.setOnClickListener(v -> calculatePaper(developers, stops, fixes));
        page.addView(calc);
        page.addView(space(16));
        paperResultBox = new LinearLayout(this);
        paperResultBox.setOrientation(LinearLayout.VERTICAL);
        page.addView(paperResultBox);
        page.addView(space(80));
        setContentView(scroll(page));
        restorePaperUiState();
    }

    private void calculatePaper(List<Product> developers, List<Product> stops, List<Product> fixes) {
        Product dev = productAt(developers, paperDeveloperSpinner.getSelectedItemPosition());
        Product stop = productAt(stops, paperStopSpinner.getSelectedItemPosition());
        Product fix = productAt(fixes, paperFixSpinner.getSelectedItemPosition());
        if (dev == null || stop == null || fix == null) {
            toast("Aggiungi rivelatore carta, arresto e fissaggio al magazzino."); return;
        }
        double volume = parseDoubleOrMinus(paperVolumeField.getText().toString());
        if (volume <= 0) { toast("Inserisci un volume valido."); return; }
        String devDilution = String.valueOf(paperDeveloperDilutionSpinner.getSelectedItem());
        if ("—".equals(devDilution)) { toast("Diluizione rivelatore non disponibile."); return; }
        double[] devMix = mix(volume, devDilution);
        String stopDilution = paperAuxDilution(stop);
        String fixDilution = paperAuxDilution(fix);
        double[] stopMix = mix(volume, stopDilution);
        double[] fixMix = mix(volume, fixDilution);
        if (devMix == null || stopMix == null || fixMix == null) {
            toast("Una diluizione non è calcolabile: modifica la scheda."); return;
        }

        lastPaperDeveloper = dev;
        lastPaperStop = stop;
        lastPaperFix = fix;
        lastPaperVolume = volume;
        paperResultBox.removeAllViews();
        String paperTech = chemicalTechnicalSummaryIt(dev.name);
        String paperDevText = devDilution + " · " + formatMix(devMix, volume);
        if (!paperTech.isEmpty()) paperDevText += "\n\nSCHEDA TECNICA\n" + paperTech;
        resultLine(paperResultBox, "RIVELATORE", paperDevText);
        resultLine(paperResultBox, "ARRESTO", stopDilution + " · " + formatMix(stopMix, volume));
        resultLine(paperResultBox, "FISSAGGIO", fixDilution + " · " + formatMix(fixMix, volume));

        paperCapacityBox = new LinearLayout(this);
        paperCapacityBox.setOrientation(LinearLayout.VERTICAL);
        paperResultBox.addView(label("RIUTILIZZO BAGNI", 15, WHITE, true));
        paperResultBox.addView(space(8));
        paperResultBox.addView(paperCapacityBox);
        renderPaperCapacity(dev, stop, fix, volume);

        Button register = actionButton("REGISTRA STAMPA", BURGUNDY);
        register.setOnClickListener(v -> registerPaperSession());
        paperResultBox.addView(register);
        paperResultBox.addView(space(9));
        Button fresh = smallButton("NUOVO BAGNO / AZZERA CONTATORE");
        fresh.setOnClickListener(v -> {
            resetPaperBath(dev, volume);
            resetPaperBath(stop, volume);
            resetPaperBath(fix, volume);
            renderPaperCapacity(dev, stop, fix, volume);
            toast("Contatori del bagno azzerati.");
        });
        paperResultBox.addView(fresh);
        paperResultBox.addView(space(20));
    }

    private void registerPaperSession() {
        if (lastPaperDeveloper == null) return;
        double w = parseDoubleOrMinus(paperWidthField.getText().toString());
        double h = parseDoubleOrMinus(paperHeightField.getText().toString());
        int sheets = parseIntOrMinus(paperSheetsField.getText().toString());
        if (w <= 0 || h <= 0 || sheets <= 0) {
            toast("Controlla formato carta e numero fogli."); return;
        }
        double area = (w / 100.0) * (h / 100.0) * sheets;
        registerPaperUse(lastPaperDeveloper, lastPaperVolume, area);
        registerPaperUse(lastPaperStop, lastPaperVolume, area);
        registerPaperUse(lastPaperFix, lastPaperVolume, area);
        renderPaperCapacity(lastPaperDeveloper, lastPaperStop, lastPaperFix, lastPaperVolume);
        toast(sheets + (sheets == 1 ? " foglio registrato." : " fogli registrati."));
    }

    private void renderPaperCapacity(Product dev, Product stop, Product fix, double volumeMl) {
        if (paperCapacityBox == null) return;
        paperCapacityBox.removeAllViews();
        resultLine(paperCapacityBox, "RIVELATORE", paperCapacityStatus(dev, volumeMl));
        resultLine(paperCapacityBox, "ARRESTO", paperCapacityStatus(stop, volumeMl));
        resultLine(paperCapacityBox, "FISSAGGIO", paperCapacityStatus(fix, volumeMl));
    }

    // ---------------------------------------------------------------------
    // CAPACITÀ / RIUTILIZZO
    // ---------------------------------------------------------------------

    private String reuseDescription(Product p) {
        if (p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT)
            return "Riutilizzo: monouso / scartare dopo l'uso.";
        if (p.reuseMode == REUSE_FRESH_RECOMMENDED)
            return "Riutilizzo: il produttore consiglia soluzione di lavoro fresca; nessun reintegro specifico pubblicato.";
        if (p.reuseMode == ChemistrySpecEngine.REUSE_REUSABLE) {
            String s = "Riutilizzo: riutilizzabile.";
            if (p.filmCapacityPerLiter > 0)
                s += "\nCapacità pellicola: " + fmt(p.filmCapacityPerLiter) + " rulli/L.";
            if (p.paperCapacitySqMPerLiter > 0)
                s += "\nCapacità carta: " + fmt(p.paperCapacitySqMPerLiter) + " m²/L.";
            if (p.filmCapacityPerLiter <= 0 && p.paperCapacitySqMPerLiter <= 0)
                s += " Capacità numerica non determinata dalla fonte.";
            return s;
        }
        return "Riutilizzo: non determinato dalla fonte.";
    }

    private String filmCapacityStatus(Product p, double volumeMl) {
        if (p == null) return "—";
        if (p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT)
            return "Monouso: non riutilizzare questo bagno.";
        String k = key(p.name);
        float storedVol = prefs.getFloat("film_bath_volume_" + k, 0f);
        float used = prefs.contains("film_used_units_v2_" + k)
                ? prefs.getFloat("film_used_units_v2_" + k, 0f)
                : prefs.getInt("film_used_" + k, 0);
        if (storedVol > 0 && Math.abs(storedVol - volumeMl) > 1) used = 0;
        if (p.reuseMode != ChemistrySpecEngine.REUSE_REUSABLE)
            return "Riutilizzo non determinato. Equivalenti rullo registrati nel bagno: " + fmt(used) + ".";
        if (p.filmCapacityPerLiter <= 0)
            return "Riutilizzabile; capacità numerica non trovata. Equivalenti rullo registrati: " + fmt(used) + ".";
        double capacity = p.filmCapacityPerLiter * volumeMl / 1000.0;
        double remaining = Math.max(0, capacity - used);
        return "Bagno " + fmt(volumeMl) + " ml · capacità " + fmt(capacity) +
                " rulli equivalenti · usati " + fmt(used) + " · residui " + fmt(remaining) + ".";
    }

    private String paperCapacityStatus(Product p, double volumeMl) {
        if (p == null) return "—";
        if (p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT)
            return "Monouso: non riutilizzare questo bagno.";
        float used = prefs.getFloat("paper_used_sqm_" + key(p.name), 0f);
        float storedVol = prefs.getFloat("paper_bath_volume_" + key(p.name), 0f);
        if (storedVol > 0 && Math.abs(storedVol - volumeMl) > 1) used = 0;
        if (p.reuseMode != ChemistrySpecEngine.REUSE_REUSABLE)
            return "Riutilizzo non determinato. Carta registrata: " + fmt(used) + " m².";
        if (p.paperCapacitySqMPerLiter <= 0)
            return "Riutilizzabile; capacità numerica non trovata. Carta registrata: " + fmt(used) + " m².";
        double capacity = p.paperCapacitySqMPerLiter * volumeMl / 1000.0;
        double remaining = Math.max(0, capacity - used);
        return "Bagno " + fmt(volumeMl) + " ml · capacità " + fmt(capacity) +
                " m² · usati " + fmt(used) + " m² · residui " + fmt(remaining) + " m².";
    }

    private void registerFilmUse(Product p, double volumeMl, double units) {
        if (p == null || p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT) return;
        String k = key(p.name);
        float oldVol = prefs.getFloat("film_bath_volume_" + k, 0f);
        float used = prefs.contains("film_used_units_v2_" + k)
                ? prefs.getFloat("film_used_units_v2_" + k, 0f)
                : prefs.getInt("film_used_" + k, 0);
        if (oldVol <= 0 || Math.abs(oldVol - volumeMl) > 1) used = 0;
        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putFloat("film_used_units_v2_" + k, used + (float) units).apply();
    }

    private void resetFilmBath(Product p, double volumeMl) {
        if (p == null) return;
        String k = key(p.name);
        prefs.edit().putFloat("film_bath_volume_" + k, (float) volumeMl)
                .putInt("film_used_" + k, 0)
                .putFloat("film_used_units_v2_" + k, 0f).apply();
    }

    private void registerPaperUse(Product p, double volumeMl, double areaSqM) {
        if (p == null || p.reuseMode == ChemistrySpecEngine.REUSE_ONE_SHOT || p.reuseMode == REUSE_FRESH_RECOMMENDED) return;
        String k = key(p.name);
        float oldVol = prefs.getFloat("paper_bath_volume_" + k, 0f);
        float used = prefs.getFloat("paper_used_sqm_" + k, 0f);
        if (oldVol <= 0 || Math.abs(oldVol - volumeMl) > 1) used = 0;
        prefs.edit().putFloat("paper_bath_volume_" + k, (float) volumeMl)
                .putFloat("paper_used_sqm_" + k, used + (float) areaSqM).apply();
    }

    private void resetPaperBath(Product p, double volumeMl) {
        if (p == null) return;
        String k = key(p.name);
        prefs.edit().putFloat("paper_bath_volume_" + k, (float) volumeMl)
                .putFloat("paper_used_sqm_" + k, 0f).apply();
    }

    private void appendStoredBathStatus(StringBuilder msg, Product p) {
        String k = key(p.name);
        float filmUsed = prefs.contains("film_used_units_v2_" + k)
                ? prefs.getFloat("film_used_units_v2_" + k, 0f)
                : prefs.getInt("film_used_" + k, 0);
        float filmVol = prefs.getFloat("film_bath_volume_" + k, 0f);
        float paperUsed = prefs.getFloat("paper_used_sqm_" + k, 0f);
        float paperVol = prefs.getFloat("paper_bath_volume_" + k, 0f);
        if (filmVol > 0) msg.append("\nBagno pellicola: ").append(fmt(filmVol))
                .append(" ml · ").append(fmt(filmUsed)).append(" rulli equivalenti registrati.");
        if (paperVol > 0) msg.append("\nBagno carta: ").append(fmt(paperVol))
                .append(" ml · ").append(fmt(paperUsed)).append(" m² registrati.");
    }

    private Product offlineDeveloperProduct(String canonicalName) {
        int reuse = "Foma Universal".equalsIgnoreCase(canonicalName)
                ? ChemistrySpecEngine.REUSE_ONE_SHOT
                : ChemistrySpecEngine.REUSE_UNKNOWN;
        return new Product(canonicalName, ROLE_FILM_DEV, false,
                MdcOfflineStore.dilutionsForDeveloper(canonicalName), new String[0], null,
                null, -1, "", reuse, -1, -1);
    }

    private void repairLegacyInventoryFromOfflineDb() {
        if (!MdcOfflineStore.isReady()) return;
        Set<String> oldSet = getInventory();
        if (oldSet.isEmpty()) return;
        Set<String> newSet = new HashSet<>();
        SharedPreferences.Editor moveDates = prefs.edit();
        for (String oldName : oldSet) {
            String canonical = MdcOfflineStore.canonicalDeveloperName(oldName);
            if (canonical == null) canonical = MdcOfflineStore.canonicalDeveloperForLooseName(oldName);
            if (canonical == null) {
                newSet.add(oldName);
                continue;
            }
            long opened = prefs.getLong("opened_" + key(oldName), 0L);
            Product corrected = offlineDeveloperProduct(canonical);
            saveProductMetadata(corrected);
            newSet.add(canonical);
            if (!oldName.equalsIgnoreCase(canonical)) {
                deleteProductMetadata(oldName);
                moveDates.remove("opened_" + key(oldName));
                if (opened > 0) moveDates.putLong("opened_" + key(canonical), opened);
            }
        }
        moveDates.putStringSet("inventory", newSet).apply();
    }

    private List<String> localProductMatchesForRole(String q, int role) {
        LinkedHashSet<String> out = new LinkedHashSet<>(FullCatalogStore.searchChemicalNames(q, role, 100));
        String needle = q == null ? "" : q.toLowerCase(Locale.ROOT).trim();
        for (Product p : curatedAuxChemistry) {
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
            if (loadSavedProduct(name) == null) saveProductMetadata(curated);
        }
    }

    // ---------------------------------------------------------------------
    // PERSISTENZA MAGAZZINO
    // ---------------------------------------------------------------------

    private Set<String> getInventory() {
        return new HashSet<>(prefs.getStringSet("inventory", new HashSet<>()));
    }

    private void addToInventory(Product p, long openedMillis) {
        saveProductMetadata(p);
        Set<String> set = getInventory();
        set.add(p.name);
        prefs.edit().putStringSet("inventory", set)
                .putLong("opened_" + key(p.name), openedMillis).apply();
    }

    private void replaceInventoryProduct(String oldName, Product p, long openedMillis) {
        Set<String> set = getInventory();
        set.remove(oldName);
        set.add(p.name);
        prefs.edit().putStringSet("inventory", set)
                .remove("opened_" + key(oldName))
                .putLong("opened_" + key(p.name), openedMillis).apply();
        if (!oldName.equalsIgnoreCase(p.name)) deleteProductMetadata(oldName);
        saveProductMetadata(p);
    }

    private void removeFromInventory(String name) {
        Set<String> set = getInventory();
        set.remove(name);
        String k = key(name);
        prefs.edit().putStringSet("inventory", set)
                .remove("opened_" + k)
                .remove("film_used_" + k).remove("film_bath_volume_" + k)
                .remove("paper_used_sqm_" + k).remove("paper_bath_volume_" + k)
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
                .putString("prod_working_" + k, p.workingDilution == null ? "" : p.workingDilution)
                .putString("prod_instructions_" + k, p.stockInstructions == null ? "" : p.stockInstructions)
                .putInt("prod_expiry_" + k, p.expiryDays)
                .putString("prod_source_" + k, p.sourceUrl == null ? "" : p.sourceUrl)
                .putInt("prod_reuse_" + k, p.reuseMode)
                .putFloat("prod_filmcap_" + k, (float) p.filmCapacityPerLiter)
                .putFloat("prod_papercap_" + k, (float) p.paperCapacitySqMPerLiter)
                .apply();
    }

    private void deleteProductMetadata(String name) {
        String k = key(name);
        prefs.edit().remove("prod_saved_" + k).remove("prod_name_" + k)
                .remove("prod_roles_" + k).remove("prod_stock_" + k)
                .remove("prod_film_" + k).remove("prod_paper_" + k)
                .remove("prod_working_" + k).remove("prod_instructions_" + k)
                .remove("prod_expiry_" + k).remove("prod_source_" + k)
                .remove("prod_reuse_" + k).remove("prod_filmcap_" + k)
                .remove("prod_papercap_" + k).apply();
    }

    private Product loadSavedProduct(String name) {
        String k = key(name);
        if (!prefs.getBoolean("prod_saved_" + k, false)) return null;
        return new Product(prefs.getString("prod_name_" + k, name),
                prefs.getInt("prod_roles_" + k, 0),
                prefs.getBoolean("prod_stock_" + k, false),
                splitCsv(prefs.getString("prod_film_" + k, "")),
                splitCsv(prefs.getString("prod_paper_" + k, "")),
                emptyToNull(prefs.getString("prod_working_" + k, "")),
                emptyToNull(prefs.getString("prod_instructions_" + k, "")),
                prefs.getInt("prod_expiry_" + k, -1),
                prefs.getString("prod_source_" + k, ""),
                prefs.getInt("prod_reuse_" + k, ChemistrySpecEngine.REUSE_UNKNOWN),
                prefs.getFloat("prod_filmcap_" + k, -1f),
                prefs.getFloat("prod_papercap_" + k, -1f));
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

    private FilmStock findFilm(String name) {
        return null;
    }

    // ---------------------------------------------------------------------
    // STATO ULTIMA SESSIONE: i campi restano popolati uscendo e rientrando.
    // ---------------------------------------------------------------------
    private void saveCurrentUiState() {
        if (prefs == null) return;
        SharedPreferences.Editor e = prefs.edit();
        if (currentScreen == FILM && filmField != null) {
            e.putString("last_film_name", filmField.getText().toString().trim());
            e.putInt("last_film_nominal", selectedFilm == null ? 0 : selectedFilm.nominalIso);
            e.putString("last_film_format", selectedFilm == null ? "" : selectedFilm.format);
            e.putString("last_film_iso", isoField == null ? "" : isoField.getText().toString());
            e.putString("last_film_rolls", spinnerText(rollsSpinner));
            e.putString("last_film_tank", spinnerText(tankSpinner));
            e.putString("last_film_dev", spinnerText(developerSpinner));
            e.putString("last_film_dil", spinnerText(dilutionSpinner));
            e.putString("last_film_temp", temperatureField == null ? "" : temperatureField.getText().toString());
            e.putString("last_film_stop", spinnerText(stopSpinner));
            e.putString("last_film_fix", spinnerText(fixSpinner));
        } else if (currentScreen == PAPER && paperVolumeField != null) {
            e.putString("last_paper_dev", spinnerText(paperDeveloperSpinner));
            e.putString("last_paper_dil", spinnerText(paperDeveloperDilutionSpinner));
            e.putString("last_paper_stop", spinnerText(paperStopSpinner));
            e.putString("last_paper_fix", spinnerText(paperFixSpinner));
            e.putString("last_paper_volume", paperVolumeField.getText().toString());
            e.putString("last_paper_w", paperWidthField.getText().toString());
            e.putString("last_paper_h", paperHeightField.getText().toString());
            e.putString("last_paper_sheets", paperSheetsField.getText().toString());
        }
        e.apply();
    }

    private void restoreFilmUiState() {
        String film = prefs.getString("last_film_name", "");
        if (!film.isEmpty()) {
            int nominal = prefs.getInt("last_film_nominal", 0);
            String format = prefs.getString("last_film_format", "");
            selectFilm(new FilmStock(film, nominal, format, ""));
        }
        String iso = prefs.getString("last_film_iso", "");
        if (!iso.isEmpty() && isoField != null) isoField.setText(iso);
        String temp = prefs.getString("last_film_temp", "");
        if (!temp.isEmpty() && temperatureField != null) temperatureField.setText(temp);
        selectSpinnerText(rollsSpinner, prefs.getString("last_film_rolls", ""));
        updateCompatibleTanks();
        selectSpinnerText(tankSpinner, prefs.getString("last_film_tank", ""));
        selectSpinnerText(developerSpinner, prefs.getString("last_film_dev", ""));
        selectSpinnerText(stopSpinner, prefs.getString("last_film_stop", ""));
        selectSpinnerText(fixSpinner, prefs.getString("last_film_fix", ""));
        restoreSavedFilmDilution(0);
    }

    private void restoreSavedFilmDilution(int attempt) {
        String wanted = prefs.getString("last_film_dil", "");
        if (wanted.isEmpty() || dilutionSpinner == null) return;
        selectSpinnerText(dilutionSpinner, wanted);
        if (wanted.equals(spinnerText(dilutionSpinner))) return;
        if (attempt < 12) {
            dilutionSpinner.postDelayed(() -> restoreSavedFilmDilution(attempt + 1), 120L);
        }
    }

    private void restorePaperUiState() {
        selectSpinnerText(paperDeveloperSpinner, prefs.getString("last_paper_dev", ""));
        selectSpinnerText(paperStopSpinner, prefs.getString("last_paper_stop", ""));
        selectSpinnerText(paperFixSpinner, prefs.getString("last_paper_fix", ""));
        if (paperDeveloperSpinner != null) paperDeveloperSpinner.post(() ->
                selectSpinnerText(paperDeveloperDilutionSpinner, prefs.getString("last_paper_dil", "")));
        setIfSaved(paperVolumeField, "last_paper_volume");
        setIfSaved(paperWidthField, "last_paper_w");
        setIfSaved(paperHeightField, "last_paper_h");
        setIfSaved(paperSheetsField, "last_paper_sheets");
    }

    private void setIfSaved(EditText field, String key) {
        if (field == null) return;
        String v = prefs.getString(key, "");
        if (!v.isEmpty()) field.setText(v);
    }

    private String spinnerText(Spinner s) {
        return s == null || s.getSelectedItem() == null ? "" : String.valueOf(s.getSelectedItem());
    }

    private void selectSpinnerText(Spinner s, String wanted) {
        if (s == null || wanted == null || wanted.isEmpty() || s.getAdapter() == null) return;
        for (int i=0; i<s.getAdapter().getCount(); i++) {
            if (wanted.equals(String.valueOf(s.getAdapter().getItem(i)))) {
                s.setSelection(i);
                return;
            }
        }
    }

    // ---------------------------------------------------------------------
    // UI / UTILITY
    // ---------------------------------------------------------------------

    private LinearLayout page(String title, String subtitle) {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(16), dp(14), dp(16), dp(28));
        page.setBackgroundColor(BG);

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);

        TextView home = label("⌂", 25, WHITE, true);
        home.setGravity(Gravity.CENTER);
        home.setContentDescription("Torna alla Home");
        home.setOnClickListener(v -> {
            saveCurrentUiState();
            finish();
        });
        top.addView(home, new LinearLayout.LayoutParams(dp(46), dp(46)));

        TextView h = label(title.toUpperCase(Locale.ITALY), 24, WHITE, true);
        h.setGravity(Gravity.CENTER);
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
        accent.setBackground(bg(BURGUNDY_BRIGHT, 2, 0, 0));
        page.addView(accent);
        return page;
    }

    private View homeCard(String text, int color, View.OnClickListener listener) {
        TextView card = label(text + "    ›", 19, WHITE, true);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(20), dp(18), dp(18), dp(18));
        card.setMinHeight(dp(88));
        card.setBackground(bg(color, 12, BORDER, 1));
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
        v.setTextSize(15);
        v.setPadding(dp(13), dp(11), dp(13), dp(11));
        v.setBackground(bg(CARD, 10, BORDER, 1));
        v.setMinHeight(dp(50));
    }

    private EditText edit(String value, int type) {
        EditText e = new EditText(this);
        e.setInputType(type);
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
        ArrayAdapter<String> a = new ArrayAdapter<String>(this,
                android.R.layout.simple_spinner_item, items) {
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
        b.setTextSize(15);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setAllCaps(false);
        b.setMinHeight(dp(52));
        b.setPadding(dp(14), 0, dp(14), 0);
        int stroke = color == BURGUNDY ? BURGUNDY_BRIGHT : BORDER;
        b.setBackground(bg(color, 10, stroke, 1));
        return b;
    }

    private Button smallButton(String text) {
        Button b = actionButton(text, CARD_2);
        b.setMinHeight(dp(44));
        b.setTextSize(13);
        return b;
    }

    private TextView row(String text) {
        TextView v = label(text, 16, WHITE, true);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setPadding(dp(16), dp(14), dp(16), dp(14));
        v.setMinHeight(dp(56));
        v.setBackground(bg(CARD, 10, BORDER, 1));
        return v;
    }

    private void resultLine(LinearLayout parent, String labelText, String value) {
        LinearLayout r = new LinearLayout(this);
        r.setOrientation(LinearLayout.VERTICAL);
        r.setPadding(dp(15), dp(12), dp(15), dp(12));
        r.setBackground(bg(CARD, 10, BORDER, 1));
        r.addView(label(labelText, 11, MUTED, false));
        r.addView(space(4));
        r.addView(label(value, 17, WHITE, true));
        parent.addView(r);
        parent.addView(space(8));
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

    private void replaceSuggestions(ArrayAdapter<String> adapter, List<String> values) {
        adapter.clear(); adapter.addAll(values); adapter.notifyDataSetChanged();
    }

    private Product productAt(List<Product> list, int position) {
        if (list == null || list.isEmpty() || position < 0 || position >= list.size()) return null;
        return list.get(position);
    }

    private List<String> localProductMatches(String q) {
        return new ArrayList<>();
    }

    private List<String> localFilmMatches(String q) {
        return new ArrayList<>();
    }

    private String normalizedMixDilution(String dilution) {
        if (dilution == null) return "";
        String d = dilution.trim().toLowerCase(Locale.ROOT)
                .replace(":", "+").replace(" ", "");
        if ("a".equals(d)) return "1+15";
        if ("b".equals(d)) return "1+31";
        if ("c".equals(d)) return "1+19";
        if ("d".equals(d)) return "1+39";
        if ("e".equals(d)) return "1+47";
        if ("f".equals(d)) return "1+79";
        if ("g".equals(d)) return "1+119";
        if ("h".equals(d)) return "1+63";
        if ("j".equals(d)) return "1+150";
        if (d.matches("[0-9]+")) return "1+" + d;
        return d;
    }

    private double[] mix(double total, String dilution) {
        String d = normalizedMixDilution(dilution);
        if (d.isEmpty()) return null;
        if ("stock".equals(d)) return new double[]{total, 0};
        String[] parts = d.split("\\+");
        if (parts.length < 2) return null;
        try {
            double sum = 0;
            double developerParts = 0;
            for (int i = 0; i < parts.length; i++) {
                double value = Double.parseDouble(parts[i].trim());
                if (value <= 0) return null;
                sum += value;
                if (i < parts.length - 1) developerParts += value;
            }
            if (developerParts <= 0 || sum <= developerParts) return null;
            double concentrate = total * developerParts / sum;
            return new double[]{concentrate, total - concentrate};
        } catch (Exception e) { return null; }
    }

    private String formatDeveloperMix(String developerName, String dilution,
                                      double[] mixed, double total) {
        boolean twoPart = developerName != null &&
                (developerName.toLowerCase(Locale.ROOT).contains("moersch eco") ||
                 developerName.toLowerCase(Locale.ROOT).contains("jobo alpha"));
        String d = normalizedMixDilution(dilution);
        String[] parts = d.split("\\+");
        if (!twoPart || parts.length != 3) return formatMix(mixed, total);
        try {
            double a = Double.parseDouble(parts[0]);
            double b = Double.parseDouble(parts[1]);
            double water = Double.parseDouble(parts[2]);
            double scale = total / (a + b + water);
            return "Parte A " + fmt(a * scale) + " ml + Parte B " + fmt(b * scale) +
                    " ml + " + fmt(water * scale) + " ml acqua · totale " +
                    fmt(total) + " ml";
        } catch (Exception e) { return formatMix(mixed, total); }
    }

    private String formatMix(double[] m, double total) {
        return fmt(m[0]) + " ml + " + fmt(m[1]) + " ml acqua · totale " + fmt(total) + " ml";
    }

    private String fmt(double value) {
        if (Math.abs(value - Math.rint(value)) < 0.01)
            return String.format(Locale.ITALY, "%.0f", value);
        return String.format(Locale.ITALY, "%.2f", value).replaceAll("0+$", "").replaceAll(",$", "");
    }

    private String fmtTemp(double value) { return fmt(value) + " °C"; }

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

    private String emptyToNull(String s) { return s == null || s.trim().isEmpty() ? null : s.trim(); }
    private int parseIntOrMinus(String s) {
        try { return Integer.parseInt(s.trim()); } catch (Exception e) { return -1; }
    }
    private double parseDoubleOrMinus(String s) {
        try { return Double.parseDouble(s.trim().replace(',', '.')); } catch (Exception e) { return -1; }
    }

    private int roleForType(int which) {
        switch (which) {
            case 0: return ROLE_FILM_DEV;
            case 1: return ROLE_PAPER_DEV;
            case 2: return ROLE_FILM_DEV | ROLE_PAPER_DEV;
            case 3: return ROLE_STOP;
            case 4: return ROLE_FIX;
            case 5: return ROLE_WETTING;
            case 6: return ROLE_WASHING;
            case 7: return ROLE_CHEMISTRY;
            default: return ROLE_FILM_DEV;
        }
    }

    private int typeIndexForRole(int role) {
        if ((role & ROLE_FILM_DEV) != 0 && (role & ROLE_PAPER_DEV) != 0) return 2;
        if ((role & ROLE_FILM_DEV) != 0) return 0;
        if ((role & ROLE_PAPER_DEV) != 0) return 1;
        if ((role & ROLE_STOP) != 0) return 3;
        if ((role & ROLE_FIX) != 0) return 4;
        if ((role & ROLE_WETTING) != 0) return 5;
        if ((role & ROLE_WASHING) != 0) return 6;
        if ((role & ROLE_CHEMISTRY) != 0) return 7;
        return 0;
    }

    private Product applyDeveloperProfile(Product p) {
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
        String preparationIt = chemicalTechnicalPreparationIt(p.name);
        if (!preparationIt.isEmpty() &&
                (instructions == null || instructions.trim().isEmpty() ||
                        sameTechnicalText(instructions, preparation) || containsEnglishTechnical(instructions))) {
            instructions = preparationIt;
        } else if ((instructions == null || instructions.trim().isEmpty()) && preparation != null && !preparation.trim().isEmpty()) {
            instructions = preparation.trim();
        }
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

    private String chemicalTechnicalSummaryIt(String name) {
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
        String v = safeItalianTechnical(value);
        if (v.isEmpty()) return;
        String label = "STOCK_PREPARATO".equals(kind)
                ? "Durata stock preparato · bottiglia piena"
                : "Durata concentrato aperto · bottiglia piena";
        appendTechRaw(out, label, v);
        String c = safeItalianTechnical(condition);
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

    private static final class OperationalLifeInfo {
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
        if (!info.calculable()) return "Durata: " + safeItalianTechnical(info.text) + "\nScadenza automatica non calcolabile da un intervallo non numerico.";
        Calendar c = Calendar.getInstance();
        c.setTimeInMillis(startMillis);
        if (info.months > 0) c.add(Calendar.MONTH, info.months);
        if (info.days > 0) c.add(Calendar.DAY_OF_MONTH, info.days);
        if (info.hours > 0) c.add(Calendar.HOUR_OF_DAY, info.hours);
        return new SimpleDateFormat("dd/MM/yyyy", Locale.ITALY).format(c.getTime());
    }

    private String normalizeTechnicalName(String value) {
        if (value == null) return "";
        String n = java.text.Normalizer.normalize(value, java.text.Normalizer.Form.NFD)
                .replaceAll("\\p{M}+", "").toLowerCase(Locale.ROOT);
        n = n.replaceAll("[^a-z0-9+]+", " ").trim().replaceAll("\\s+", " ");
        return n;
    }

    private String cleanTechnicalText(String value) {
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
                " the ", " and ", " with ", " when ", " should ", " would ", " could ",
                " stored ", " store ", " keep ", " working ", " working solution ",
                " original package ", " minimum ", " defines ", " processing ",
                " explicitly ", " before ", " after ", " protected ", " darkness ",
                " oxidation ", " later ", " replace ", " guaranteed ", " reached ",
                " direct sun ", " air access ", " unopened ", " opened concentrate ",
                " prepared ", " manufacturer ", " depending on ", " once opened ",
                " use once ", " discard ", " recommended ", " about ",
                " per litre ", " per liter ", " rolls ", " sheets ", " developer ",
                " replenisher ", " concentrate ", " powder ", " liquid ",
                " full-strength ", " full strength ", " full closed ", " closed container ",
                " without use ", " lists ", " useful tank ", " chemistry matrix ",
                " us gallon ", " bottle ", " shelf life ", " dissolve ", " water ",
                " stir ", " cool ", " fresh ", " reuse ", " partially exhausted ",
                " well-closed ", " ready-to-use ", " at least ", " up to "
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

    private String prettyProfileValue(String value) {
        if (value == null) return "";
        return value.replace('_', ' ').trim();
    }

    private boolean hasFormatSuffix(String s) {
        String x = s.toLowerCase(Locale.ROOT).trim();
        return x.endsWith("35 mm") || x.endsWith("120") || x.endsWith("4×5") || x.endsWith("4x5") || x.endsWith("sheet");
    }

    private String cleanSearchTitle(String s) {
        if (s == null) return "";
        return s.replaceAll("\\s*[-–—|]\\s*(official|product|developer|film|fotoimpex|amazon).*$", "").trim();
    }

    private boolean usefulInstruction(String s) {
        return s != null && s.length() > 20 &&
                s.matches("(?s).*[0-9]+(?:[.,][0-9]+)?\\s*(?:ml|l|litre|liter|litro|litri|°c|° C|c\\b).*" );
    }

    private String normalize(String s) {
        if (s == null) return "";
        return s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+", " ").trim();
    }

    private void openUrl(String url) {
        try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); }
        catch (Exception e) { toast("Impossibile aprire la fonte."); }
    }

    private void resultFilmError(String message) {
        if (filmResultBox == null) return;
        filmResultBox.removeAllViews();
        TextView t = label(message, 15, WHITE, true);
        t.setPadding(dp(16), dp(16), dp(16), dp(16));
        t.setBackground(bg(BURGUNDY, 14, 0, 0));
        filmResultBox.addView(t);
    }

    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_SHORT).show(); }
    private int dp(float v) { return (int) (v * getResources().getDisplayMetrics().density + 0.5f); }

    private abstract class SimpleItemSelectedListener implements AdapterView.OnItemSelectedListener {
        @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) { selected(position); }
        @Override public void onNothingSelected(AdapterView<?> parent) {}
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
        final int reuseMode;
        final double filmCapacityPerLiter;
        final double paperCapacitySqMPerLiter;

        Product(String name, int roles, boolean stockPrep,
                String[] filmDilutions, String[] paperDilutions,
                String workingDilution, String stockInstructions,
                int expiryDays, String sourceUrl, int reuseMode,
                double filmCapacityPerLiter, double paperCapacitySqMPerLiter) {
            this.name = name;
            this.roles = roles;
            this.stockPrep = stockPrep;
            this.filmDilutions = filmDilutions == null ? new String[0] : filmDilutions;
            this.paperDilutions = paperDilutions == null ? new String[0] : paperDilutions;
            this.workingDilution = workingDilution;
            this.stockInstructions = stockInstructions;
            this.expiryDays = expiryDays;
            this.sourceUrl = sourceUrl == null ? "" : sourceUrl;
            this.reuseMode = reuseMode;
            this.filmCapacityPerLiter = filmCapacityPerLiter;
            this.paperCapacitySqMPerLiter = paperCapacitySqMPerLiter;
        }

        Product withRole(int role) {
            return new Product(name, role, stockPrep, filmDilutions, paperDilutions,
                    workingDilution, stockInstructions, expiryDays, sourceUrl,
                    reuseMode, filmCapacityPerLiter, paperCapacitySqMPerLiter);
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
        final int maxSheet;
        Tank(String name, int rotaryMl, int max35, int max120, int maxSheet) {
            this.name = name;
            this.rotaryMl = rotaryMl;
            this.max35 = max35;
            this.max120 = max120;
            this.maxSheet = maxSheet;
        }
    }
}
