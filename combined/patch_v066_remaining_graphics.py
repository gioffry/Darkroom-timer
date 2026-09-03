#!/usr/bin/env python3
"""Darkroom 0.6.6: final coherent graphics for the three remaining modules.

Only presentation and information hierarchy are changed. Paper calculations,
large-format persistence and maintenance content/navigation are protected.
"""

from pathlib import Path


ASSISTANT = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")
LARGE_FORMAT = Path("combined/src/main/java/it/darkroom/timer/largeformat/LargeFormatActivity.java")
MAINTENANCE = Path("combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java")


def rep(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)
    if found != count:
        raise SystemExit(f"v0.6.6 {label}: expected {count}, found {found}")
    return text.replace(old, new)


def java_method(text: str, signature: str) -> str:
    start = text.find(signature)
    if start < 0:
        raise SystemExit(f"v0.6.6 method missing: {signature}")
    opening = text.find("{", start)
    if opening < 0:
        raise SystemExit(f"v0.6.6 method has no body: {signature}")
    depth = 0
    in_string = False
    in_char = False
    escaped = False
    line_comment = False
    block_comment = False
    i = opening
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 1
        elif in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif in_char:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "'":
                in_char = False
        elif ch == "/" and nxt == "/":
            line_comment = True
            i += 1
        elif ch == "/" and nxt == "*":
            block_comment = True
            i += 1
        elif ch == '"':
            in_string = True
        elif ch == "'":
            in_char = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise SystemExit(f"v0.6.6 unterminated method: {signature}")


def replace_method(text: str, signature: str, replacement: str, label: str) -> str:
    old = java_method(text, signature)
    if not replacement.startswith(signature):
        raise SystemExit(f"v0.6.6 {label}: replacement signature mismatch")
    return rep(text, old, replacement, label)


assistant = ASSISTANT.read_text(encoding="utf-8")
large = LARGE_FORMAT.read_text(encoding="utf-8")
maintenance = MAINTENANCE.read_text(encoding="utf-8")

markers = (
    "PAPER_VISUAL_066" in assistant,
    "LARGE_FORMAT_VISUAL_066" in large,
    "MAINTENANCE_VISUAL_066" in maintenance,
)
if all(markers):
    print("remaining_graphics_066=ALREADY_APPLIED")
    raise SystemExit(0)
if any(markers):
    raise SystemExit("v0.6.6 partial application detected")
if "FILM_VISUAL_065" not in assistant:
    raise SystemExit("v0.6.6 requires the exact v0.6.5 Assistant source")


# ---------------------------------------------------------------------------
# Paper baths: green identity, ordered input groups and compact result cards.
# ---------------------------------------------------------------------------

assistant_protected = [
    "    private void refreshFilmDilutions()",
    "    private void calculateFilmOnline()",
    "    private void showDevelopmentResultSafely(DevTimeEngine.Result result,",
    "    private void renderFilmCapacityForFormat(Product dev, Product stop, Product fix,",
    "    private void renderFilmCapacity(Product dev, Product stop, Product fix, double volumeMl)",
    "    private void registerFilmUse(Product p, double volumeMl, double units)",
    "    private void resetFilmBath(Product p, double volumeMl)",
    "    private void registerPaperSession()",
    "    private void renderPaperCapacity(Product dev, Product stop, Product fix, double volumeMl)",
    "    private void registerPaperUse(Product p, double volumeMl, double areaSqM)",
    "    private void resetPaperBath(Product p, double volumeMl)",
    "    private void saveCurrentUiState()",
    "    private void restoreFilmUiState()",
    "    private void restorePaperUiState()",
]
assistant_before = {s: java_method(assistant, s) for s in assistant_protected}

assistant = rep(
    assistant,
    "    // FILM_VISUAL_065 — film-development hierarchy only; process and calculations unchanged.\n",
    "    // FILM_VISUAL_065 — film-development hierarchy only; process and calculations unchanged.\n"
    "    // PAPER_VISUAL_066 — paper-bath hierarchy only; calculations and counters unchanged.\n",
    "paper marker",
)
assistant = rep(
    assistant,
    "    private static final int FILM_SECONDARY = Color.rgb(50, 65, 71);\n",
    "    private static final int FILM_SECONDARY = Color.rgb(50, 65, 71);\n"
    "    private static final int PAPER_FILL = Color.rgb(45, 99, 72);\n"
    "    private static final int PAPER_ACTION = Color.rgb(57, 133, 94);\n"
    "    private static final int PAPER_ACCENT = Color.rgb(84, 167, 121);\n"
    "    private static final int PAPER_BORDER = Color.rgb(64, 139, 98);\n"
    "    private static final int PAPER_SECONDARY = Color.rgb(50, 65, 61);\n",
    "paper palette",
)

