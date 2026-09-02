#!/usr/bin/env python3
from pathlib import Path

main = Path('combined/src/main/java/it/darkroom/timer/MainActivity.java')


def rd():
    return main.read_text(encoding='utf-8')


def wr(s):
    main.write_text(s, encoding='utf-8')


def rep(old, new, label, count=1):
    s = rd()
    n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.6.0 {label}: atteso >= {count}, trovato {n}')
    wr(s.replace(old, new, count))
    print('v0.6.0 OK', label, flush=True)


s = rd()
if 'APP_VERSION = "0.13.13"' in s and 'String setupLine()' in s and 'PROVINO A CONTATTO 35 mm' in s:
    print('v0.6.0 contact layout already applied', flush=True)
    raise SystemExit(0)
if 'APP_VERSION = "0.13.12"' not in s or 'private boolean contact35Mode = false;' not in s:
    raise SystemExit('v0.6.0: v0.5.9 contact-sheet baseline not recognized')

rep('    private static final String APP_VERSION = "0.13.12";\n',
    '    private static final String APP_VERSION = "0.13.13";\n',
    'Timer internal version')

# User-facing terminology: ISO only. Existing v0.5.9 preference keys are read as
# a one-time compatibility fallback, but never shown in the interface again.
s = rd()
class_start = s.find('    private static final class Contact35Preset {\n')
class_end = s.find('    private TextView deviceStatus;\n', class_start)
if class_start < 0 or class_end < 0:
    raise SystemExit('v0.6.0: Contact35Preset bounds missing')
new_class = r'''    private static final class Contact35Preset {
        final long id;
        final String film;
        final int iso;
        final int milliseconds;
        final String column;
        final String aperture;
        final String contrast;

        Contact35Preset(long id, String film, int iso, int milliseconds,
                        String column, String aperture, String contrast) {
            this.id = id;
            this.film = film == null ? "" : film.trim();
            this.iso = iso;
            this.milliseconds = milliseconds;
            String c = column == null ? "" : column.trim();
            String a = aperture == null ? "" : aperture.trim();
            this.column = c.isEmpty() ? "57" : c.replaceFirst("(?i)^H\\s*", "");
            this.aperture = a.isEmpty() ? "8" : a.replaceFirst("(?i)^f/?\\s*", "");
            this.contrast = contrast == null || contrast.trim().isEmpty() ? "Y0 / M10" : contrast.trim();
        }

        String title() { return film + " · ISO " + iso; }
        String setupLine() {
            return "24×30 · 50 mm · H" + column + " · f/" + aperture + " · " + contrast;
        }
    }

'''
wr(s[:class_start] + new_class + s[class_end:])
print('v0.6.0 OK Contact35Preset ISO + editable setup', flush=True)

rep('    private Button provinoPrintWorkspaceButton;\n', '', 'remove redundant workspace button field')
rep('    private TextView contact35SelectedTime;\n',
    '    private TextView contact35SelectedTime;\n    private TextView contact35SelectedSetup;\n',
    'selected setup field')

# Replace the whole contact-sheet helper/UI block produced by v0.5.9. This keeps
# the timing path unchanged while simplifying the hierarchy and expanding presets.
s = rd()
helpers_start = s.find('    private SharedPreferences contact35Preferences() {\n')
build_start = s.find('    private LinearLayout buildTestPanel() {\n', helpers_start)
build_end = s.find('    private LinearLayout buildLogPanel() {\n', build_start)
if helpers_start < 0 or build_start < 0 or build_end < 0:
    raise SystemExit('v0.6.0: contact helper/build bounds missing')

