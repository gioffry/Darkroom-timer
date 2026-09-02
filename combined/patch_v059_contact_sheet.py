#!/usr/bin/env python3
from pathlib import Path

root = Path('combined/src/main/java/it/darkroom/timer')
main = root / 'MainActivity.java'
service = root / 'SonoffArmService.java'


def rd(p):
    return Path(p).read_text(encoding='utf-8')


def wr(p, s):
    Path(p).write_text(s, encoding='utf-8')


def rep(p, old, new, label, count=1):
    s = rd(p)
    n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.5.9 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old, new, count))
    print('v0.5.9 OK', label, flush=True)


s = rd(main)
if 'private boolean contact35Mode = false;' in s and 'APP_VERSION = "0.13.12"' in s:
    print('v0.5.9 contact-sheet patch already applied', flush=True)
    raise SystemExit(0)

if 'private static final String APP_VERSION = "0.13.11";' not in s:
    raise SystemExit('v0.5.9: consolidated v0.5.8 Timer baseline not recognized')
if 'private LinearLayout buildTestPanel() {' not in s:
    raise SystemExit('v0.5.9: buildTestPanel marker missing')
if 'count = Math.max(2, Math.min(20, intent.getIntExtra(EXTRA_COUNT, 7)));' not in rd(service):
    raise SystemExit('v0.5.9: Sonoff test count baseline not recognized')

# Internal Timer engine marker advances because this release changes the PROVINO workflow.
rep(main,
    '    private static final String APP_VERSION = "0.13.11";\n',
    '    private static final String APP_VERSION = "0.13.12";\n',
    'Timer internal version')

# Contact-sheet preset record. Values are intentionally tiny and kept in SharedPreferences,
# so user calibration survives normal APK updates without any database migration.
rep(main,
'''    private interface ChoiceAction {\n        void choose(int index);\n    }\n\n''',
'''    private interface ChoiceAction {\n        void choose(int index);\n    }\n\n    private static final class Contact35Preset {\n        final long id;\n        final String film;\n        final int ei;\n        final int milliseconds;\n\n        Contact35Preset(long id, String film, int ei, int milliseconds) {\n            this.id = id;\n            this.film = film == null ? "" : film.trim();\n            this.ei = ei;\n            this.milliseconds = milliseconds;\n        }\n\n        String title() { return film + " · EI " + ei; }\n    }\n\n''',
    'Contact35Preset model')

rep(main,
'''    private TextView testSplitPhaseText;\n    private TextView testContrastGuide;\n''',
'''    private TextView testSplitPhaseText;\n    private TextView testContrastGuide;\n    private Button provinoPrintWorkspaceButton;\n    private Button contact35WorkspaceButton;\n    private Button contact35NewPresetButton;\n    private LinearLayout normalProvinoContent;\n    private LinearLayout contact35Content;\n    private LinearLayout contact35PresetList;\n    private TextView contact35SelectedLabel;\n    private TextView contact35SelectedTime;\n''',
    'contact UI fields')

rep(main,
'''    private long transientCompletionUntilMs = 0L;\n    private boolean testChooserOpen = false;\n''',
'''    private long transientCompletionUntilMs = 0L;\n    private boolean testChooserOpen = false;\n    private boolean contact35Mode = false;\n    private long contact35SelectedId = -1L;\n''',
    'contact state fields')

rep(main,
'''        splitReturnFilterValue = ExposureRecipe.snap5(p.getInt("splitProvinoReturnFilterValue", testBaseFilterValue));\n        splitReturnTestWidthMs = p.getInt("splitProvinoReturnTestWidthMs", testWidthMs);\n''',
'''        splitReturnFilterValue = ExposureRecipe.snap5(p.getInt("splitProvinoReturnFilterValue", testBaseFilterValue));\n        splitReturnTestWidthMs = p.getInt("splitProvinoReturnTestWidthMs", testWidthMs);\n        contact35Mode = p.getBoolean("contact35Mode", false);\n        contact35SelectedId = p.getLong("contact35SelectedId", -1L);\n''',
    'load contact state')