assistant = replace_method(
    assistant,
    "    private void showPaper()",
    '''    private void showPaper() {
        currentScreen = PAPER;
        LinearLayout page = page("Bagni stampa", "Prepara e registra i bagni per la stampa.");
        List<Product> developers = inventoryProductsByRole(ROLE_PAPER_DEV);
        List<Product> stops = inventoryProductsByRole(ROLE_STOP);
        List<Product> fixes = inventoryProductsByRole(ROLE_FIX);

        LinearLayout chemistry = paperSection(
                "1 · CHIMICA DI STAMPA",
                "Rivelatore, diluizione, arresto e fissaggio");
        paperDeveloperSpinner = productSpinner(developers, "Nessun rivelatore carta in magazzino");
        paperDeveloperDilutionSpinner = spinner(new String[]{"—"});
        paperStopSpinner = productSpinner(stops, "Nessun arresto in magazzino");
        paperFixSpinner = productSpinner(fixes, "Nessun fissaggio in magazzino");
        chemistry.addView(fieldBlock("RIVELATORE CARTA", paperDeveloperSpinner));
        chemistry.addView(fieldBlock("DILUIZIONE RIVELATORE", paperDeveloperDilutionSpinner));
        chemistry.addView(fieldBlock("ARRESTO", paperStopSpinner));
        chemistry.addView(fieldBlock("FISSAGGIO", paperFixSpinner));
        page.addView(chemistry);
        page.addView(space(11));

        paperDeveloperSpinner.setOnItemSelectedListener(new SimpleItemSelectedListener() {
            @Override public void selected(int position) {
                Product p = productAt(developers, position);
                String[] ds = p == null || p.paperDilutions.length == 0
                        ? new String[]{"—"} : p.paperDilutions;
                setSpinnerItems(paperDeveloperDilutionSpinner, ds);
            }
        });

        LinearLayout usage = paperSection(
                "2 · VOLUME E UTILIZZO",
                "Quantità del bagno e carta da registrare nei contatori");
        paperVolumeField = edit("1000", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        usage.addView(fieldBlock("VOLUME DA PREPARARE (ml)", paperVolumeField));
        paperWidthField = edit("24", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        usage.addView(fieldBlock("LARGHEZZA CARTA (cm)", paperWidthField));
        paperHeightField = edit("30", InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        usage.addView(fieldBlock("ALTEZZA CARTA (cm)", paperHeightField));
        paperSheetsField = edit("1", InputType.TYPE_CLASS_NUMBER);
        usage.addView(fieldBlock("NUMERO FOGLI", paperSheetsField));
        page.addView(usage);
        page.addView(space(12));

        Button calc = paperButton("CALCOLA", PAPER_ACTION);
        calc.setOnClickListener(v -> calculatePaper(developers, stops, fixes));
        page.addView(calc);
        page.addView(space(16));
        paperResultBox = new LinearLayout(this);
        paperResultBox.setOrientation(LinearLayout.VERTICAL);
        page.addView(paperResultBox);
        page.addView(space(80));
        setContentView(scroll(page));
        restorePaperUiState();
    }''',
    "paper form",
)

assistant = replace_method(
    assistant,
    "    private void calculatePaper(List<Product> developers, List<Product> stops, List<Product> fixes)",
    '''    private void calculatePaper(List<Product> developers, List<Product> stops, List<Product> fixes) {
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

        LinearLayout preparation = paperInformationCard("PREPARAZIONE BAGNI");
        addPaperResultField(preparation, "RIVELATORE · " + dev.name,
                devDilution + " · " + formatMix(devMix, volume));
        addPaperResultField(preparation, "ARRESTO · " + stop.name,
                stopDilution + " · " + formatMix(stopMix, volume));
        addPaperResultField(preparation, "FISSAGGIO · " + fix.name,
                fixDilution + " · " + formatMix(fixMix, volume));
        paperResultBox.addView(preparation);
        paperResultBox.addView(space(10));

        String paperTech = chemicalTechnicalSummaryIt(dev.name);
        if (!paperTech.isEmpty()) {
            LinearLayout technicalBody = paperAccordionBody();
            TextView technical = label(paperTech, 14, WHITE, false);
            technical.setLineSpacing(0f, 1.12f);
            technicalBody.addView(technical);
            addPaperAccordion(paperResultBox, "SCHEDA TECNICA RIVELATORE",
                    "Preparazione · conservazione · capacità", technicalBody);
        }

        paperCapacityBox = paperAccordionBody();
        renderPaperCapacity(dev, stop, fix, volume);
        addPaperAccordion(paperResultBox, "RIUTILIZZO BAGNI",
                "Capacità e contatori disponibili", paperCapacityBox);

        Button register = paperButton("REGISTRA STAMPA", PAPER_ACTION);
        register.setOnClickListener(v -> registerPaperSession());
        paperResultBox.addView(register);
        paperResultBox.addView(space(9));
        Button fresh = paperButton("NUOVO BAGNO / AZZERA CONTATORE", PAPER_SECONDARY);
        fresh.setOnClickListener(v -> {
            resetPaperBath(dev, volume);
            resetPaperBath(stop, volume);
            resetPaperBath(fix, volume);
            renderPaperCapacity(dev, stop, fix, volume);
            toast("Contatori del bagno azzerati.");
        });
        paperResultBox.addView(fresh);
        paperResultBox.addView(space(20));
    }''',
    "paper result",
)

