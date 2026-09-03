#!/usr/bin/env python3
"""Darkroom 0.6.5: coherent film-development workflow, visuals only."""

from pathlib import Path


ASSISTANT = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")


def rep(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)
    if found != count:
        raise SystemExit(f"v0.6.5 {label}: expected {count}, found {found}")
    return text.replace(old, new)


def between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    start_count = text.count(start)
    end_count = text.count(end)
    if start_count != 1 or end_count < 1:
        raise SystemExit(
            f"v0.6.5 {label}: start={start_count}, end={end_count}"
        )
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[:i] + replacement + text[j:]


def java_method(text: str, signature: str) -> str:
    start = text.find(signature)
    if start < 0:
        raise SystemExit(f"v0.6.5 protected method missing: {signature}")
    opening = text.find("{", start)
    if opening < 0:
        raise SystemExit(f"v0.6.5 protected method has no body: {signature}")
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
    raise SystemExit(f"v0.6.5 unterminated method: {signature}")


assistant = ASSISTANT.read_text(encoding="utf-8")

if "FILM_VISUAL_065" in assistant:
    print("film_development_065=ALREADY_APPLIED")
    raise SystemExit(0)
if "INVENTORY_VISUAL_064" not in assistant:
    raise SystemExit("v0.6.5: exact v0.6.4 Assistant source not recognized")

# These methods implement selection, calculation, capacity, persistence and
# inventory accounting. They must remain byte-for-byte identical.
protected_signatures = [
    "    private void refreshFilmDilutions()",
    "    private void finishOnlineFilmSelection(OnlineCatalogSearch.FilmData fd)",
    "    private void selectFilm(FilmStock f)",
    "    private void updateCompatibleTanks()",
    "    private double filmCapacityUnits(int count, String format)",
    "    private double chemicalMinimumForLoad(",
    "    private void calculateFilmOnline()",
    "    private void showFilmCalculationFailure(Throwable error)",
    "    private void showDevelopmentResultSafely(DevTimeEngine.Result result,",
    "    private void renderFilmCapacityForFormat(Product dev, Product stop, Product fix,",
    "    private void renderFilmCapacity(Product dev, Product stop, Product fix, double volumeMl)",
    "    private void registerFilmUse(Product p, double volumeMl, double units)",
    "    private void resetFilmBath(Product p, double volumeMl)",
    "    private void saveCurrentUiState()",
    "    private void restoreFilmUiState()",
    "    private void restoreSavedFilmDilution(int attempt)",
]
protected_before = {
    signature: java_method(assistant, signature) for signature in protected_signatures
}

assistant = rep(
    assistant,
    "    // INVENTORY_VISUAL_064 — chemical-family UI only; inventory behaviour unchanged.\n",
    "    // INVENTORY_VISUAL_064 — chemical-family UI only; inventory behaviour unchanged.\n"
    "    // FILM_VISUAL_065 — film-development hierarchy only; process and calculations unchanged.\n",
    "film marker",
)
assistant = rep(
    assistant,
    "    private static final int NEUTRAL_ACTION = Color.rgb(58, 62, 66);\n",
    "    private static final int NEUTRAL_ACTION = Color.rgb(58, 62, 66);\n"
    "    private static final int IVORY = Color.rgb(235, 210, 174);\n"
    "    private static final int FILM_FILL = Color.rgb(43, 91, 106);\n"
    "    private static final int FILM_ACTION = Color.rgb(55, 126, 148);\n"
    "    private static final int FILM_ACCENT = Color.rgb(82, 164, 188);\n"
    "    private static final int FILM_BORDER = Color.rgb(66, 139, 161);\n"
    "    private static final int FILM_SECONDARY = Color.rgb(50, 65, 71);\n",
    "film palette",
)

