#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOT = Path("combined/src/main/java/it/darkroom/timer")
MAIN = ROOT / "MainActivity.java"
JPEG = ROOT / "JpegCardRenderer.java"
ENL = ROOT / "EnlargementActivity.java"

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)

def replace_between(text, start_marker, end_marker, replacement, label):
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"{label}: start marker not found")
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f"{label}: end marker not found")
    return text[:start] + replacement + text[end:]

def method_block(text, signature):
    start = text.find(signature)
    if start < 0:
        raise SystemExit(f"method guard missing: {signature}")
    brace = text.find("{", start)
    if brace < 0:
        raise SystemExit(f"method guard brace missing: {signature}")
    depth = 0
    for i in range(brace, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    raise SystemExit(f"method guard unterminated: {signature}")

def volume_fingerprint(text):
    keys = (
        "VOLUME_", "VOL+", "VOL-", "KEYCODE_VOLUME", "dispatchKeyEvent",
        "toggleFocusFromVolume", "screenOffFocusBridgeRequested",
        "ACTION_ENABLE_SCREEN_OFF_FOCUS", "ACTION_DISABLE_SCREEN_OFF_FOCUS",
    )
    lines = [line for line in text.splitlines() if any(k in line for k in keys)]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()

main = MAIN.read_text(encoding="utf-8")
jpeg = JPEG.read_text(encoding="utf-8")
enl = ENL.read_text(encoding="utf-8")

volume_before = volume_fingerprint(main)
math_before = {
    "calc": hashlib.sha256(method_block(enl, "    Calc calc(").encode("utf-8")).hexdigest(),
    "buildMeta": hashlib.sha256(method_block(enl, "    String buildMeta(").encode("utf-8")).hexdigest(),
    "lensMm": hashlib.sha256(method_block(enl, "    static int lensMm(").encode("utf-8")).hexdigest(),
}

# 1) UI: direct BASE toggle instead of the seconds-pattern popup.
main = replace_once(
    main,
    "import android.widget.ScrollView;\nimport android.widget.TextView;",
    "import android.widget.ScrollView;\nimport android.widget.Switch;\nimport android.widget.TextView;",
    "Switch import",
)
main = replace_once(main, 'private static final String APP_VERSION = "0.13.24";',
                    'private static final String APP_VERSION = "0.13.25";', "internal app version")
main = replace_once(main, "    private Button testSecondsPatternButton;",
                    "    private Switch testBaseToggle;", "base toggle field")

# 2) Contact-sheet preset: lens becomes an explicit per-preset choice.
contact_start = "    private static final class Contact35Preset {"
contact_end = "    private TextView deviceStatus;"
contact_class = '''    private static final class Contact35Preset {
        final long id;
        final String film;
        final int iso;
        final int milliseconds;
        final String lens;
        final String column;
        final String aperture;
        final String contrast;

        Contact35Preset(long id, String film, int iso, int milliseconds,
                        String lens, String column, String aperture, String contrast) {
            this.id = id;
            this.film = film == null ? "" : film.trim();
            this.iso = iso;
            this.milliseconds = milliseconds;
            String l = lens == null ? "" : lens.trim();
            String c = column == null ? "" : column.trim();
            String a = aperture == null ? "" : aperture.trim();
            this.lens = l.isEmpty() ? "50" : l.replaceFirst("(?i)\\\\s*mm$", "").trim();
            this.column = c.isEmpty() ? "57" : c.replaceFirst("(?i)^H\\\\s*", "");
            this.aperture = a.isEmpty() ? "8" : a.replaceFirst("(?i)^f/?\\\\s*", "");
            this.contrast = contrast == null || contrast.trim().isEmpty() ? "Y0 / M10" : contrast.trim();
        }

        String title() { return film + " · ISO " + iso; }
        String setupLine() {
            return "24×30 · " + lens + " mm · H" + column + " · f/" + aperture + " · " + contrast;
        }
    }

'''
main = replace_between(main, contact_start, contact_end, contact_class, "contact preset class")

# Extra fields for the enlargement verification state.
main = replace_once(
    main,
    "    private TextView contact35SelectedSetup;\n    private TextView printSequenceSummary;",
    "    private TextView contact35SelectedSetup;\n"
    "    private Button setEnlargementButton;\n"
    "    private TextView enlargementVerificationText;\n"
    "    private TextView printSequenceSummary;",
    "enlargement verification fields",
)

# Direct BASE switch row.
old_pattern_ui = '''        testSecondsPatternButton = compactButton(testSecondsPatternButtonLabel());
        testSecondsPatternButton.setOnClickListener(v -> showTestSecondsPatternDialog());
        exposure.addView(testSecondsPatternButton, margin(lp(-1, dp(50)), 0, 8, 0, 0));
'''
new_pattern_ui = '''        LinearLayout testBaseToggleRow = new LinearLayout(this);
        testBaseToggleRow.setOrientation(LinearLayout.HORIZONTAL);
        testBaseToggleRow.setGravity(Gravity.CENTER_VERTICAL);
        testBaseToggleRow.setPadding(dp(14), 0, dp(12), 0);
        testBaseToggleRow.setBackground(roundRect(BUTTON, 9, 1, BORDER));
        TextView testBaseToggleLabel = text("BASE", 14, TEXT_PRIMARY, true);
        testBaseToggleRow.addView(testBaseToggleLabel, lp(0, dp(50), 1f));
        testBaseToggle = new Switch(this);
        testBaseToggle.setShowText(true);
        testBaseToggle.setTextOn("ON");
        testBaseToggle.setTextOff("OFF");
        testBaseToggle.setTextColor(PROVINO_ACCENT);
        testBaseToggle.setChecked(isBaseStepSeconds());
        testBaseToggle.setOnCheckedChangeListener((buttonView, checked) -> setTestBaseStepEnabled(checked));
        testBaseToggleRow.addView(testBaseToggle, lp(-2, dp(50)));
        exposure.addView(testBaseToggleRow, margin(lp(-1, dp(50)), 0, 8, 0, 0));
'''
main = replace_once(main, old_pattern_ui, new_pattern_ui, "direct base toggle UI")

pattern_start = "    private String testSecondsPatternButtonLabel()"
pattern_end = "    private String testStripMethodButtonLabel()"
pattern_methods = '''    private String currentTestStepLabel() {
        if (isBaseStepSeconds()) {
            return "BASE " + formatTime(testBaseMs) + " + PASSO " + formatTime(testWidthMs);
        }
        return TimingMath.stepLabel(timingMethod);
    }

    private void refreshTestSecondsPatternUi() {
        boolean secondsSingle = provinoFlow == PROVINO_SINGLE && !TimingMath.isFStop(timingMethod);
        if (testBaseToggle != null) {
            testBaseToggle.setVisibility(secondsSingle ? View.VISIBLE : View.GONE);
            boolean desired = isBaseStepSeconds();
            if (testBaseToggle.isChecked() != desired) testBaseToggle.setChecked(desired);
        }
        if (testBaseTimeRow != null) testBaseTimeRow.setVisibility(isBaseStepSeconds() ? View.VISIBLE : View.GONE);
        if (testBaseTimeText != null) testBaseTimeText.setText("BASE " + formatTime(testBaseMs));
    }

    private void setTestBaseStepEnabled(boolean enabled) {
        if (armed || provinoFlow != PROVINO_SINGLE || TimingMath.isFStop(timingMethod)) {
            refreshTestSecondsPatternUi();
            return;
        }
        testSecondsPattern = enabled ? TEST_SECONDS_BASE_STEP : TEST_SECONDS_CUMULATIVE;
        if (enabled) {
            // BASE is one common exposure on the whole sheet, followed by equal
            // added exposures while progressively covering the strip.
            testStripMethod = TimingMath.MASK_COVER;
            if (testBaseMs <= 0) testBaseMs = 7000;
            if (testWidthMs > 5000) testWidthMs = 1000;
        }
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putString("testSecondsPattern", testSecondsPattern)
                .putInt("testBaseMs", testBaseMs)
                .putInt("testWidthMs", testWidthMs)
                .putString("testStripMethod", testStripMethod)
                .apply();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        refreshTestStripMethodUi();
        updateTimingUi();
    }

'''
main = replace_between(main, pattern_start, pattern_end, pattern_methods, "base toggle methods")

# 3) Contact preset persistence/editor now stores the chosen lens.
main = replace_once(
    main,
    '                    String column = prefs.getString("column_" + id, "57");\n'
    '                    String aperture = prefs.getString("aperture_" + id, "8");',
    '                    String lens = prefs.getString("lens_" + id, "50");\n'
    '                    String column = prefs.getString("column_" + id, "57");\n'
    '                    String aperture = prefs.getString("aperture_" + id, "8");',
    "load contact lens",
)
main = replace_once(
    main,
    '                        out.add(new Contact35Preset(id, film, iso, snap(ms, 500, 36_000_000), column, aperture, contrast));',
    '                        out.add(new Contact35Preset(id, film, iso, snap(ms, 500, 36_000_000), lens, column, aperture, contrast));',
    "contact constructor load",
)
main = replace_once(
    main,
    '                .putInt("ms_" + preset.id, snap(preset.milliseconds, 500, 36_000_000))\n'
    '                .putString("column_" + preset.id, preset.column)',
    '                .putInt("ms_" + preset.id, snap(preset.milliseconds, 500, 36_000_000))\n'
    '                .putString("lens_" + preset.id, preset.lens)\n'
    '                .putString("column_" + preset.id, preset.column)',
    "persist contact lens",
)
main = replace_once(
    main,
    '                .remove("ms_" + id)\n'
    '                .remove("column_" + id)',
    '                .remove("ms_" + id)\n'
    '                .remove("lens_" + id)\n'
    '                .remove("column_" + id)',
    "delete contact lens",
)
main = replace_once(
    main,
    '        TextView fixed = text("Standard comuni: carta 24×30 · Rodagon 50 mm. Colonna, diaframma e contrasto sono precompilati ma modificabili per ogni preset.", 12, MUTED, false);',
    '        TextView fixed = text("Carta comune 24×30. Obiettivo, colonna, diaframma e contrasto sono salvati e modificabili per ogni preset.", 12, MUTED, false);',
    "contact editor intro",
)
main = replace_once(
    main,
    '        EditText iso = editField("es. 125", existing == null ? "" : String.valueOf(existing.iso));\n'
    '        EditText column = editField("predefinito 57", existing == null ? "57" : existing.column);',
    '        EditText iso = editField("es. 125", existing == null ? "" : String.valueOf(existing.iso));\n'
    '        EditText lens = editField("es. 50", existing == null ? "50" : existing.lens);\n'
    '        EditText column = editField("predefinito 57", existing == null ? "57" : existing.column);',
    "contact editor lens field",
)
main = replace_once(
    main,
    '        iso.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);\n'
    '        column.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);',
    '        iso.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);\n'
    '        lens.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);\n'
    '        column.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);',
    "contact lens input type",
)
main = replace_once(
    main,
    '        panel.addView(contactPresetField("ISO", iso), margin(lp(-1, -2), 0, 0, 0, 8));\n'
    '        panel.addView(contactPresetField("SCALA COLONNA LPL", column), margin(lp(-1, -2), 0, 0, 0, 8));',
    '        panel.addView(contactPresetField("ISO", iso), margin(lp(-1, -2), 0, 0, 0, 8));\n'
    '        panel.addView(contactPresetField("OBIETTIVO (mm)", lens), margin(lp(-1, -2), 0, 0, 0, 8));\n'
    '        panel.addView(contactPresetField("SCALA COLONNA LPL", column), margin(lp(-1, -2), 0, 0, 0, 8));',
    "contact lens editor row",
)
main = replace_once(
    main,
    '            String columnValue = column.getText().toString().trim();\n'
    '            String apertureValue = aperture.getText().toString().trim();',
    '            String lensValue = lens.getText().toString().trim();\n'
    '            String columnValue = column.getText().toString().trim();\n'
    '            String apertureValue = aperture.getText().toString().trim();',
    "contact lens save value",
)
main = replace_once(
    main,
    '                    || columnValue.isEmpty() || apertureValue.isEmpty() || contrastValue.isEmpty()) {',
    '                    || lensValue.isEmpty() || columnValue.isEmpty() || apertureValue.isEmpty() || contrastValue.isEmpty()) {',
    "contact lens validation",
)
main = replace_once(
    main,
    '            Contact35Preset saved = new Contact35Preset(id, filmName, isoValue, ms,\n'
    '                    columnValue, apertureValue, contrastValue);',
    '            Contact35Preset saved = new Contact35Preset(id, filmName, isoValue, ms,\n'
    '                    lensValue, columnValue, apertureValue, contrastValue);',
    "contact lens constructor save",
)
main = replace_once(
    main,
    '        TextView common = text("STANDARD COMUNE · 24×30 · Rodagon 50 mm", 12, MUTED, true);',
    '        TextView common = text("STANDARD COMUNE · carta 24×30", 12, MUTED, true);',
    "contact common setup",
)
main = replace_once(
    main,
    '        TextView variable = text("Colonna, diaframma e contrasto sono salvati nel preset", 11, MUTED, false);',
    '        TextView variable = text("Obiettivo, colonna, diaframma e contrasto sono salvati nel preset", 11, MUTED, false);',
    "contact variable setup",
)

# 4) Enlargement button: inherited data become explicitly unconfirmed after saving a log.
old_enlargement_button = '''        Button setEnlargement = functionalButton("IMPOSTA INGRANDIMENTO", ENLARGEMENT_ACCENT);
        setEnlargement.setOnClickListener(v -> startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup")));
        outer.addView(setEnlargement, margin(lp(-1, dp(46)), 0, 0, 0, 10));
'''
new_enlargement_button = '''        setEnlargementButton = functionalButton("IMPOSTA INGRANDIMENTO", ENLARGEMENT_ACCENT);
        setEnlargementButton.setOnClickListener(v -> handleEnlargementButton());
        outer.addView(setEnlargementButton, margin(lp(-1, dp(46)), 0, 0, 0, 4));
        enlargementVerificationText = text("Dati ereditati dal lavoro precedente: confermali o modificali.", 11, AMBER, true);
        enlargementVerificationText.setGravity(Gravity.CENTER);
        enlargementVerificationText.setPadding(dp(6), 0, dp(6), dp(7));
        outer.addView(enlargementVerificationText, lp(-1, -2));
        refreshEnlargementConfirmationUi();
'''
main = replace_once(main, old_enlargement_button, new_enlargement_button, "enlargement alert button")

# On resume, reflect changes made in EnlargementActivity and refresh the log when returning from a correction.
resume_anchor = '        new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 320L);\n'
resume_insert = resume_anchor + '        refreshEnlargementConfirmationUi();\n        if (mode == MODE_LOG) refreshLogList();\n'
main = replace_once(main, resume_anchor, resume_insert, "onResume enlargement refresh")

# Do not display beta in ordinary log summary; show only the LPL column value.
summary_start = "    private String enlargementLogSummary(String meta) {"
summary_end = "    private String splitLogSummary(LogEntry entry, PrintSequence savedSequence) {"
summary_method = '''    private String enlargementLogSummary(String meta) {
        if (meta == null || meta.trim().isEmpty()) return "—";
        String neg = enlargementMetaValue(meta, "neg");
        String paper = enlargementMetaValue(meta, "paper").replace('.', ',').replace("x", " × ");
        String lens = enlargementMetaValue(meta, "lens");
        String columnScale = enlargementMetaValue(meta, "columnScale");
        String carrier = enlargementMetaValue(meta, "carrier");
        String fill = enlargementMetaValue(meta, "fill");
        String mode = "0".equals(fill) ? "immagine intera" : ("1".equals(fill) ? "riempi larghezza" : ("2".equals(fill) ? "riempi altezza" : ""));
        String format = "35".equals(neg) ? "35 mm" : ("66".equals(neg) ? "6×6" : ("45".equals(neg) ? "4×5" : ""));
        String carrierLabel = "35mm".equals(carrier) ? "portanegativi 35 mm" : ("6x6".equals(carrier) ? "portanegativi 6×6" : ("4x5".equals(carrier) ? "portanegativi 4×5" : ""));
        StringBuilder b = new StringBuilder();
        if (!format.isEmpty()) b.append(format);
        if (!lens.isEmpty()) b.append(b.length() > 0 ? " · " : "").append("obiettivo ").append(lens).append(" mm");
        if (!carrierLabel.isEmpty()) b.append(b.length() > 0 ? " · " : "").append(carrierLabel);
        if (!paper.isEmpty()) b.append(b.length() > 0 ? " · " : "").append("carta ").append(paper).append(" cm");
        if (!columnScale.isEmpty()) {
            try { b.append(b.length() > 0 ? " · " : "").append("Colonna LPL: ").append(String.format(Locale.ITALY, "%.1f", Double.parseDouble(columnScale))); }
            catch (Exception ignored) {}
        }
        if (!mode.isEmpty()) b.append(b.length() > 0 ? " · " : "").append(mode);
        return b.length() == 0 ? "—" : b.toString();
    }

'''
main = replace_between(main, summary_start, summary_end, summary_method, "ordinary enlargement summary")

# Enlargement verification helper methods. They do not block exposure; they are an anti-forget state.
quick_save_anchor = '''    private boolean shouldOfferQuickSave() {
        SharedPreferences session = getSharedPreferences("log_session", MODE_PRIVATE);
        long cycle = session.getLong("lastCycleAt", 0L);
        long saved = getSharedPreferences("ui", MODE_PRIVATE).getLong("lastSavedCycleAt", 0L);
        return cycle > saved;
    }

'''
verification_methods = quick_save_anchor + '''    private boolean enlargementNeedsConfirmation() {
        return getSharedPreferences("ui", MODE_PRIVATE).getBoolean("enlargementNeedsConfirmation", false);
    }

    private void markEnlargementNeedsVerification() {
        getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("enlargementNeedsConfirmation", true).apply();
        refreshEnlargementConfirmationUi();
    }

    private void confirmCurrentEnlargement() {
        getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("enlargementNeedsConfirmation", false).apply();
        refreshEnlargementConfirmationUi();
        Toast.makeText(this, "Ingrandimento confermato per questa scheda", Toast.LENGTH_SHORT).show();
    }

    private void refreshEnlargementConfirmationUi() {
        if (setEnlargementButton == null) return;
        boolean needs = enlargementNeedsConfirmation();
        int accent = darkroomMode ? RED : (needs ? AMBER : ENLARGEMENT_ACCENT);
        setEnlargementButton.setText(needs ? "⚠  INGRANDIMENTO DA VERIFICARE" : "IMPOSTA INGRANDIMENTO");
        setEnlargementButton.setBackground(roundRect(accent, 10, 0, 0));
        setEnlargementButton.setTextColor(actionInk(accent));
        if (enlargementVerificationText != null) {
            enlargementVerificationText.setVisibility(needs ? View.VISIBLE : View.GONE);
            enlargementVerificationText.setTextColor(darkroomMode ? RED : AMBER);
        }
    }

    private void handleEnlargementButton() {
        if (!enlargementNeedsConfirmation()) {
            startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup"));
            return;
        }
        String meta = getSharedPreferences("ui", MODE_PRIVATE).getString("enlargementMeta", "");
        if (meta == null || meta.trim().isEmpty()) {
            startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup"));
            return;
        }
        String summary = enlargementLogSummary(meta);
        showAppChoiceDialog("INGRANDIMENTO DA VERIFICARE",
                new String[]{
                        "CONFERMA DATI ATTUALI\\n" + summary,
                        "MODIFICA INGRANDIMENTO"
                },
                which -> {
                    if (which == 0) confirmCurrentEnlargement();
                    else startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup"));
                }, "ANNULLA");
    }

'''
main = replace_once(main, quick_save_anchor, verification_methods, "enlargement verification helpers")

# Saving a new/current session ends that photograph and re-arms the alert for the next one.
save_mark_anchor = '''            LogStore.save(this, entry);
            markCurrentSessionSaved(entry);
            dialog.dismiss();
'''
save_mark_new = '''            LogStore.save(this, entry);
            markCurrentSessionSaved(entry);
            if (isNew) markEnlargementNeedsVerification();
            dialog.dismiss();
'''
main = replace_once(main, save_mark_anchor, save_mark_new, "alert after save log")

# Loading a saved print is an explicit enlargement choice, so treat it as confirmed.
main = replace_once(
    main,
    '                .putString("enlargementMeta", entry.enlargementMeta == null ? "" : entry.enlargementMeta)\n'
    '                .putLong("activeSourceLogId", entry.id)',
    '                .putString("enlargementMeta", entry.enlargementMeta == null ? "" : entry.enlargementMeta)\n'
    '                .putBoolean("enlargementNeedsConfirmation", false)\n'
    '                .putLong("activeSourceLogId", entry.id)',
    "reprint confirms enlargement",
)

# Existing log editor already edits manual fields; add an explicit correction path for the automatic enlargement data.
log_fields_anchor = '''        panel.addView(paper, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(notes, margin(lp(-1, dp(84)), 0, 0, 0, 12));

        Button save = compactButton("SALVA SCHEDA");
'''
log_fields_new = '''        panel.addView(paper, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(notes, margin(lp(-1, dp(84)), 0, 0, 0, 12));

        if (!isNew) {
            Button editEnlargement = functionalButton("CORREGGI INGRANDIMENTO DELLA SCHEDA", ENLARGEMENT_ACCENT);
            editEnlargement.setOnClickListener(v -> {
                entry.title = title.getText().toString().trim();
                entry.negative = negative[0];
                entry.aperture = aperture.getText().toString().trim();
                entry.columnHeight = "";
                entry.magenta = magenta.getText().toString().trim();
                entry.yellow = yellow.getText().toString().trim();
                entry.density = logDensityLabel(densityActive[0]);
                entry.paper = paper.getText().toString().trim();
                entry.notes = trimNotes(notes.getText().toString().trim());
                entry.favorite = favorite[0];
                LogStore.save(this, entry);
                dialog.dismiss();
                startActivity(new Intent(this, EnlargementActivity.class)
                        .putExtra("mode", "editlog")
                        .putExtra("originLogId", entry.id));
            });
            panel.addView(editEnlargement, margin(lp(-1, dp(50)), 0, 0, 0, 10));
        }

        Button save = compactButton("SALVA SCHEDA");
'''
main = replace_once(main, log_fields_anchor, log_fields_new, "edit logged enlargement")

# 5) Provino result dialog: the strips themselves scroll; header/actions remain fixed.
chooser_method = main.find("    private void showProvinoResultDialog(")
if chooser_method < 0:
    raise SystemExit("provino chooser method missing")
loop_start = main.find("        for (int i=0;i<physical.length;i++) {", chooser_method)
loop_end_marker = "\n\n        if (provinoFlow == PROVINO_SINGLE) {"
loop_end = main.find(loop_end_marker, loop_start)
if loop_start < 0 or loop_end < 0:
    raise SystemExit("provino chooser option loop anchors missing")
chooser_list = '''        ScrollView stripScroll = new ScrollView(this);
        stripScroll.setFillViewport(false);
        LinearLayout stripList = new LinearLayout(this);
        stripList.setOrientation(LinearLayout.VERTICAL);
        for (int i=0;i<physical.length;i++) {
            final int idx=i;
            Button option=compactButton((i+1)+"ª striscia   —   "+formatTime(physical[i])+("NESSUNO".equals(filterLabel)?"":" · "+filterLabel));
            option.setOnClickListener(v -> {
                selected[0]=idx;
                selectedText.setText("SELEZIONATA · "+(idx+1)+"ª · "+formatTime(physical[idx]));
            });
            stripList.addView(option, margin(lp(-1,dp(47)),0,0,0,6));
        }
        stripScroll.addView(stripList, new ScrollView.LayoutParams(-1, -2));
        panel.addView(stripScroll, lp(-1, 0, 1f));'''
main = main[:loop_start] + chooser_list + main[loop_end:]

# 6) Graphical log: no beta, column only, no app version in footer.
jpeg = replace_once(jpeg, '"Titolo", "Negativo", "Diaframma", "β / Scala LPL", "Magenta", "Yellow",',
                    '"Titolo", "Negativo", "Diaframma", "Colonna LPL", "Magenta", "Yellow",',
                    "jpg column label")
jpeg = replace_once(jpeg, "                enlargementBeta(e),", "                enlargementColumn(e),", "jpg column value call")
jpg_method_start = "    private static String enlargementBeta(LogEntry e) {"
jpg_method_end = "    private static String apertureLabel(String value) {"
jpg_column_method = '''    private static String enlargementColumn(LogEntry e) {
        String meta = e == null ? "" : e.enlargementMeta;
        if (meta == null || meta.trim().isEmpty()) return "—";
        String scale = "";
        for (String part : meta.split("\\\\|")) {
            if (part.startsWith("columnScale=")) scale = part.substring(12);
        }
        try { return String.format(Locale.ITALY, "%.1f", Double.parseDouble(scale)); }
        catch (Exception ignored) { return "—"; }
    }

'''
jpeg = replace_between(jpeg, jpg_method_start, jpg_method_end, jpg_column_method, "jpg column renderer")
jpeg = replace_once(jpeg,
                    '        String footer = "Darkroom Timer di F.G. - v" + (version == null ? "X.X.X" : version);',
                    '        String footer = "Darkroom Timer di F.G.";',
                    "jpg footer version removal")

# 7) EnlargementActivity gains a log-correction mode but its calibrated math methods are untouched.
render_anchor = '''    void renderMain() {
        boolean resize = "resize".equals(mode);
'''
render_new = '''    void renderMain() {
        if ("editlog".equals(mode)) {
            renderEditLog();
            return;
        }
        boolean resize = "resize".equals(mode);
'''
enl = replace_once(enl, render_anchor, render_new, "editlog mode dispatch")

cal_notice_marker = "    void addCalibrationNotice() {"
editlog_methods = '''    void renderEditLog() {
        begin("CORREGGI INGRANDIMENTO",
                "Aggiorna i dati automatici della scheda LOG senza modificare tempi, piano di stampa o calibrazione LPL.");
        addCalibrationNotice();
        if (originEntry == null) {
            info("Scheda LOG non trovata.");
            return;
        }
        String oldMeta = originEntry.enlargementMeta == null ? "" : originEntry.enlargementMeta;
        String format = negativeFromEntry(originEntry);
        if (format.isEmpty()) format = "35";
        neg = spinner(NEGATIVE_CHOICES);
        neg.setSelection(formatIndex(format));
        root.addView(label("NEGATIVO · OBIETTIVO AUTOMATICO", 12, MUTED, true));
        root.addView(neg, lp(-1, dp(50)));
        addPaperFields(oldMeta);
        fill = spinner(FILLS);
        fill.setSelection(Math.max(0, Math.min(2, intVal(oldMeta, "fill", 0))));
        root.addView(label("MODALITÀ", 12, MUTED, true));
        root.addView(fill, lp(-1, dp(50)));
        Button calc = button("CALCOLA CORREZIONE", ACCENT);
        calc.setOnClickListener(v -> calculateEditLog());
        root.addView(calc, margin(lp(-1, dp(52)), 0, dp(12), 0, dp(10)));
        resultBox = new LinearLayout(this);
        resultBox.setOrientation(LinearLayout.VERTICAL);
        root.addView(resultBox, lp(-1, -2));
    }

    void calculateEditLog() {
        try {
            clearResult();
            String format = NEGATIVE_CODES[neg.getSelectedItemPosition()];
            Dims d = readDims();
            Calc c = calc(format, d.W, d.H, fill.getSelectedItemPosition());
            String meta = buildMeta(format, d.W, d.H, fill.getSelectedItemPosition(), c.beta, c.pw, c.ph, c.crop, 0L, "");
            resultBox.addView(section("NUOVO INGRANDIMENTO", resultText(c, format)));
            Button save = button("SALVA CORREZIONE NEL LOG", ACCENT);
            save.setOnClickListener(v -> {
                originEntry.enlargementMeta = meta;
                syncCorrectedLogDisplayFields(originEntry, meta);
                LogStore.save(this, originEntry);
                Toast.makeText(this, "Ingrandimento corretto nella scheda LOG", Toast.LENGTH_SHORT).show();
                finish();
            });
            resultBox.addView(save, margin(lp(-1, dp(52)), 0, dp(10), 0, dp(4)));
        } catch (Exception e) {
            clearResult();
            infoInto(resultBox, "Inserisci dimensioni carta valide.");
        }
    }

    void syncCorrectedLogDisplayFields(LogEntry entry, String meta) {
        if (entry == null || meta == null || meta.trim().isEmpty()) return;
        String format = normalizeNegative(val(meta, "neg"));
        if (!format.isEmpty()) entry.negative = logNegative(format);
        entry.columnHeight = "";
        String paperValue = val(meta, "paper");
        if (!paperValue.isEmpty()) {
            String display = paperValue.replace('.', ',').replace("x", " × ") + " cm";
            String current = entry.paper == null ? "" : entry.paper.trim();
            String base = current.replaceFirst(
                    "(?i)\\\\s*·\\\\s*\\\\d+(?:[.,]\\\\d+)?\\\\s*[×x]\\\\s*\\\\d+(?:[.,]\\\\d+)?\\\\s*cm\\\\s*$", "").trim();
            if (base.isEmpty()) base = "Fomaspeed Variant 311 RC lucida";
            entry.paper = base + " · " + display;
        }
    }

'''
enl = replace_once(enl, cal_notice_marker, editlog_methods + cal_notice_marker, "editlog methods")

# Setting or deriving an enlargement explicitly confirms it for the current work.
enl = replace_once(
    enl,
    '                    .putInt("enlargementUiNeg", neg.getSelectedItemPosition())\n'
    '                    .putInt("enlargementUiFill", fill.getSelectedItemPosition()).apply();',
    '                    .putInt("enlargementUiNeg", neg.getSelectedItemPosition())\n'
    '                    .putInt("enlargementUiFill", fill.getSelectedItemPosition())\n'
    '                    .putBoolean("enlargementNeedsConfirmation", false).apply();',
    "setup confirms enlargement",
)
enl = replace_once(
    enl,
    '                .putInt("enlargementUiNeg", formatIndex(x.negativeCode))\n'
    '                .putString("testBaseFilterType", ExposureRecipe.normalizeFilter(x.newRecipe.filterType))',
    '                .putInt("enlargementUiNeg", formatIndex(x.negativeCode))\n'
    '                .putBoolean("enlargementNeedsConfirmation", false)\n'
    '                .putString("testBaseFilterType", ExposureRecipe.normalizeFilter(x.newRecipe.filterType))',
    "resize confirms enlargement",
)

# Guard the exact calibrated enlargement methods and every volume-key-related MainActivity line.
if volume_fingerprint(main) != volume_before:
    raise SystemExit("VOL+/VOL- guard failed: v0.7.12 touched volume/focus key logic")
math_after = {
    "calc": hashlib.sha256(method_block(enl, "    Calc calc(").encode("utf-8")).hexdigest(),
    "buildMeta": hashlib.sha256(method_block(enl, "    String buildMeta(").encode("utf-8")).hexdigest(),
    "lensMm": hashlib.sha256(method_block(enl, "    static int lensMm(").encode("utf-8")).hexdigest(),
}
if math_after != math_before:
    raise SystemExit("LPL calibration guard failed: calibrated enlargement math changed")

# Final source-level assertions.
assert 'APP_VERSION = "0.13.25"' in main
assert 'private Switch testBaseToggle;' in main
assert 'SERIE IN SECONDI · CUMULATIVA' not in main
assert 'showTestSecondsPatternDialog' not in main
assert 'putBoolean("enlargementNeedsConfirmation", true)' in main
assert 'CORREGGI INGRANDIMENTO DELLA SCHEDA' in main
assert 'ScrollView stripScroll' in main
assert 'contactPresetField("OBIETTIVO (mm)", lens)' in main
assert '.putString("lens_" + preset.id, preset.lens)' in main
assert 'Colonna LPL: ' in main
assert 'β / Scala LPL' not in jpeg
assert '"Colonna LPL"' in jpeg
assert 'String footer = "Darkroom Timer di F.G.";' in jpeg
assert '"editlog".equals(mode)' in enl
assert 'CALCOLA CORREZIONE' in enl

MAIN.write_text(main, encoding="utf-8")
JPEG.write_text(jpeg, encoding="utf-8")
ENL.write_text(enl, encoding="utf-8")

print("v0712_patch=PASS")
print("sonoff_vol_plus_minus_changes=ZERO")
print("lpl_calibrated_math_changes=ZERO")
print("log_jpg_version_removed=PASS")
print("log_beta_hidden=PASS")
print("log_column_label=Colonna_LPL")
print("log_enlargement_edit=PASS")
print("enlargement_post_log_alert=PASS")
print("test_strip_chooser_scroll=PASS")
print("contact_lens_selectable=PASS")
print("seconds_base_toggle=PASS")