assistant = replace_method(
    assistant,
    "    private LinearLayout page(String title, String subtitle)",
    '''    private LinearLayout page(String title, String subtitle) {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(16), dp(14), dp(16), dp(28));
        page.setBackgroundColor(BG);
        boolean chemicalPage = "Prodotti chimici".equalsIgnoreCase(title);
        boolean filmPage = "Sviluppo pellicola".equalsIgnoreCase(title);
        boolean paperPage = "Bagni stampa".equalsIgnoreCase(title);

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);

        TextView home = label("⌂", 25, filmPage || paperPage ? IVORY : WHITE, true);
        home.setGravity(Gravity.CENTER);
        home.setContentDescription("Torna alla Home");
        home.setOnClickListener(v -> {
            saveCurrentUiState();
            finish();
        });
        top.addView(home, new LinearLayout.LayoutParams(dp(46), dp(46)));

        TextView h = label(title.toUpperCase(Locale.ITALY), filmPage || paperPage ? 23 : 24,
                filmPage || paperPage ? IVORY : WHITE, true);
        h.setGravity(Gravity.CENTER);
        if (chemicalPage || filmPage || paperPage)
            h.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
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
        int accentColor = chemicalPage ? CHEM_ACCENT
                : filmPage ? FILM_ACCENT : paperPage ? PAPER_ACCENT : BURGUNDY_BRIGHT;
        accent.setBackground(bg(accentColor, 2, 0, 0));
        page.addView(accent);
        return page;
    }''',
    "paper page header",
)