show_film_start = '''    private void showFilm() {
        currentScreen = FILM;
        selectedFilm = null;
        selectedFilmDeveloper = null;
        selectedStop = null;
        selectedFix = null;
        lastFilmTank = null;

        LinearLayout page = page("Sviluppo pellicola",
                "Pellicola, chimica, tank e tempo JOBO CPE2.");

        LinearLayout filmSection = filmSection(
                "1 · PELLICOLA E FORMATO",
                "Ricerca, formato, sensibilità esposta e quantità");
        filmField = new AutoCompleteTextView(this);
        filmField.setThreshold(3);
        filmField.setHint("Scrivi almeno 3 lettere…");
        styleInput(filmField);
        List<String> suggestions = new ArrayList<>();
        ArrayAdapter<String> filmAdapter = new ArrayAdapter<>(this,
                android.R.layout.simple_dropdown_item_1line, suggestions);
        filmField.setAdapter(filmAdapter);
        Map<String, OnlineCatalogSearch.SearchResult> onlineFilms = new HashMap<>();
        filmSection.addView(fieldBlock("PELLICOLA", filmField));
        filmSearchStatus = label(
                "Cerca nel database offline dopo 3 lettere.", 12, MUTED, false);
        styleFilmInformation(filmSearchStatus);
        filmSection.addView(filmSearchStatus);
        filmSection.addView(space(9));
        filmSuggestionsBox = new LinearLayout(this);
        filmSuggestionsBox.setOrientation(LinearLayout.VERTICAL);
        filmSection.addView(filmSuggestionsBox);

        formatSpinner = spinner(new String[]{"Seleziona prima la pellicola"});
        filmSection.addView(fieldBlock("FORMATO", formatSpinner));
        isoField = edit("", InputType.TYPE_CLASS_NUMBER);
        isoField.setHint("ISO nominale");
        filmSection.addView(fieldBlock("ISO ESPOSTO", isoField));
        rollsSpinner = spinner(new String[]{"1", "2", "3", "4", "5"});
        LinearLayout filmCountBlock = fieldBlock("NUMERO RULLI", rollsSpinner);
        filmCountLabel = (TextView) filmCountBlock.getChildAt(0);
        filmSection.addView(filmCountBlock);
        page.addView(filmSection);
        page.addView(space(11));

        LinearLayout processSection = filmSection(
                "2 · SVILUPPO JOBO",
                "Tank, rivelatore, diluizione e temperatura");
        tankSpinner = spinner(new String[]{"Seleziona prima la pellicola"});
        processSection.addView(fieldBlock("TANK JOBO", tankSpinner));

        List<Product> developers = inventoryProductsByRole(ROLE_FILM_DEV);
        developerSpinner = productSpinner(developers, "Nessun rivelatore in magazzino");
        processSection.addView(fieldBlock("RIVELATORE", developerSpinner));
        dilutionSpinner = spinner(new String[]{"—"});
        processSection.addView(fieldBlock("DILUIZIONE", dilutionSpinner));

        temperatureField = edit("20", InputType.TYPE_CLASS_NUMBER |
                InputType.TYPE_NUMBER_FLAG_DECIMAL);
        processSection.addView(fieldBlock("TEMPERATURA °C", temperatureField));
        page.addView(processSection);
        page.addView(space(11));

        LinearLayout auxiliarySection = filmSection(
                "3 · BAGNI AUSILIARI",
                "Arresto e fissaggio scelti dal magazzino");
        List<Product> stops = inventoryProductsByRole(ROLE_STOP);
        stopSpinner = productSpinner(stops, "Nessun arresto in magazzino");
        auxiliarySection.addView(fieldBlock("ARRESTO", stopSpinner));
        List<Product> fixes = inventoryProductsByRole(ROLE_FIX);
        fixSpinner = productSpinner(fixes, "Nessun fissaggio in magazzino");
        auxiliarySection.addView(fieldBlock("FISSAGGIO", fixSpinner));
        page.addView(auxiliarySection);
        page.addView(space(12));

'''
assistant = between(
    assistant,
    "    private void showFilm() {",
    "        developerSpinner.setOnItemSelectedListener",
    show_film_start,
    "ordered film form",
)
assistant = rep(
    assistant,
    '''        Button calc = actionButton("CALCOLA", BURGUNDY);
        calc.setOnClickListener(v -> {
            try {
                calculateFilmOnline();
''',
    '''        Button calc = filmButton("CALCOLA", FILM_ACTION);
        calc.setOnClickListener(v -> {
            try {
                calculateFilmOnline();
''',
    "film calculate action",
)