helpers = r'''    private SharedPreferences contact35Preferences() {
        return getSharedPreferences("contact35_presets", MODE_PRIVATE);
    }

    private ArrayList<Contact35Preset> loadContact35Presets() {
        SharedPreferences prefs = contact35Preferences();
        ArrayList<Contact35Preset> out = new ArrayList<>();
        String ids = prefs.getString("ids", "");
        if (ids != null && !ids.trim().isEmpty()) {
            for (String bit : ids.split(",")) {
                try {
                    long id = Long.parseLong(bit.trim());
                    String film = prefs.getString("film_" + id, "");
                    int iso = prefs.getInt("iso_" + id, prefs.getInt("ei_" + id, 0));
                    int ms = prefs.getInt("ms_" + id, 0);
                    String column = prefs.getString("column_" + id, "57");
                    String aperture = prefs.getString("aperture_" + id, "8");
                    String contrast = prefs.getString("contrast_" + id, "Y0 / M10");
                    if (film != null && !film.trim().isEmpty() && iso > 0 && ms >= 500)
                        out.add(new Contact35Preset(id, film, iso, snap(ms, 500, 36_000_000), column, aperture, contrast));
                } catch (Exception ignored) {}
            }
        }
        Collections.sort(out, (a, b) -> {
            int byFilm = a.film.compareToIgnoreCase(b.film);
            if (byFilm != 0) return byFilm;
            return Integer.compare(a.iso, b.iso);
        });
        return out;
    }

    private Contact35Preset findContact35Preset(long id) {
        if (id <= 0L) return null;
        for (Contact35Preset p : loadContact35Presets()) if (p.id == id) return p;
        return null;
    }

    private void persistContact35Preset(Contact35Preset preset) {
        if (preset == null || preset.id <= 0L || preset.film.trim().isEmpty()
                || preset.iso <= 0 || preset.milliseconds < 500) return;
        SharedPreferences prefs = contact35Preferences();
        String ids = prefs.getString("ids", "");
        boolean found = false;
        if (ids != null && !ids.trim().isEmpty()) {
            for (String bit : ids.split(",")) if (bit.trim().equals(String.valueOf(preset.id))) { found = true; break; }
        }
        String nextIds = ids == null ? "" : ids.trim();
        if (!found) nextIds = nextIds.isEmpty() ? String.valueOf(preset.id) : nextIds + "," + preset.id;
        prefs.edit()
                .putString("ids", nextIds)
                .putString("film_" + preset.id, preset.film.trim())
                .putInt("iso_" + preset.id, preset.iso)
                .remove("ei_" + preset.id)
                .putInt("ms_" + preset.id, snap(preset.milliseconds, 500, 36_000_000))
                .putString("column_" + preset.id, preset.column)
                .putString("aperture_" + preset.id, preset.aperture)
                .putString("contrast_" + preset.id, preset.contrast)
                .apply();
    }

    private void deleteContact35Preset(long id) {
        if (id <= 0L) return;
        SharedPreferences prefs = contact35Preferences();
        String ids = prefs.getString("ids", "");
        StringBuilder kept = new StringBuilder();
        if (ids != null && !ids.trim().isEmpty()) {
            for (String bit : ids.split(",")) {
                String value = bit.trim();
                if (value.isEmpty() || value.equals(String.valueOf(id))) continue;
                if (kept.length() > 0) kept.append(',');
                kept.append(value);
            }
        }
        prefs.edit()
                .putString("ids", kept.toString())
                .remove("film_" + id)
                .remove("iso_" + id)
                .remove("ei_" + id)
                .remove("ms_" + id)
                .remove("column_" + id)
                .remove("aperture_" + id)
                .remove("contrast_" + id)
                .apply();
        if (contact35SelectedId == id) {
            contact35SelectedId = -1L;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("contact35SelectedId", -1L).apply();
        }
        refreshContact35Ui();
        applyModeUi();
    }

    private void clearContact35CycleMarker() {
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .remove("contact35CycleActive")
                .remove("contact35CyclePresetId")
                .apply();
    }

    private void setContact35Mode(boolean enabled) {
        if (armed) return;
        if (enabled && provinoFlow != PROVINO_SINGLE) {
            Toast.makeText(this, "Torna al provino singolo o termina lo Split Grade prima del contatto", Toast.LENGTH_LONG).show();
            return;
        }
        contact35Mode = enabled;
        getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("contact35Mode", contact35Mode).apply();
        refreshContact35Ui();
        applyModeUi();
        if (contact35Mode) {
            Contact35Preset selected = findContact35Preset(contact35SelectedId);
            if (selected == null)
                setStatusPresentation("PROVINO A CONTATTO 35 mm", "Crea un nuovo preset oppure richiamane uno già salvato", BLUE);
            else
                setStatusPresentation("CONTATTO 35 mm — " + selected.title(), selected.setupLine(), BLUE);
        }
    }

    private void selectContact35Preset(Contact35Preset preset) {
        if (armed || preset == null) return;
        contact35SelectedId = preset.id;
        getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("contact35SelectedId", preset.id).apply();
        refreshContact35Ui();
        applyModeUi();
        setStatusPresentation("CONTATTO 35 mm — " + preset.title(), preset.setupLine(), BLUE);
    }

    private void showContact35PresetActions(final Contact35Preset preset) {
        if (armed || preset == null) return;
        showAppChoiceDialog("PRESET · " + preset.title(), new String[]{"MODIFICA", "ELIMINA"}, which -> {
            if (which == 0) {
                showContact35PresetEditor(preset);
            } else {
                showAppConfirmDialog("ELIMINARE IL PRESET?",
                        preset.title() + " · " + formatTime(preset.milliseconds),
                        "ELIMINA", () -> deleteContact35Preset(preset.id), "ANNULLA");
            }
        }, "ANNULLA");
    }

    private void showContact35PresetEditor(final Contact35Preset existing) {
        if (armed) return;
        if (darkroomMode) {
            Toast.makeText(this, "Per creare o modificare preset esci dalla modalità camera oscura", Toast.LENGTH_LONG).show();
            return;
        }
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        ScrollView sc = new ScrollView(this);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(CARD, 14, 1, BORDER));
        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));

        panel.addView(text(existing == null ? "NUOVO PRESET · CONTATTO 35 mm" : "MODIFICA PRESET · CONTATTO 35 mm", 19, TEXT_PRIMARY, true), lp(-1, -2));
        TextView fixed = text("Standard comuni: carta 24×30 · Rodagon 50 mm. Colonna, diaframma e contrasto sono precompilati ma modificabili per ogni preset.", 12, MUTED, false);
        fixed.setPadding(0, dp(5), 0, dp(12));
        panel.addView(fixed, lp(-1, -2));

        EditText film = editField("Pellicola — es. FP4+", existing == null ? "" : existing.film);
        EditText iso = editField("ISO — es. 125", existing == null ? "" : String.valueOf(existing.iso));
        EditText column = editField("Colonna LPL — predefinito 57", existing == null ? "57" : existing.column);
        EditText aperture = editField("Diaframma — predefinito f/8", existing == null ? "8" : existing.aperture);
        EditText contrast = editField("Contrasto — predefinito Y0 / M10", existing == null ? "Y0 / M10" : existing.contrast);
        EditText seconds = editField("Tempo (s) — es. 11,5", existing == null ? "" : String.format(Locale.ITALY, "%.1f", existing.milliseconds / 1000.0));
        iso.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        column.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        aperture.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        seconds.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        panel.addView(film, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(iso, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(column, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(aperture, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(contrast, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(seconds, margin(lp(-1, dp(52)), 0, 0, 0, 12));

        Button save = compactButton("SALVA PRESET");
        save.setBackground(roundRect(BLUE, 9, 0, 0));
        save.setTextColor(Color.BLACK);
        save.setOnClickListener(v -> {
            String filmName = film.getText().toString().trim();
            int isoValue;
            double secondsValue;
            try {
                isoValue = Integer.parseInt(iso.getText().toString().trim());
                secondsValue = Double.parseDouble(seconds.getText().toString().trim().replace(',', '.'));
            } catch (Exception ex) {
                Toast.makeText(this, "Controlla ISO e tempo", Toast.LENGTH_SHORT).show();
                return;
            }
            String columnValue = column.getText().toString().trim();
            String apertureValue = aperture.getText().toString().trim();
            String contrastValue = contrast.getText().toString().trim();
            if (filmName.isEmpty() || isoValue <= 0 || isoValue > 25600 || secondsValue < 0.5 || secondsValue > 36000.0
                    || columnValue.isEmpty() || apertureValue.isEmpty() || contrastValue.isEmpty()) {
                Toast.makeText(this, "Inserisci pellicola, ISO, setup e un tempo valido", Toast.LENGTH_LONG).show();
                return;
            }
            int ms = snap((int)Math.round(secondsValue * 1000.0), 500, 36_000_000);
            long id = existing == null ? System.currentTimeMillis() : existing.id;
            Contact35Preset saved = new Contact35Preset(id, filmName, isoValue, ms,
                    columnValue, apertureValue, contrastValue);
            persistContact35Preset(saved);
            dialog.dismiss();
            selectContact35Preset(saved);
        });
        panel.addView(save, lp(-1, dp(52)));

        Button cancel = compactButton("ANNULLA");
        cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel, margin(lp(-1, dp(48)), 0, 8, 0, 0));

        dialog.setContentView(sc);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f),
                (int)(getResources().getDisplayMetrics().heightPixels * 0.88f));
    }

    private LinearLayout buildContact35Panel() {
        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);

        LinearLayout intro = card();
        TextView title = text("PROVINO A CONTATTO · 35 mm", 17, TEXT_PRIMARY, true);
        title.setGravity(Gravity.CENTER);
        intro.addView(title);
        TextView common = text("STANDARD COMUNE · 24×30 · Rodagon 50 mm", 12, MUTED, true);
        common.setGravity(Gravity.CENTER);
        common.setPadding(dp(4), dp(5), dp(4), dp(3));
        intro.addView(common);
        TextView variable = text("Colonna, diaframma e contrasto sono salvati nel preset", 11, MUTED, false);
        variable.setGravity(Gravity.CENTER);
        variable.setPadding(dp(4), 0, dp(4), dp(10));
        intro.addView(variable);
        contact35NewPresetButton = compactButton("+  NUOVO PRESET");
        contact35NewPresetButton.setOnClickListener(v -> showContact35PresetEditor(null));
        intro.addView(contact35NewPresetButton, lp(-1, dp(50)));
        outer.addView(intro, margin(lp(-1, -2), 0, 0, 0, 10));

        LinearLayout selected = card();
        contact35SelectedLabel = text("NESSUN PRESET SELEZIONATO", 14, MUTED, true);
        contact35SelectedLabel.setGravity(Gravity.CENTER);
        selected.addView(contact35SelectedLabel);
        contact35SelectedSetup = text("24×30 · 50 mm · H57 · f/8 · Y0 / M10", 12, MUTED, true);
        contact35SelectedSetup.setGravity(Gravity.CENTER);
        contact35SelectedSetup.setPadding(dp(4), dp(6), dp(4), 0);
        selected.addView(contact35SelectedSetup);
        contact35SelectedTime = text("—", 44, BLUE, true);
        contact35SelectedTime.setGravity(Gravity.CENTER);
        contact35SelectedTime.setPadding(0, dp(6), 0, dp(4));
        selected.addView(contact35SelectedTime, lp(-1, dp(64)));
        TextView selectedHint = text("Tocca un preset per richiamarlo · pressione prolungata per modificarlo o eliminarlo", 11, MUTED, false);
        selectedHint.setGravity(Gravity.CENTER);
        selected.addView(selectedHint);
        outer.addView(selected, margin(lp(-1, -2), 0, 0, 0, 10));

        TextView presetsTitle = text("PRESET SALVATI", 12, MUTED, true);
        presetsTitle.setPadding(dp(4), 0, 0, dp(5));
        outer.addView(presetsTitle, lp(-1, -2));
        contact35PresetList = new LinearLayout(this);
        contact35PresetList.setOrientation(LinearLayout.VERTICAL);
        outer.addView(contact35PresetList, lp(-1, -2));
        return outer;
    }

    private void refreshContact35PresetList() {
        if (contact35PresetList == null) return;
        contact35PresetList.removeAllViews();
        ArrayList<Contact35Preset> presets = loadContact35Presets();
        if (presets.isEmpty()) {
            TextView empty = text("Nessun preset salvato. Premi + NUOVO PRESET dopo aver calibrato il tuo contatto.", 12, MUTED, false);
            empty.setGravity(Gravity.CENTER);
            empty.setPadding(dp(10), dp(10), dp(10), dp(10));
            contact35PresetList.addView(empty, lp(-1, -2));
            return;
        }
        for (Contact35Preset preset : presets) {
            boolean selected = preset.id == contact35SelectedId;
            Button b = compactButton(preset.title() + "   ·   " + formatTime(preset.milliseconds));
            b.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
            b.setPadding(dp(16), 0, dp(12), 0);
            b.setBackground(roundRect(selected ? BLUE : BUTTON, 9, 1, selected ? BLUE : BORDER));
            b.setTextColor(selected ? Color.BLACK : TEXT_PRIMARY);
            b.setOnClickListener(v -> selectContact35Preset(preset));
            b.setOnLongClickListener(v -> { showContact35PresetActions(preset); return true; });
            contact35PresetList.addView(b, margin(lp(-1, dp(52)), 0, 0, 0, 7));
        }
    }

    private void refreshContact35Ui() {
        if (contact35WorkspaceButton != null) {
            boolean active = contact35Mode;
            contact35WorkspaceButton.setBackground(roundRect(active ? BLUE : BUTTON, 9, 1, active ? BLUE : BORDER));
            contact35WorkspaceButton.setTextColor(active ? Color.BLACK : TEXT_PRIMARY);
        }
        if (contact35Mode && testSingleModeButton != null) {
            testSingleModeButton.setBackground(roundRect(BUTTON, 9, 1, BORDER));
            testSingleModeButton.setTextColor(TEXT_PRIMARY);
        }
        if (normalProvinoContent != null) normalProvinoContent.setVisibility(contact35Mode ? View.GONE : View.VISIBLE);
        if (contact35Content != null) contact35Content.setVisibility(contact35Mode ? View.VISIBLE : View.GONE);
        if (contact35NewPresetButton != null) {
            contact35NewPresetButton.setEnabled(!armed);
            contact35NewPresetButton.setAlpha(contact35NewPresetButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));
        }

        Contact35Preset selected = findContact35Preset(contact35SelectedId);
        if (contact35SelectedLabel != null) contact35SelectedLabel.setText(selected == null ? "NESSUN PRESET SELEZIONATO" : selected.title());
        if (contact35SelectedSetup != null) contact35SelectedSetup.setText(selected == null
                ? "24×30 · 50 mm · H57 · f/8 · Y0 / M10" : selected.setupLine());
        if (contact35SelectedTime != null) contact35SelectedTime.setText(selected == null ? "—" : formatTime(selected.milliseconds));
        refreshContact35PresetList();

        if (testPendingChoiceButton != null) {
            if (contact35Mode) testPendingChoiceButton.setVisibility(View.GONE);
            else refreshPendingTestStripChoiceUi();
        }
        if (actionButton != null && mode == MODE_TEST && !armed) {
            if (contact35Mode) {
                actionButton.setText(selected == null ? "SELEZIONA UN PRESET" : "ARMA CONTATTO · " + formatTime(selected.milliseconds));
                boolean ready = selected != null && device != null && device.isValid();
                actionButton.setEnabled(ready);
                actionButton.setAlpha(ready ? 1f : (darkroomMode ? 0.62f : 0.45f));
            } else {
                boolean ready = device != null && device.isValid();
                actionButton.setEnabled(ready);
                actionButton.setAlpha(ready ? 1f : (darkroomMode ? 0.62f : 0.45f));
            }
        }
    }

'''