paper_helpers = '''    private LinearLayout paperSection(String title, String detail) {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setPadding(dp(14), dp(13), dp(14), dp(4));
        section.setBackground(bg(BG, 13, PAPER_BORDER, 1));
        section.addView(label(title, 15, PAPER_ACCENT, true));
        TextView subtitle = label(detail, 12, MUTED, false);
        subtitle.setPadding(0, dp(3), 0, dp(13));
        section.addView(subtitle);
        return section;
    }

    private LinearLayout paperInformationCard(String title) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(15), dp(13), dp(15), dp(14));
        card.setBackground(bg(BG, 13, PAPER_BORDER, 1));
        card.addView(label(title, 16, PAPER_ACCENT, true));
        return card;
    }

    private void addPaperResultField(LinearLayout parent, String title, String value) {
        TextView heading = label(title, 11, PAPER_ACCENT, true);
        heading.setPadding(0, dp(10), 0, dp(3));
        parent.addView(heading);
        parent.addView(label(value, 16, WHITE, true));
    }

    private LinearLayout paperAccordionBody() {
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(13), dp(8), dp(13), dp(11));
        return body;
    }

    private void addPaperAccordion(LinearLayout parent, String title,
                                   String compactSummary, LinearLayout body) {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setBackground(bg(BG, 13, PAPER_BORDER, 1));
        TextView header = label("▸ " + title + "\\n" + compactSummary, 14, WHITE, true);
        header.setPadding(dp(15), dp(12), dp(15), dp(12));
        header.setBackground(bg(PAPER_FILL, 12, 0, 0));
        body.setVisibility(View.GONE);
        final boolean[] open = new boolean[]{false};
        header.setOnClickListener(v -> {
            open[0] = !open[0];
            body.setVisibility(open[0] ? View.VISIBLE : View.GONE);
            header.setText((open[0] ? "▾ " : "▸ ") + title + "\\n" + compactSummary);
        });
        section.addView(header);
        section.addView(body);
        parent.addView(section);
        parent.addView(space(10));
    }

    private Button paperButton(String text, int fill) {
        Button button = actionButton(text, fill);
        button.setTextColor(WHITE);
        button.setAllCaps(false);
        button.setBackground(bg(fill, 10, 0, 0));
        return button;
    }

'''
assistant = rep(
    assistant,
    "    private LinearLayout fieldBlock(String labelText, View field) {\n",
    paper_helpers + "    private LinearLayout fieldBlock(String labelText, View field) {\n",
    "paper helpers",
)
assistant = rep(
    assistant,
    "        int fieldLabelColor = currentScreen == FILM ? FILM_ACCENT : MUTED;\n",
    "        int fieldLabelColor = currentScreen == FILM ? FILM_ACCENT\n"
    "                : currentScreen == PAPER ? PAPER_ACCENT : MUTED;\n",
    "paper field labels",
)
assistant = rep(
    assistant,
    "        int inputBorder = currentScreen == FILM ? FILM_BORDER : BORDER;\n",
    "        int inputBorder = currentScreen == FILM ? FILM_BORDER\n"
    "                : currentScreen == PAPER ? PAPER_BORDER : BORDER;\n",
    "paper input borders",
)
assistant = rep(
    assistant,
    "        int spinnerBorder = currentScreen == FILM ? FILM_BORDER : BORDER;\n",
    "        int spinnerBorder = currentScreen == FILM ? FILM_BORDER\n"
    "                : currentScreen == PAPER ? PAPER_BORDER : BORDER;\n",
    "paper selector borders",
)
assistant = rep(
    assistant,
    '''        boolean filmInformation = currentScreen == FILM;
        r.setBackground(bg(filmInformation ? BG : CARD, 10,
                filmInformation ? FILM_BORDER : BORDER, 1));
        r.addView(label(labelText, 11,
                filmInformation ? FILM_ACCENT : MUTED, filmInformation));
''',
    '''        boolean filmInformation = currentScreen == FILM;
        boolean paperInformation = currentScreen == PAPER;
        r.setBackground(bg(filmInformation || paperInformation ? BG : CARD, 10,
                filmInformation ? FILM_BORDER : paperInformation ? PAPER_BORDER : BORDER, 1));
        r.addView(label(labelText, 11,
                filmInformation ? FILM_ACCENT : paperInformation ? PAPER_ACCENT : MUTED,
                filmInformation || paperInformation));
''',
    "paper result information",
)

assistant_after = {s: java_method(assistant, s) for s in assistant_protected}
for signature in assistant_protected:
    if assistant_before[signature] != assistant_after[signature]:
        raise SystemExit(f"v0.6.6 protected Assistant logic changed: {signature}")

for callback in [
    "v -> calculatePaper(developers, stops, fixes)",
    "v -> registerPaperSession()",
    "resetPaperBath(dev, volume);",
    "resetPaperBath(stop, volume);",
    "resetPaperBath(fix, volume);",
]:
    if assistant.count(callback) != 1:
        raise SystemExit(f"v0.6.6 paper callback integrity failure: {callback}")


# ---------------------------------------------------------------------------
# Large format: violet module identity, filled actions, outlined information.
# ---------------------------------------------------------------------------

large_protected = [
    "    private String sideSummary(Side side)",
    "    private String statusLabel(String status)",
    "    private String normaliseStatus(String status)",
    "    private int zoneGap(Side side)",
    "    private int nextNumber()",
    "    private String now()",
    "    private void load()",
    "    private boolean readV2(String raw)",
    "    private void readSide(JSONObject o, Side side)",
    "    private int parseInt(String value, int fallback)",
    "    private void save()",
    "    private JSONObject sideJson(Side side)",
]
large_before = {s: java_method(large, s) for s in large_protected}

large = rep(
    large,
    "/** Registro 4x5: ogni chassis ha due lati indipendenti A/B. */\n",
    "/** Registro 4x5: ogni chassis ha due lati indipendenti A/B. */\n"
    "// LARGE_FORMAT_VISUAL_066 — presentation only; chassis data model unchanged.\n",
    "large-format marker",
)
large = rep(
    large,
    "    private static final int BORDER = Color.rgb(164, 139, 105);\n",
    "    private static final int BORDER = Color.rgb(164, 139, 105);\n"
    "    private static final int VIOLET_FILL = Color.rgb(91, 70, 113);\n"
    "    private static final int VIOLET_ACTION = Color.rgb(113, 83, 143);\n"
    "    private static final int VIOLET_ACCENT = Color.rgb(166, 130, 196);\n"
    "    private static final int VIOLET_BORDER = Color.rgb(128, 96, 157);\n"
    "    private static final int VIOLET_SECONDARY = Color.rgb(63, 70, 77);\n"
    "    private static final int DELETE_ACTION = Color.rgb(124, 47, 47);\n",
    "large-format palette",
)