assistant = rep(
    assistant,
    "        summary.setBackground(bg(CARD, 13, BORDER, 1));\n"
    "        summary.addView(label(\"RISULTATO SVILUPPO\", 15, WHITE, true));\n"
    "        addUnifiedChemicalField(summary, \"TEMPO JOBO CPE2\",\n"
    "                result != null && result.found ? result.finalDisplay() : \"Tempo non disponibile\");\n",
    "        summary.setBackground(bg(BG, 13, FILM_BORDER, 1));\n"
    "        summary.addView(label(\"RISULTATO SVILUPPO\", 16, FILM_ACCENT, true));\n"
    "        addFilmTimeField(summary, \"TEMPO JOBO CPE2\",\n"
    "                result != null && result.found ? result.finalDisplay() : \"Tempo non disponibile\");\n",
    "development summary",
)
assistant = rep(
    assistant,
    "        preparation.setBackground(bg(CARD, 13, BORDER, 1));\n"
    "        preparation.addView(label(\"PREPARAZIONE BAGNI\", 15, WHITE, true));\n",
    "        preparation.setBackground(bg(BG, 13, FILM_BORDER, 1));\n"
    "        preparation.addView(label(\"PREPARAZIONE BAGNI\", 16, FILM_ACCENT, true));\n",
    "bath preparation information",
)
assistant = rep(
    assistant,
    '                Button openMinimumSource = smallButton("APRI FONTE VOLUME");\n',
    '                Button openMinimumSource = filmButton("APRI FONTE VOLUME", FILM_FILL);\n',
    "source action",
)
assistant = rep(
    assistant,
    '        Button register = actionButton("REGISTRA QUESTO SVILUPPO", BURGUNDY);\n',
    '        Button register = filmButton("REGISTRA QUESTO SVILUPPO", FILM_ACTION);\n',
    "register action",
)
assistant = rep(
    assistant,
    '''        Button fresh = smallButton("NUOVO BAGNO / AZZERA CONTATORE");
        fresh.setOnClickListener(v -> {
            resetFilmBath(dev, workingVolumeMl);
''',
    '''        Button fresh = filmButton("NUOVO BAGNO / AZZERA CONTATORE", FILM_SECONDARY);
        fresh.setOnClickListener(v -> {
            resetFilmBath(dev, workingVolumeMl);
''',
    "fresh-bath action",
)

assistant = rep(
    assistant,
    '''    private void addUnifiedChemicalField(LinearLayout parent, String title, String value) {
        if (value == null || value.trim().isEmpty()) return;
        TextView heading = label(title, 11, MUTED, true);
        heading.setPadding(0, dp(8), 0, dp(3));
        parent.addView(heading);
        parent.addView(label(value.trim(), 15, WHITE, false));
    }
''',
    '''    private void addUnifiedChemicalField(LinearLayout parent, String title, String value) {
        if (value == null || value.trim().isEmpty()) return;
        TextView heading = label(title, 11, FILM_ACCENT, true);
        heading.setPadding(0, dp(9), 0, dp(3));
        parent.addView(heading);
        TextView content = label(value.trim(), 15, WHITE, false);
        content.setLineSpacing(0f, 1.12f);
        parent.addView(content);
    }
''',
    "film information fields",
)