new_build = r'''    private LinearLayout buildTestPanel() {
        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);

        LinearLayout provinoModeRow = new LinearLayout(this);
        provinoModeRow.setOrientation(LinearLayout.HORIZONTAL);
        provinoModeRow.setGravity(Gravity.CENTER);
        testSingleModeButton = compactButton("PROVINO SINGOLO");
        testSplitModeButton = compactButton("PROVINO SPLIT GRADE");
        testSingleModeButton.setOnClickListener(v -> {
            if (contact35Mode) setContact35Mode(false);
            requestSingleProvinoMode();
        });
        testSplitModeButton.setOnClickListener(v -> {
            if (contact35Mode) setContact35Mode(false);
            startSplitProvino();
        });
        provinoModeRow.addView(testSingleModeButton, margin(lp(0, dp(48), 1f), 0, 0, dp(4), 0));
        provinoModeRow.addView(testSplitModeButton, margin(lp(0, dp(48), 1f), dp(4), 0, 0, 0));
        outer.addView(provinoModeRow, margin(lp(-1, -2), 0, 0, 0, 10));

        testSplitPhaseText = text("", 14, BLUE, true);
        testSplitPhaseText.setGravity(Gravity.CENTER);
        testSplitPhaseText.setPadding(dp(12), dp(10), dp(12), dp(10));
        outer.addView(testSplitPhaseText, margin(lp(-1, -2), 0, 0, 0, 10));

        Button setEnlargement = compactButton("IMPOSTA INGRANDIMENTO");
        setEnlargement.setOnClickListener(v -> startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup")));
        outer.addView(setEnlargement, margin(lp(-1, dp(46)), 0, 0, 0, 10));

        contact35WorkspaceButton = compactButton("PROVINO A CONTATTO 35 mm");
        contact35WorkspaceButton.setOnClickListener(v -> setContact35Mode(!contact35Mode));
        outer.addView(contact35WorkspaceButton, margin(lp(-1, dp(48)), 0, 0, 0, 10));

        normalProvinoContent = new LinearLayout(this);
        normalProvinoContent.setOrientation(LinearLayout.VERTICAL);

        LinearLayout exposure = card();
        testPromptText = text(testPromptDescription(), 16, TEXT_PRIMARY, true);
        testPromptText.setGravity(Gravity.CENTER);
        exposure.addView(testPromptText);
        testStepText = text(testStepDescription(), 12, MUTED, false);
        testStepText.setGravity(Gravity.CENTER);
        exposure.addView(testStepText);
        testBaseFilterButton = compactButton(testBaseFilterButtonLabel());
        testBaseFilterButton.setOnClickListener(v -> showTestBaseFilterDialog());
        exposure.addView(testBaseFilterButton, margin(lp(-1, dp(50)), 0, 10, 0, 0));
        testStripMethodButton = compactButton(testStripMethodButtonLabel());
        testStripMethodButton.setOnClickListener(v -> showTestStripMethodDialog());
        exposure.addView(testStripMethodButton, margin(lp(-1, dp(50)), 0, 8, 0, 0));
        testPendingChoiceButton = compactButton("SCEGLI STRISCIA DEL PROVINO");
        testPendingChoiceButton.setTextColor(Color.WHITE);
        testPendingChoiceButton.setBackground(roundRect(BLUE, 9, 0, 0));
        testPendingChoiceButton.setOnClickListener(v -> maybeShowTestResultChooser(true));
        exposure.addView(testPendingChoiceButton, margin(lp(-1, dp(52)), 0, 8, 0, 0));
        refreshPendingTestStripChoiceUi();
        testFStopBadge = addFStopBadge(exposure, false);
        testContrastGuide = text("Leggi il provino dal CHIARO allo SCURO: se trovi prima i BIANCHI giusti → AUMENTA il contrasto; se trovi prima i NERI giusti → DIMINUISCI il contrasto. Se bianchi e neri sono giusti nello stesso gradino → CONTRASTO GIUSTO.", 12, darkroomMode ? RED : TEXT_PRIMARY, false);
        testContrastGuide.setPadding(dp(12), dp(10), dp(12), dp(10));
        testContrastGuide.setBackground(roundRect(darkroomMode ? Color.rgb(28,0,0) : Color.rgb(35,40,44), 9, 1, darkroomMode ? RED : BORDER));
        exposure.addView(testContrastGuide, margin(lp(-1,-2), 0, 8, 0, 0));
        exposure.addView(space(10));

        LinearLayout selector = new LinearLayout(this);
        selector.setGravity(Gravity.CENTER);
        selector.setOrientation(LinearLayout.HORIZONTAL);
        Button minus = smallButton("−");
        Button plus = smallButton("+");
        testTimeText = text(formatTime(testWidthMs), 44, BLUE, true);
        testTimeText.setGravity(Gravity.CENTER);
        selector.addView(minus, lp(dp(62), dp(58)));
        selector.addView(testTimeText, lp(0, dp(64), 1f));
        selector.addView(plus, lp(dp(62), dp(58)));
        minus.setOnClickListener(v -> adjustTestTime(-1));
        plus.setOnClickListener(v -> adjustTestTime(+1));
        exposure.addView(selector);
        testCumulativeText = text(cumulativeTimes(), 13, BLUE, true);
        testCumulativeText.setGravity(Gravity.CENTER);
        testCumulativeText.setPadding(dp(6), dp(6), dp(6), 0);
        exposure.addView(testCumulativeText, lp(-1, -2));
        normalProvinoContent.addView(exposure, margin(lp(-1, -2), 0, 0, 0, 10));

        LinearLayout settings = card();
        settings.addView(stepperRow("NUMERO ESPOSIZIONI", true));
        settings.addView(divider());
        settings.addView(stepperRow("PAUSA TRA LE ESPOSIZIONI", false));
        normalProvinoContent.addView(settings, lp(-1, -2));

        TextView note = text("Una sola pressione del pulsante fisico avvia il provino. Dopo la prima esposizione, le successive partono automaticamente dopo la pausa.", 12, MUTED, false);
        note.setGravity(Gravity.CENTER);
        note.setPadding(dp(8), dp(10), dp(8), 0);
        normalProvinoContent.addView(note, lp(-1, -2));
        outer.addView(normalProvinoContent, lp(-1, -2));

        contact35Content = buildContact35Panel();
        outer.addView(contact35Content, lp(-1, -2));

        refreshSplitProvinoUi();
        refreshContact35Ui();
        return outer;
    }

'''