large = replace_method(
    large,
    "    private void buildFrame()",
    '''    private void buildFrame() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(18), dp(18), dp(28));
        scroll.addView(root, new ScrollView.LayoutParams(-1, -2));

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);
        TextView back = label("⌂", 25, IVORY, true);
        back.setGravity(Gravity.CENTER);
        back.setContentDescription("Torna alla Home");
        back.setOnClickListener(v -> finish());
        top.addView(back, new LinearLayout.LayoutParams(dp(46), dp(46)));

        TextView title = label("GRANDE FORMATO", 25, IVORY, true);
        title.setGravity(Gravity.CENTER);
        title.setLetterSpacing(0.035f);
        top.addView(title, new LinearLayout.LayoutParams(0, dp(46), 1f));
        top.addView(new View(this), new LinearLayout.LayoutParams(dp(46), dp(46)));
        root.addView(top, lp(-1, dp(46)));

        TextView sub = label("CHASSIS 4×5 · LATI A/B", 12, MUTED, true);
        sub.setGravity(Gravity.CENTER_HORIZONTAL);
        sub.setLetterSpacing(0.08f);
        root.addView(sub, margin(lp(-1, -2), 0, 4, 0, 7));

        View accent = new View(this);
        GradientDrawable accentBg = new GradientDrawable();
        accentBg.setColor(VIOLET_ACCENT);
        accentBg.setCornerRadius(dp(2));
        accent.setBackground(accentBg);
        LinearLayout.LayoutParams accentLp = new LinearLayout.LayoutParams(dp(34), dp(2));
        accentLp.gravity = Gravity.CENTER_HORIZONTAL;
        accentLp.setMargins(0, 0, 0, dp(19));
        root.addView(accent, accentLp);

        body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        root.addView(body, lp(-1, -2));
        setContentView(scroll);
    }''',
    "large-format header",
)

large = rep(
    large,
    "        gap.setBackground(statusBackground(STATUS_EXPOSED, true));\n",
    "        gap.setBackground(informationBg());\n",
    "large-format static gap",
)
large = rep(
    large,
    '        TextView now = action("ADESSO", false);\n',
    '        TextView now = action("ADESSO", true);\n',
    "large-format now action",
)
large = rep(
    large,
    '''        TextView delete = action("ELIMINA CHASSIS", false);
        delete.setTextColor(Color.rgb(197, 126, 109));
''',
    '''        TextView delete = action("ELIMINA CHASSIS", DELETE_ACTION);
''',
    "large-format destructive action",
)
large = rep(
    large,
    "        v.setAlpha(active ? 1f : 0.67f);\n",
    "        v.setAlpha(active ? 1f : 0.82f);\n",
    "large-format status legibility",
)
large = rep(
    large,
    "        g.setStroke(dp(active ? 2 : 1), active ? IVORY : BORDER);\n",
    "        g.setStroke(dp(active ? 2 : 1), active ? IVORY : VIOLET_BORDER);\n",
    "large-format status border",
    count=2,
)

large = replace_method(
    large,
    "    private void paintChoiceButton(TextView v, boolean active, String paletteStatus)",
    '''    private void paintChoiceButton(TextView v, boolean active, String paletteStatus) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(active ? statusColor(paletteStatus) : VIOLET_FILL);
        g.setCornerRadius(dp(9));
        g.setStroke(dp(active ? 2 : 1), active ? IVORY : VIOLET_BORDER);
        v.setBackground(g);
        v.setAlpha(active ? 1f : 0.84f);
    }''',
    "large-format choices",
)
large = replace_method(
    large,
    "    private GradientDrawable inputBg()",
    '''    private GradientDrawable inputBg() {
        GradientDrawable g = new GradientDrawable();
        g.setColor(BG);
        g.setCornerRadius(dp(9));
        g.setStroke(dp(1), VIOLET_BORDER);
        return g;
    }''',
    "large-format inputs",
)
large = replace_method(
    large,
    "    private TextView sectionTitle(String text)",
    '''    private TextView sectionTitle(String text) {
        TextView v = label(text, 12, VIOLET_ACCENT, true);
        v.setLetterSpacing(0.08f);
        return v;
    }''',
    "large-format section labels",
)
large = replace_method(
    large,
    "    private TextView action(String text, boolean primary)",
    '''    private TextView action(String text, boolean primary) {
        return action(text, primary ? VIOLET_ACTION : VIOLET_SECONDARY);
    }''',
    "large-format action routing",
)
large = rep(
    large,
    "    private GradientDrawable cardBg() {\n",
    '''    private TextView action(String text, int fill) {
        TextView v = label(text, 14, IVORY, true);
        v.setGravity(Gravity.CENTER);
        GradientDrawable g = new GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(dp(10));
        v.setBackground(g);
        return v;
    }

    private GradientDrawable informationBg() {
        GradientDrawable g = new GradientDrawable();
        g.setColor(BG);
        g.setCornerRadius(dp(10));
        g.setStroke(dp(1), VIOLET_BORDER);
        return g;
    }

    private GradientDrawable cardBg() {
''',
    "large-format action helpers",
)
large = replace_method(
    large,
    "    private GradientDrawable cardBg()",
    '''    private GradientDrawable cardBg() {
        GradientDrawable g = new GradientDrawable();
        g.setColor(BG);
        g.setCornerRadius(dp(12));
        g.setStroke(dp(1), VIOLET_BORDER);
        return g;
    }''',
    "large-format information cards",
)