film_accordion = '''    private void addFilmAccordion(LinearLayout parent, String title,
                                  String compactSummary, LinearLayout body) {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setBackground(bg(BG, 13, FILM_BORDER, 1));
        TextView header = label("▸ " + title + "\\n" + compactSummary, 14, WHITE, true);
        header.setPadding(dp(16), dp(13), dp(16), dp(13));
        header.setBackground(bg(FILM_FILL, 12, 0, 0));
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

'''
assistant = between(
    assistant,
    "    private void addFilmAccordion(LinearLayout parent, String title,",
    "    private String filmReuseCompactSummary(",
    film_accordion,
    "filled film accordions",
)

page_method = '''    private LinearLayout page(String title, String subtitle) {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(16), dp(14), dp(16), dp(28));
        page.setBackgroundColor(BG);
        boolean chemicalPage = "Prodotti chimici".equalsIgnoreCase(title);
        boolean filmPage = "Sviluppo pellicola".equalsIgnoreCase(title);

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);

        TextView home = label("⌂", 25, filmPage ? IVORY : WHITE, true);
        home.setGravity(Gravity.CENTER);
        home.setContentDescription("Torna alla Home");
        home.setOnClickListener(v -> {
            saveCurrentUiState();
            finish();
        });
        top.addView(home, new LinearLayout.LayoutParams(dp(46), dp(46)));

        TextView h = label(title.toUpperCase(Locale.ITALY), filmPage ? 23 : 24,
                filmPage ? IVORY : WHITE, true);
        h.setGravity(Gravity.CENTER);
        if (chemicalPage || filmPage)
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
                : filmPage ? FILM_ACCENT : BURGUNDY_BRIGHT;
        accent.setBackground(bg(accentColor, 2, 0, 0));
        page.addView(accent);
        return page;
    }

'''
assistant = between(
    assistant,
    "    private LinearLayout page(String title, String subtitle) {",
    "    private View homeCard(",
    page_method,
    "film page header",
)

film_helpers = '''    private LinearLayout filmSection(String title, String detail) {
        LinearLayout section = new LinearLayout(this);
        section.setOrientation(LinearLayout.VERTICAL);
        section.setPadding(dp(14), dp(13), dp(14), dp(4));
        section.setBackground(bg(BG, 13, FILM_BORDER, 1));
        TextView heading = label(title, 15, FILM_ACCENT, true);
        section.addView(heading);
        TextView subtitle = label(detail, 12, MUTED, false);
        subtitle.setPadding(0, dp(3), 0, dp(13));
        section.addView(subtitle);
        return section;
    }

    private void styleFilmInformation(TextView view) {
        view.setPadding(dp(12), dp(9), dp(12), dp(9));
        view.setTextColor(MUTED);
        view.setBackground(bg(BG, 9, FILM_BORDER, 1));
    }

    private Button filmButton(String text, int fill) {
        Button button = actionButton(text, fill);
        button.setTextColor(WHITE);
        button.setAllCaps(false);
        button.setBackground(bg(fill, 10, 0, 0));
        return button;
    }

    private void addFilmTimeField(LinearLayout parent, String title, String value) {
        TextView heading = label(title, 11, FILM_ACCENT, true);
        heading.setPadding(0, dp(12), 0, dp(3));
        parent.addView(heading);
        TextView time = label(value == null ? "—" : value.trim(), 27, FILM_ACCENT, true);
        time.setPadding(0, 0, 0, dp(3));
        parent.addView(time);
    }

'''
assistant = rep(
    assistant,
    "    private LinearLayout fieldBlock(String labelText, View field) {\n",
    film_helpers + "    private LinearLayout fieldBlock(String labelText, View field) {\n",
    "film UI helpers",
)