# Keep the transient ready message coherent with the active PROVINO workspace.
rep(main,
'''            if (device != null && device.isValid()) {\n                setStatusPresentation("PRONTO", "Scegli il tempo e premi ARMA", GREEN);\n            } else {\n''',
'''            if (device != null && device.isValid()) {\n                if (mode == MODE_TEST && contact35Mode)\n                    setStatusPresentation("PRONTO", "Scegli un preset del contatto 35 mm e premi ARMA", BLUE);\n                else\n                    setStatusPresentation("PRONTO", "Scegli il tempo e premi ARMA", GREEN);\n            } else {\n''',
    'contact ready message')

# -----------------------------------------------------------------------------
# Replace PROVINO UI with a two-level selector:
# PROVINO STAMPA | CONTATTO 35 mm, while keeping SINGOLO | SPLIT GRADE unchanged
# inside the normal workspace.
# -----------------------------------------------------------------------------
s = rd(main)
start = s.find('    private LinearLayout buildTestPanel() {\n')
end = s.find('    private LinearLayout buildLogPanel() {\n', start)
if start < 0 or end < 0:
    raise SystemExit('v0.5.9: buildTestPanel bounds not found')

contact_helpers = r'''    private SharedPreferences contact35Preferences() {
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
                    int ei = prefs.getInt("ei_" + id, 0);
                    int ms = prefs.getInt("ms_" + id, 0);
                    if (film != null && !film.trim().isEmpty() && ei > 0 && ms >= 500)
                        out.add(new Contact35Preset(id, film, ei, snap(ms, 500, 36_000_000)));
                } catch (Exception ignored) {}
            }
        }
        Collections.sort(out, (a, b) -> {
            int byFilm = a.film.compareToIgnoreCase(b.film);
            if (byFilm != 0) return byFilm;
            return Integer.compare(a.ei, b.ei);
        });
        return out;
    }

    private Contact35Preset findContact35Preset(long id) {
        if (id <= 0L) return null;
        for (Contact35Preset p : loadContact35Presets()) if (p.id == id) return p;
        return null;
    }

    private void persistContact35Preset(Contact35Preset preset) {
        if (preset == null || preset.id <= 0L || preset.film.trim().isEmpty() || preset.ei <= 0 || preset.milliseconds < 500) return;
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
                .putInt("ei_" + preset.id, preset.ei)
                .putInt("ms_" + preset.id, snap(preset.milliseconds, 500, 36_000_000))
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
                .remove("ei_" + id)
                .remove("ms_" + id)
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
            Toast.makeText(this, "Torna a SINGOLO o termina lo Split Grade prima del contatto", Toast.LENGTH_LONG).show();
            return;
        }
        contact35Mode = enabled;
        getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("contact35Mode", contact35Mode).apply();
        refreshContact35Ui();
        applyModeUi();
        if (contact35Mode) {
            Contact35Preset selected = findContact35Preset(contact35SelectedId);
            if (selected == null)
                setStatusPresentation("CONTATTO 35 mm", "Crea un nuovo preset oppure richiamane uno già salvato", BLUE);
            else
                setStatusPresentation("CONTATTO 35 mm — " + selected.title(),
                        "SETUP 24×30 · 50 mm · H57 · f/8 · M10", BLUE);
        }
    }

    private void selectContact35Preset(Contact35Preset preset) {
        if (armed || preset == null) return;
        contact35SelectedId = preset.id;
        getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("contact35SelectedId", preset.id).apply();
        refreshContact35Ui();
        applyModeUi();
        setStatusPresentation("CONTATTO 35 mm — " + preset.title(),
                "SETUP 24×30 · 50 mm · H57 · f/8 · M10", BLUE);
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
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(CARD, 14, 1, BORDER));

        panel.addView(text(existing == null ? "NUOVO PRESET · CONTATTO 35 mm" : "MODIFICA PRESET · CONTATTO 35 mm", 19, TEXT_PRIMARY, true), lp(-1, -2));
        TextView fixed = text("Setup fisso: carta 24×30 · Rodagon 50 mm · H57 · f/8 · Y0/M10. Inserisci solo la tua calibrazione.", 12, MUTED, false);
        fixed.setPadding(0, dp(5), 0, dp(12));
        panel.addView(fixed, lp(-1, -2));

        EditText film = editField("Pellicola — es. FP4+", existing == null ? "" : existing.film);
        EditText ei = editField("ISO/EI — es. 125", existing == null ? "" : String.valueOf(existing.ei));
        EditText seconds = editField("Tempo (s) — es. 11,5", existing == null ? "" : String.format(Locale.ITALY, "%.1f", existing.milliseconds / 1000.0));
        ei.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        seconds.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        panel.addView(film, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(ei, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(seconds, margin(lp(-1, dp(52)), 0, 0, 0, 12));

        Button save = compactButton("SALVA PRESET");
        save.setBackground(roundRect(BLUE, 9, 0, 0));
        save.setTextColor(Color.BLACK);
        save.setOnClickListener(v -> {
            String filmName = film.getText().toString().trim();
            int eiValue;
            double secondsValue;
            try {
                eiValue = Integer.parseInt(ei.getText().toString().trim());
                secondsValue = Double.parseDouble(seconds.getText().toString().trim().replace(',', '.'));
            } catch (Exception ex) {
                Toast.makeText(this, "Controlla ISO/EI e tempo", Toast.LENGTH_SHORT).show();
                return;
            }
            if (filmName.isEmpty() || eiValue <= 0 || eiValue > 25600 || secondsValue < 0.5 || secondsValue > 36000.0) {
                Toast.makeText(this, "Inserisci pellicola, ISO/EI e un tempo valido", Toast.LENGTH_LONG).show();
                return;
            }
            int ms = snap((int)Math.round(secondsValue * 1000.0), 500, 36_000_000);
            long id = existing == null ? System.currentTimeMillis() : existing.id;
            Contact35Preset saved = new Contact35Preset(id, filmName, eiValue, ms);
            persistContact35Preset(saved);
            dialog.dismiss();
            selectContact35Preset(saved);
        });
        panel.addView(save, lp(-1, dp(52)));

        Button cancel = compactButton("ANNULLA");
        cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel, margin(lp(-1, dp(48)), 0, 8, 0, 0));

        dialog.setContentView(panel);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f), ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private LinearLayout buildContact35Panel() {
        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);

        LinearLayout intro = card();
        TextView title = text("PROVINO A CONTATTO · 35 mm", 17, TEXT_PRIMARY, true);
        title.setGravity(Gravity.CENTER);
        intro.addView(title);
        TextView setup = text("SETUP FISSO · 24×30 · 50 mm · H57 · f/8 · M10", 12, MUTED, true);
        setup.setGravity(Gravity.CENTER);
        setup.setPadding(dp(4), dp(5), dp(4), dp(10));
        intro.addView(setup);
        contact35NewPresetButton = compactButton("+  NUOVO PRESET");
        contact35NewPresetButton.setOnClickListener(v -> showContact35PresetEditor(null));
        intro.addView(contact35NewPresetButton, lp(-1, dp(50)));
        outer.addView(intro, margin(lp(-1, -2), 0, 0, 0, 10));

        LinearLayout selected = card();
        contact35SelectedLabel = text("NESSUN PRESET SELEZIONATO", 14, MUTED, true);
        contact35SelectedLabel.setGravity(Gravity.CENTER);
        selected.addView(contact35SelectedLabel);
        contact35SelectedTime = text("—", 44, BLUE, true);
        contact35SelectedTime.setGravity(Gravity.CENTER);
        contact35SelectedTime.setPadding(0, dp(8), 0, dp(4));
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
        if (provinoPrintWorkspaceButton != null) {
            boolean active = !contact35Mode;
            provinoPrintWorkspaceButton.setBackground(roundRect(active ? BLUE : BUTTON, 9, 1, active ? BLUE : BORDER));
            provinoPrintWorkspaceButton.setTextColor(active ? Color.BLACK : TEXT_PRIMARY);
        }
        if (contact35WorkspaceButton != null) {
            boolean active = contact35Mode;
            contact35WorkspaceButton.setBackground(roundRect(active ? BLUE : BUTTON, 9, 1, active ? BLUE : BORDER));
            contact35WorkspaceButton.setTextColor(active ? Color.BLACK : TEXT_PRIMARY);
        }
        if (normalProvinoContent != null) normalProvinoContent.setVisibility(contact35Mode ? View.GONE : View.VISIBLE);
        if (contact35Content != null) contact35Content.setVisibility(contact35Mode ? View.VISIBLE : View.GONE);
        if (contact35NewPresetButton != null) {
            contact35NewPresetButton.setEnabled(!armed);
            contact35NewPresetButton.setAlpha(contact35NewPresetButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));
        }

        Contact35Preset selected = findContact35Preset(contact35SelectedId);
        if (contact35SelectedLabel != null) contact35SelectedLabel.setText(selected == null ? "NESSUN PRESET SELEZIONATO" : selected.title());
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

        LinearLayout workspaceRow = new LinearLayout(this);
        workspaceRow.setOrientation(LinearLayout.HORIZONTAL);
        workspaceRow.setGravity(Gravity.CENTER);
        provinoPrintWorkspaceButton = compactButton("PROVINO STAMPA");
        contact35WorkspaceButton = compactButton("CONTATTO 35 mm");
        provinoPrintWorkspaceButton.setOnClickListener(v -> setContact35Mode(false));
        contact35WorkspaceButton.setOnClickListener(v -> setContact35Mode(true));
        workspaceRow.addView(provinoPrintWorkspaceButton, margin(lp(0, dp(48), 1f), 0, 0, dp(4), 0));
        workspaceRow.addView(contact35WorkspaceButton, margin(lp(0, dp(48), 1f), dp(4), 0, 0, 0));
        outer.addView(workspaceRow, margin(lp(-1, -2), 0, 0, 0, 10));

        normalProvinoContent = new LinearLayout(this);
        normalProvinoContent.setOrientation(LinearLayout.VERTICAL);
        LinearLayout provinoModeRow = new LinearLayout(this);
        provinoModeRow.setOrientation(LinearLayout.HORIZONTAL);
        provinoModeRow.setGravity(Gravity.CENTER);
        testSingleModeButton = compactButton("SINGOLO");
        testSplitModeButton = compactButton("SPLIT GRADE");
        testSingleModeButton.setOnClickListener(v -> requestSingleProvinoMode());
        testSplitModeButton.setOnClickListener(v -> startSplitProvino());
        provinoModeRow.addView(testSingleModeButton, margin(lp(0, dp(48), 1f), 0, 0, dp(4), 0));
        provinoModeRow.addView(testSplitModeButton, margin(lp(0, dp(48), 1f), dp(4), 0, 0, 0));
        normalProvinoContent.addView(provinoModeRow, margin(lp(-1, -2), 0, 0, 0, 10));

        testSplitPhaseText = text("", 14, BLUE, true);
        testSplitPhaseText.setGravity(Gravity.CENTER);
        testSplitPhaseText.setPadding(dp(12), dp(10), dp(12), dp(10));
        normalProvinoContent.addView(testSplitPhaseText, margin(lp(-1, -2), 0, 0, 0, 10));

        Button setEnlargement = compactButton("IMPOSTA INGRANDIMENTO");
        setEnlargement.setOnClickListener(v -> startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup")));
        normalProvinoContent.addView(setEnlargement, margin(lp(-1, dp(46)), 0, 0, 0, 10));

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

wr(main, s[:start] + contact_helpers + new_build + s[end:])
print('v0.5.9 OK PROVINO workspace + contact preset UI', flush=True)

# applyModeUi: normal logic first, then contact workspace gets final say over the shared ARMA button.
rep(main,
'''        refreshSplitProvinoUi();\n    }\n\n    private void arm() {\n''',
'''        refreshSplitProvinoUi();\n        refreshContact35Ui();\n    }\n\n    private void arm() {\n''',
    'applyModeUi contact refresh')

# Keep reconnect/disabled state from enabling ARMA when contact mode has no selected preset.
rep(main,
'''    private void setControlsEnabled(boolean enabled) {\n        boolean ready = enabled && device != null && device.isValid() && !armed;\n        actionButton.setEnabled(ready);\n''',
'''    private void setControlsEnabled(boolean enabled) {\n        boolean ready = enabled && device != null && device.isValid() && !armed;\n        if (mode == MODE_TEST && contact35Mode && findContact35Preset(contact35SelectedId) == null) ready = false;\n        actionButton.setEnabled(ready);\n''',
    'contact ARMA enable guard')

# Replace ARM method: a contact preset is a single MINIR2-timed exposure, never a test-strip
# series. It intentionally uses the existing robust Sonoff service timing path.
s = rd(main)
start = s.find('    private void arm() {\n')
end = s.find('    private void cancelCurrentCycle() {\n', start)
if start < 0 or end < 0:
    raise SystemExit('v0.5.9: arm bounds not found')
new_arm = r'''    private void arm() {
        if (mode == MODE_LOG) return;
        Contact35Preset contactPreset = null;
        if (mode == MODE_TEST && contact35Mode) {
            contactPreset = findContact35Preset(contact35SelectedId);
            if (contactPreset == null) {
                setStatusPresentation("CONTATTO 35 mm", "Seleziona prima un preset", BLUE);
                return;
            }
        }
        if (device == null || !device.isValid()) {
            stateText.setText("Il SONOFF dell’ingranditore non è ancora verificato in DIY");
            return;
        }
        if (mode == MODE_PRINT && !validatePrintSequenceForBase()) return;
        if (safelightAuto) {
            DeviceConfig safe = SafelightConfig.load(this);
            if (!safe.isValid() || safe.deviceId.equals(device.deviceId)) {
                setStatusPresentation("ATTENZIONE", "Configura un secondo SONOFF DIY dedicato alla luce rossa", RED);
                return;
            }
        }
        armed = true;
        cancelCycleButton.setEnabled(true);
        setStatusPresentation("PREPARAZIONE",
                mode == MODE_PRINT ? "Imposto Inching…" : (contact35Mode ? "Preparo il contatto 35 mm…" : "Preparo il provino…"), AMBER);
        setControlsEnabled(false);

        Intent i;
        if (mode == MODE_PRINT) {
            SharedPreferences activeUi = getSharedPreferences("ui", MODE_PRIVATE);
            getSharedPreferences("log_session", MODE_PRIVATE).edit()
                    .putString("pendingEnlargementMeta", activeUi.getString("enlargementMeta", ""))
                    .putLong("pendingEnlargementAt", System.currentTimeMillis())
                    .apply();
            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_PRINT);
            ensureExposureRecipeBase();
            persistExposureRecipe();
            i.putExtra(SonoffArmService.EXTRA_WIDTH, printWidthMs);
            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);
            i.putExtra(SonoffArmService.EXTRA_PRINT_SEQUENCE, printSequence == null ? "" : printSequence.encode());
            i.putExtra(SonoffArmService.EXTRA_RECIPE_STATE, exposureRecipe.encode());
        } else if (contact35Mode) {
            int ms = snap(contactPreset.milliseconds, 500, 36_000_000);
            getSharedPreferences("ui", MODE_PRIVATE).edit()
                    .putBoolean("contact35CycleActive", true)
                    .putLong("contact35CyclePresetId", contactPreset.id)
                    .apply();
            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_TEST);
            i.putExtra(SonoffArmService.EXTRA_WIDTH, ms);
            i.putExtra(SonoffArmService.EXTRA_COUNT, 1);
            i.putExtra(SonoffArmService.EXTRA_PAUSE, 500);
            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, TimingMath.METHOD_SECONDS);
            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, new int[]{ms});
            i.putExtra(SonoffArmService.EXTRA_TEST_MASKING_METHOD, TimingMath.MASK_COVER);
            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_TYPE, ExposureRecipe.FILTER_MAGENTA);
            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_VALUE, 10);
            i.putExtra(SonoffArmService.EXTRA_CONTACT_SHEET_35, true);
        } else {
            i = new Intent(this, SonoffArmService.class).setAction(SonoffArmService.ACTION_ARM_TEST);
            i.putExtra(SonoffArmService.EXTRA_WIDTH, testWidthMs);
            i.putExtra(SonoffArmService.EXTRA_COUNT, testCount);
            i.putExtra(SonoffArmService.EXTRA_PAUSE, testPauseMs);
            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);
            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());
            i.putExtra(SonoffArmService.EXTRA_TEST_MASKING_METHOD, TimingMath.normalizeMaskingMethod(testStripMethod));
            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_TYPE, ExposureRecipe.normalizeFilter(testBaseFilterType));
            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_VALUE, ExposureRecipe.snap5(testBaseFilterValue));
            if (provinoFlow == PROVINO_SPLIT_HARD && splitSoftChosenMs > 0) {
                i.putExtra(SonoffArmService.EXTRA_TEST_PRE_EXPOSURE_MS, snap(splitSoftChosenMs, 500, 36_000_000));
                i.putExtra(SonoffArmService.EXTRA_TEST_PRE_EXPOSURE_FILTER_TYPE, ExposureRecipe.FILTER_YELLOW);
                i.putExtra(SonoffArmService.EXTRA_TEST_PRE_EXPOSURE_FILTER_VALUE, ExposureRecipe.snap5(splitSoftYellow));
            }
        }
        startServiceCompat(i);
    }