large_after = {s: java_method(large, s) for s in large_protected}
for signature in large_protected:
    if large_before[signature] != large_after[signature]:
        raise SystemExit(f"v0.6.6 protected large-format logic changed: {signature}")
for callback, expected in [
    ("chassis.add(c);", 3),
    ("side.status = newStatus;", 1),
    ("chassis.remove(chassisItem);", 1),
    ("row.setOnClickListener(v -> showSideEditor(chassisItem, side, sideName));", 1),
]:
    if large.count(callback) != expected:
        raise SystemExit(f"v0.6.6 large-format callback integrity failure: {callback}")


# ---------------------------------------------------------------------------
# Use and maintenance: slate identity, filled navigation, outlined content.
# ---------------------------------------------------------------------------

content_start = maintenance.index("    private static final String EV_TABLE_QUESTION")
content_end = maintenance.index("    @Override protected void onCreate")
maintenance_reference_before = maintenance[content_start:content_end]
maintenance_protected = [
    "    private void renderManuals()",
    "    private void renderMinolta()",
    "    private void renderTechnique()",
    "    private void renderRolleiAccessories()",
    "    private void renderRollei35Accessories()",
    "    private void renderRollei28Accessories()",
    "    private void renderMaintenance()",
    "    private void renderCookbook()",
    "    private void renderFaqPage(String heading,String source,String[] questions,String[] answers,String url,String urlLabel)",
    "    private void addFaqMatches(List<FaqHit> out,String section,String[] qs,String[] as,String needle)",
    "    private void openUrl(String url)",
]
maintenance_before = {s: java_method(maintenance, s) for s in maintenance_protected}

maintenance = rep(
    maintenance,
    "/** Autonomous reference module. No Timer state, SONOFF state or Assistant state is read or written here. */\n",
    "/** Autonomous reference module. No Timer state, SONOFF state or Assistant state is read or written here. */\n"
    "// MAINTENANCE_VISUAL_066 — reference content and navigation behaviour unchanged.\n",
    "maintenance marker",
)
maintenance = rep(
    maintenance,
    "    private static final int RED = Color.rgb(124, 31, 31);\n",
    "    private static final int RED = Color.rgb(124, 31, 31);\n"
    "    private static final int IVORY = Color.rgb(235, 210, 174);\n"
    "    private static final int SLATE_FILL = Color.rgb(63, 70, 77);\n"
    "    private static final int SLATE_ACTION = Color.rgb(79, 88, 97);\n"
    "    private static final int SLATE_ACCENT = Color.rgb(130, 144, 157);\n"
    "    private static final int SLATE_BORDER = Color.rgb(92, 104, 115);\n",
    "maintenance palette",
)
maintenance = rep(
    maintenance,
    '        body.addView(navCard("APP DARKROOM","Guida completa v0.2.8 e 10 FAQ operative",()->navigate(this::renderDarkroom)));\n',
    '        body.addView(navCard("APP DARKROOM","Guida operativa e 10 FAQ",()->navigate(this::renderDarkroom)));\n',
    "maintenance stale home version",
)
maintenance = rep(
    maintenance,
    '''        renderFaqPage("APP DARKROOM","Uso operativo di Darkroom · guida completa v0.2.8",Q_DARKROOM,A_DARKROOM,DARKROOM_GUIDE_URL,"APRI GUIDA COMPLETA PDF");
        notice("La v0.2.9 aggiunge queste FAQ e una correzione grafica alla Home; il funzionamento operativo documentato nella guida v0.2.8 resta invariato.");
''',
    '''        renderFaqPage("APP DARKROOM","Uso operativo di Darkroom · guida completa",Q_DARKROOM,A_DARKROOM,DARKROOM_GUIDE_URL,"APRI GUIDA COMPLETA PDF");
        notice("La guida PDF resta disponibile come riferimento completo; queste FAQ raccolgono le risposte operative più rapide.");
''',
    "maintenance stale guide version",
)
maintenance = rep(
    maintenance,
    "GradientDrawable bg=new GradientDrawable(); bg.setColor(PANEL); bg.setCornerRadius(dp(12)); bg.setStroke(dp(1),BRONZE); search.setBackground(bg);",
    "GradientDrawable bg=new GradientDrawable(); bg.setColor(BG); bg.setCornerRadius(dp(12)); bg.setStroke(dp(1),SLATE_BORDER); search.setBackground(bg);",
    "maintenance search field",
)