assistant = rep(
    assistant,
    "        TextView l = label(labelText, 12, MUTED, true);\n"
    "        l.setPadding(dp(4), 0, 0, dp(6));\n",
    "        int fieldLabelColor = currentScreen == FILM ? FILM_ACCENT : MUTED;\n"
    "        TextView l = label(labelText, 12, fieldLabelColor, true);\n"
    "        l.setPadding(dp(4), 0, 0, dp(6));\n",
    "film field labels",
)
assistant = rep(
    assistant,
    "        v.setBackground(bg(CARD, 10, BORDER, 1));\n"
    "        v.setMinHeight(dp(50));\n",
    "        int inputBorder = currentScreen == FILM ? FILM_BORDER : BORDER;\n"
    "        v.setBackground(bg(CARD, 10, inputBorder, 1));\n"
    "        v.setMinHeight(dp(50));\n",
    "film text inputs",
)
assistant = rep(
    assistant,
    "        s.setBackground(bg(CARD, 13, BORDER, 1));\n"
    "        s.setMinimumHeight(dp(52));\n",
    "        int spinnerBorder = currentScreen == FILM ? FILM_BORDER : BORDER;\n"
    "        s.setBackground(bg(CARD, 13, spinnerBorder, 1));\n"
    "        s.setMinimumHeight(dp(52));\n",
    "film selectors",
)
assistant = rep(
    assistant,
    "        v.setBackground(bg(CARD, 10, BORDER, 1));\n"
    "        return v;\n"
    "    }\n\n"
    "    private void resultLine",
    "        int rowFill = currentScreen == FILM ? FILM_FILL : CARD;\n"
    "        int rowBorder = currentScreen == FILM ? FILM_BORDER : BORDER;\n"
    "        v.setBackground(bg(rowFill, 10, rowBorder, 1));\n"
    "        return v;\n"
    "    }\n\n"
    "    private void resultLine",
    "filled film search results",
)
assistant = rep(
    assistant,
    '''        r.setPadding(dp(15), dp(12), dp(15), dp(12));
        r.setBackground(bg(CARD, 10, BORDER, 1));
        r.addView(label(labelText, 11, MUTED, false));
        r.addView(space(4));
        r.addView(label(value, 17, WHITE, true));
''',
    '''        r.setPadding(dp(15), dp(12), dp(15), dp(12));
        boolean filmInformation = currentScreen == FILM;
        r.setBackground(bg(filmInformation ? BG : CARD, 10,
                filmInformation ? FILM_BORDER : BORDER, 1));
        r.addView(label(labelText, 11,
                filmInformation ? FILM_ACCENT : MUTED, filmInformation));
        r.addView(space(4));
        r.addView(label(value, 17, WHITE, true));
''',
    "outlined film information",
)

protected_after = {
    signature: java_method(assistant, signature) for signature in protected_signatures
}
for signature in protected_signatures:
    if protected_before[signature] != protected_after[signature]:
        raise SystemExit(f"v0.6.5 protected logic changed: {signature}")

# Preserve the exact operational callbacks that live inside the two UI methods
# intentionally restyled above.
required_callbacks = [
    "selectedFilmDeveloper = productAt(developers, position);",
    "selectedStop = productAt(stops, position);",
    "selectedFix = productAt(fixes, position);",
    "calculateFilmOnline();",
    "registerFilmUse(dev, workingVolumeMl, units);",
    "registerFilmUse(stop, workingVolumeMl, units);",
    "registerFilmUse(fix, workingVolumeMl, units);",
    "resetFilmBath(dev, workingVolumeMl);",
    "resetFilmBath(stop, workingVolumeMl);",
    "resetFilmBath(fix, workingVolumeMl);",
]
for callback in required_callbacks:
    if assistant.count(callback) != 1:
        raise SystemExit(f"v0.6.5 callback integrity failure: {callback}")

ASSISTANT.write_text(assistant, encoding="utf-8")

print("film_development_065=APPLIED")
print("film_family=BLUE_TEAL")
print("film_sections=FILM_JOBO_AUXILIARY")
print("film_actions=FILLED")
print("film_information=OUTLINED")
print("film_result_time=DOMINANT")
print("film_process_changes=ZERO")