'''
wr(main, s[:start] + new_arm + s[end:])
print('v0.5.9 OK contact ARM path', flush=True)

# A contact exposure must never open the normal "choose strip" importer.
rep(main,
'''    private void maybeShowTestResultChooser(boolean forceManual) {\n        if (armed || mode != MODE_TEST || isFinishing()) return;\n''',
'''    private void maybeShowTestResultChooser(boolean forceManual) {\n        if (armed || mode != MODE_TEST || isFinishing()) return;\n        if (contact35Mode || getSharedPreferences("ui", MODE_PRIVATE).getBoolean("contact35CycleActive", false)) return;\n''',
    'suppress strip chooser for contact')

# Contact completion: consume the test-cycle bookkeeping immediately, do not offer
# to transfer it to STAMPA/LOG, and preserve the selected preset for the next roll.
old_completion = '''            } else if (detail.toLowerCase(Locale.ITALY).contains("provino completato")) {\n                int countDone = session.getInt("lastTestCount", testCount);\n                if (provinoFlow == PROVINO_SPLIT_SOFT) {\n                    title = "✓  FASE 1 COMPLETATA — MORBIDO";\n                    detail = "Scegli il tempo morbido oppure reimposta la fase";\n                } else if (provinoFlow == PROVINO_SPLIT_HARD) {\n                    title = "✓  FASE 2 COMPLETATA — DURO";\n                    detail = "Ogni striscia comprende già la base morbida scelta";\n                } else {\n                    title = "✓  PROVINO COMPLETATO — " + countDone + "/" + countDone;\n                    detail = "Scegli la striscia da usare come punto di partenza per la stampa";\n                }\n                accent = BLUE;\n                transientCompletion = true;\n                new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 180L);\n'''
new_completion = '''            } else if (detail.toLowerCase(Locale.ITALY).contains("provino completato")) {\n                SharedPreferences ui = getSharedPreferences("ui", MODE_PRIVATE);\n                boolean contactCycle = contact35Mode || ui.getBoolean("contact35CycleActive", false);\n                if (contactCycle) {\n                    long presetId = ui.getLong("contact35CyclePresetId", contact35SelectedId);\n                    Contact35Preset preset = findContact35Preset(presetId);\n                    long testAt = session.getLong("lastTestAt", 0L);\n                    long cycleAt = session.getLong("lastCycleAt", 0L);\n                    SharedPreferences.Editor done = ui.edit()\n                            .remove("contact35CycleActive")\n                            .remove("contact35CyclePresetId");\n                    if (testAt > 0L) done.putLong("lastTestChooserShownAt", testAt);\n                    if (cycleAt > 0L) done.putLong("lastSavedCycleAt", cycleAt);\n                    done.apply();\n                    title = "✓  CONTATTO 35 mm COMPLETATO";\n                    detail = preset == null ? "Inching disattivato · preset pronto per una nuova esposizione"\n                            : preset.title() + " · " + formatTime(preset.milliseconds) + " · Inching disattivato";\n                    accent = BLUE;\n                    transientCompletion = true;\n                    refreshPendingTestStripChoiceUi();\n                } else {\n                    int countDone = session.getInt("lastTestCount", testCount);\n                    if (provinoFlow == PROVINO_SPLIT_SOFT) {\n                        title = "✓  FASE 1 COMPLETATA — MORBIDO";\n                        detail = "Scegli il tempo morbido oppure reimposta la fase";\n                    } else if (provinoFlow == PROVINO_SPLIT_HARD) {\n                        title = "✓  FASE 2 COMPLETATA — DURO";\n                        detail = "Ogni striscia comprende già la base morbida scelta";\n                    } else {\n                        title = "✓  PROVINO COMPLETATO — " + countDone + "/" + countDone;\n                        detail = "Scegli la striscia da usare come punto di partenza per la stampa";\n                    }\n                    accent = BLUE;\n                    transientCompletion = true;\n                    new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 180L);\n                }\n'''
rep(main, old_completion, new_completion, 'contact completion handling')

rep(main,
'''        } else if (SonoffArmService.STATE_ERROR.equals(state)) {\n            armed = false;\n''',
'''        } else if (SonoffArmService.STATE_ERROR.equals(state)) {\n            armed = false;\n            clearContact35CycleMarker();\n''',
    'clear contact marker on error')

rep(main,
'''            } else if (detail.toLowerCase(Locale.ITALY).contains("annullato")) {\n                title = "CICLO ANNULLATO";\n''',
'''            } else if (detail.toLowerCase(Locale.ITALY).contains("annullato")) {\n                clearContact35CycleMarker();\n                title = "CICLO ANNULLATO";\n''',
    'clear contact marker on cancel')

# -----------------------------------------------------------------------------
# Sonoff service: permit exactly one exposure only when explicitly flagged as a
# 35 mm contact sheet. Regular test strips keep their historical 2..20 invariant.
# -----------------------------------------------------------------------------
rep(service,
'''    public static final String EXTRA_TEST_PRE_EXPOSURE_FILTER_VALUE = "test_pre_exposure_filter_value";\n''',
'''    public static final String EXTRA_TEST_PRE_EXPOSURE_FILTER_VALUE = "test_pre_exposure_filter_value";\n    public static final String EXTRA_CONTACT_SHEET_35 = "contact_sheet_35";\n''',
    'contact service extra')

rep(service,
'''    private volatile int count = 7;\n''',
'''    private volatile int count = 7;\n    private volatile boolean contactSheet35 = false;\n''',
    'contact service state')

rep(service,
'''            mode = ACTION_ARM_TEST.equals(action) ? MODE_TEST : MODE_PRINT;\n            widthMs = sanitizeWidth(intent.getIntExtra(EXTRA_WIDTH, 8500));\n''',
'''            mode = ACTION_ARM_TEST.equals(action) ? MODE_TEST : MODE_PRINT;\n            contactSheet35 = mode == MODE_TEST && intent.getBooleanExtra(EXTRA_CONTACT_SHEET_35, false);\n            widthMs = sanitizeWidth(intent.getIntExtra(EXTRA_WIDTH, 8500));\n''',
    'read contact service flag')

rep(service,
'''            count = Math.max(2, Math.min(20, intent.getIntExtra(EXTRA_COUNT, 7)));\n''',
'''            count = contactSheet35 ? 1 : Math.max(2, Math.min(20, intent.getIntExtra(EXTRA_COUNT, 7)));\n''',
    'single contact exposure count')

rep(service,
'''                    : (TimingMath.isFStop(timingMethod) ? "PROVINO F-STOP · ¼ stop • strisce " + TimingMath.seriesLabel(testTargetsMs) + " • pausa " + seconds(pauseMs) : "PROVINO richiesto " + count + " × " + seconds(widthMs) + " • pausa " + seconds(pauseMs)));\n''',
'''                    : (contactSheet35 ? "CONTATTO 35 mm richiesto " + seconds(widthMs)\n                    : (TimingMath.isFStop(timingMethod) ? "PROVINO F-STOP · ¼ stop • strisce " + TimingMath.seriesLabel(testTargetsMs) + " • pausa " + seconds(pauseMs) : "PROVINO richiesto " + count + " × " + seconds(widthMs) + " • pausa " + seconds(pauseMs))));\n''',
    'contact technical log label')

rep(service,
'''                    : (TimingMath.isFStop(timingMethod) ? "Preparo provino: " + count + " strisce • ¼ stop" : "Preparo provino: " + count + " × " + seconds(widthMs)));\n''',
'''                    : (contactSheet35 ? "Preparo contatto 35 mm: " + seconds(widthMs)\n                    : (TimingMath.isFStop(timingMethod) ? "Preparo provino: " + count + " strisce • ¼ stop" : "Preparo provino: " + count + " × " + seconds(widthMs))));\n''',
    'contact arming label')

rep(service,
'''                            : (!testPreExposureDone ? "ESPOSIZIONE MORBIDA SU TUTTA LA STRISCIA — " + seconds(testPreExposureMs)\n                            : (TimingMath.isFStop(timingMethod) ? "PROVINO DURO " + current + "/" + count + " — fascia finale " + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod)) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs)));\n''',
'''                            : (contactSheet35 ? "CONTATTO 35 mm — esposizione " + seconds(widthMs)\n                            : (!testPreExposureDone ? "ESPOSIZIONE MORBIDA SU TUTTA LA STRISCIA — " + seconds(testPreExposureMs)\n                            : (TimingMath.isFStop(timingMethod) ? "PROVINO DURO " + current + "/" + count + " — fascia finale " + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod)) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs))));\n''',
    'contact exposure label')

rep(service,
'''                String msg = mode == MODE_PRINT\n                        ? "PRONTO — stampa conclusa, Inching disattivato"\n                        : "PRONTO — provino completato, Inching disattivato";\n''',
'''                String msg = mode == MODE_PRINT\n                        ? "PRONTO — stampa conclusa, Inching disattivato"\n                        : (contactSheet35 ? "PRONTO — provino completato · CONTATTO 35 mm, Inching disattivato"\n                        : "PRONTO — provino completato, Inching disattivato");\n''',
    'contact completion service label')

print('v0.5.9 contact-sheet patch complete', flush=True)