maintenance = replace_method(
    maintenance,
    "    private void begin(String heading,String subheading)",
    '''    private void begin(String heading,String subheading) {
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        body=new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(16),dp(14),dp(16),dp(28));
        scroll.addView(body,new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout top=new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);
        TextView back=actionText(backStack.isEmpty()?"⌂":"←");
        back.setTextSize(25);
        back.setPadding(0,0,0,0);
        back.setGravity(Gravity.CENTER);
        back.setContentDescription(backStack.isEmpty()?"Torna alla Home":"Indietro");
        back.setOnClickListener(v->onBackPressed());
        top.addView(back,new LinearLayout.LayoutParams(dp(46),dp(46)));
        TextView h=title(heading,23);
        h.setTextColor(IVORY);
        h.setTypeface(Typeface.create(Typeface.SERIF,Typeface.BOLD));
        h.setGravity(Gravity.CENTER);
        top.addView(h,new LinearLayout.LayoutParams(0,dp(46),1f));
        top.addView(new View(this),new LinearLayout.LayoutParams(dp(46),dp(46)));
        body.addView(top,new LinearLayout.LayoutParams(-1,dp(46)));

        if(subheading!=null&&!subheading.isEmpty()){
            TextView sub=subtitle(subheading);
            sub.setGravity(Gravity.CENTER);
            body.addView(sub,margin(-1,-2,dp(8),dp(5),dp(8),dp(8)));
        }
        View accent=new View(this);
        accent.setBackground(filledPanelBg(SLATE_ACCENT,2));
        LinearLayout.LayoutParams accentLp=margin(dp(34),dp(2),0,dp(3),0,dp(18));
        accentLp.gravity=Gravity.CENTER_HORIZONTAL;
        body.addView(accent,accentLp);
        setContentView(scroll);
    }''',
    "maintenance header",
)

maintenance = replace_method(
    maintenance,
    "    private LinearLayout navCard(String heading,String detail,Runnable action)",
    '''    private LinearLayout navCard(String heading,String detail,Runnable action) {
        LinearLayout c=card();
        c.setBackground(filledPanelBg(SLATE_FILL,10));
        c.setClickable(true);
        c.setFocusable(true);
        TextView h=title("›  "+heading,18);
        h.setTextColor(WARM);
        c.addView(h);
        c.addView(subtitle(detail));
        c.setOnClickListener(v->action.run());
        return c;
    }''',
    "maintenance navigation actions",
)

maintenance = replace_method(
    maintenance,
    "    private LinearLayout faqCard(String question,String answerText)",
    '''    private LinearLayout faqCard(String question,String answerText) {
        LinearLayout c=card();
        c.setPadding(dp(7),dp(7),dp(7),dp(7));
        TextView q=text("›  "+question,16,WARM,true);
        q.setPadding(dp(12),dp(12),dp(12),dp(12));
        q.setBackground(filledPanelBg(SLATE_FILL,9));
        if(EV_TABLE_QUESTION.equals(question)){
            LinearLayout a=evTableView();
            a.setVisibility(View.GONE);
            q.setOnClickListener(v->{ boolean open=a.getVisibility()==View.VISIBLE; a.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); });
            c.addView(q);
            c.addView(a);
            return c;
        }
        TextView a=text(answerText,14,Color.rgb(218,207,190),false);
        a.setLineSpacing(0f,1.12f);
        a.setPadding(dp(10),dp(12),dp(10),dp(10));
        a.setVisibility(View.GONE);
        q.setOnClickListener(v->{ boolean open=a.getVisibility()==View.VISIBLE; a.setVisibility(open?View.GONE:View.VISIBLE); q.setText((open?"›  ":"⌄  ")+question); });
        c.addView(q);
        c.addView(a);
        return c;
    }''',
    "maintenance FAQ hierarchy",
)