wr(s[:helpers_start] + helpers + new_build + s[build_end:])
print('v0.6.0 OK simplified PROVINO hierarchy', flush=True)

# Contact contrast is a manual enlarger setting stored in the preset. Do not write a
# stale hard-coded M10 into the technical test metadata when the user edits it.
rep('''            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_TYPE, ExposureRecipe.FILTER_MAGENTA);\n            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_VALUE, 10);\n''',
    '''            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_TYPE, ExposureRecipe.FILTER_NONE);\n            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_VALUE, 0);\n''',
    'remove hard-coded contact contrast from Sonoff metadata')

# Guard against the terminology/layout regressions that motivated this release.
s = rd()
for forbidden in ('ISO/EI', ' · EI ', 'Controlla ISO/EI', 'Inserisci pellicola, ISO/EI'):
    if forbidden in s:
        raise SystemExit('v0.6.0 forbidden user-facing EI marker remains: ' + forbidden)
if 'compactButton("PROVINO STAMPA")' in s:
    raise SystemExit('v0.6.0 redundant PROVINO STAMPA workspace button remains')
required = [
    'compactButton("PROVINO SINGOLO")',
    'compactButton("PROVINO SPLIT GRADE")',
    'compactButton("IMPOSTA INGRANDIMENTO")',
    'compactButton("PROVINO A CONTATTO 35 mm")',
    'editField("ISO — es. 125"',
    'editField("Colonna LPL — predefinito 57"',
    'editField("Diaframma — predefinito f/8"',
    'editField("Contrasto — predefinito Y0 / M10"',
    'String setupLine()'
]
for marker in required:
    if marker not in s:
        raise SystemExit('v0.6.0 required marker missing: ' + marker)
order = [s.index('compactButton("PROVINO SINGOLO")'),
         s.index('compactButton("IMPOSTA INGRANDIMENTO")'),
         s.index('compactButton("PROVINO A CONTATTO 35 mm")')]
if order != sorted(order):
    raise SystemExit('v0.6.0 PROVINO visual hierarchy order invalid')

print('v0.6.0 contact layout patch complete', flush=True)