maintenance = replace_method(
    maintenance,
    "    private TextView evCell(String value,int widthDp,int heightDp,boolean header,boolean alternate)",
    '''    private TextView evCell(String value,int widthDp,int heightDp,boolean header,boolean alternate) {
        TextView cell=text(value,12,header?IVORY:WARM,header);
        cell.setGravity(Gravity.CENTER);
        cell.setPadding(dp(4),0,dp(4),0);
        GradientDrawable bg=new GradientDrawable();
        bg.setColor(header?SLATE_FILL:(alternate?Color.rgb(31,34,37):Color.rgb(22,24,26)));
        bg.setStroke(dp(1),SLATE_BORDER);
        cell.setBackground(bg);
        cell.setLayoutParams(new LinearLayout.LayoutParams(dp(widthDp),dp(heightDp)));
        return cell;
    }''',
    "maintenance EV table",
)

maintenance = replace_method(
    maintenance,
    "    private LinearLayout card()",
    '''    private LinearLayout card() {
        LinearLayout c=new LinearLayout(this);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setPadding(dp(15),dp(13),dp(15),dp(13));
        c.setBackground(outlinedPanelBg());
        c.setElevation(dp(1));
        c.setLayoutParams(margin(-1,-2,0,0,0,dp(10)));
        return c;
    }''',
    "maintenance information cards",
)
maintenance = rep(
    maintenance,
    "    private LinearLayout card() {\n",
    '''    private GradientDrawable outlinedPanelBg() {
        GradientDrawable bg=new GradientDrawable();
        bg.setColor(BG);
        bg.setCornerRadius(dp(10));
        bg.setStroke(dp(1),SLATE_BORDER);
        return bg;
    }

    private GradientDrawable filledPanelBg(int color,int radiusDp) {
        GradientDrawable bg=new GradientDrawable();
        bg.setColor(color);
        bg.setCornerRadius(dp(radiusDp));
        return bg;
    }

    private LinearLayout card() {
''',
    "maintenance panel helpers",
)
maintenance = replace_method(
    maintenance,
    "    private void notice(String value)",
    '''    private void notice(String value) {
        TextView v=text(value,13,MUTED,false);
        v.setBackground(outlinedPanelBg());
        v.setPadding(dp(12),dp(10),dp(12),dp(10));
        body.addView(v,margin(-1,-2,0,dp(2),0,dp(10)));
    }''',
    "maintenance notices",
)
maintenance = replace_method(
    maintenance,
    "    private TextView linkButton(String label,String url)",
    '''    private TextView linkButton(String label,String url) {
        TextView v=actionText(label);
        v.setGravity(Gravity.CENTER);
        v.setTextColor(WARM);
        v.setBackground(filledPanelBg(SLATE_ACTION,9));
        v.setOnClickListener(view->openUrl(url));
        v.setLayoutParams(margin(-1,dp(48),0,dp(8),0,dp(12)));
        return v;
    }''',
    "maintenance link actions",
)
maintenance = replace_method(
    maintenance,
    "    private TextView actionText(String label)",
    '''    private TextView actionText(String label) {
        TextView v=text(label,13,IVORY,true);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setPadding(dp(12),0,dp(12),0);
        return v;
    }''',
    "maintenance action text",
)

new_content_start = maintenance.index("    private static final String EV_TABLE_QUESTION")
new_content_end = maintenance.index("    @Override protected void onCreate")
if maintenance_reference_before != maintenance[new_content_start:new_content_end]:
    raise SystemExit("v0.6.6 maintenance reference content changed")
maintenance_after = {s: java_method(maintenance, s) for s in maintenance_protected}
for signature in maintenance_protected:
    if maintenance_before[signature] != maintenance_after[signature]:
        raise SystemExit(f"v0.6.6 protected maintenance behaviour changed: {signature}")
if maintenance.count("q.setOnClickListener") != 2:
    raise SystemExit("v0.6.6 FAQ toggle callbacks changed")
if maintenance.count("v.setOnClickListener(view->openUrl(url));") != 1:
    raise SystemExit("v0.6.6 external-link callback changed")


ASSISTANT.write_text(assistant, encoding="utf-8")
LARGE_FORMAT.write_text(large, encoding="utf-8")
MAINTENANCE.write_text(maintenance, encoding="utf-8")

print("remaining_graphics_066=APPLIED")
print("paper_baths=GREEN")
print("large_format=VIOLET")
print("use_maintenance=SLATE")
print("clickable_actions=FILLED")
print("static_information=OUTLINED")
print("paper_calculation_changes=ZERO")
print("large_format_data_changes=ZERO")
print("maintenance_reference_changes=ZERO")
print("timer_process_changes=ZERO")
