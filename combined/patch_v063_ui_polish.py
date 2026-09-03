#!/usr/bin/env python3
"""Darkroom 0.6.3: phone-verified UI polish without changing behaviour."""

from pathlib import Path


MAIN = Path("combined/src/main/java/it/darkroom/timer/MainActivity.java")
ENLARGEMENT = Path("combined/src/main/java/it/darkroom/timer/EnlargementActivity.java")
VISUAL = Path("combined/src/main/java/it/darkroom/ui/DarkroomVisualSystem.java")


def rep(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)
    if found != count:
        raise SystemExit(f"v0.6.3 {label}: expected {count}, found {found}")
    return text.replace(old, new)


main = MAIN.read_text(encoding="utf-8")
enlargement = ENLARGEMENT.read_text(encoding="utf-8")
visual = VISUAL.read_text(encoding="utf-8")

if "UI_POLISH_063" in main and "ENLARGEMENT_COMPACT_063" in enlargement:
    print("ui_polish_063=ALREADY_APPLIED")
    raise SystemExit(0)
if "TIMER_REFINEMENT_062" not in main or 'APP_VERSION = "0.13.15"' not in main:
    raise SystemExit("v0.6.3: exact v0.6.2 Timer source not recognized")
if "ENLARGEMENT_VISUAL_062" not in enlargement:
    raise SystemExit("v0.6.3: exact v0.6.2 enlargement source not recognized")

main_before = main
enlargement_before = enlargement
visual_before = visual

main = rep(
    main,
    "    // TIMER_REFINEMENT_062 — phone-verified hierarchy and phase identity.\n",
    "    // TIMER_REFINEMENT_062 — phone-verified hierarchy and phase identity.\n"
    "    // UI_POLISH_063 — phone-verified dialogs, settings and archive hierarchy.\n",
    "Timer polish marker",
)
main = rep(main, 'APP_VERSION = "0.13.15"', 'APP_VERSION = "0.13.16"', "Timer version")

# The print plan is a neutral paper/workspace colour, not the yellow filtration phase.
visual = rep(
    visual,
    "    public static final int PRINT_PLAN = Color.rgb(200, 177, 69);",
    "    public static final int PRINT_PLAN = Color.rgb(196, 174, 142);",
    "print-plan colour",
)

# The masking-method chooser shows the current choice and follows the active provino phase.
main = rep(
    main,
    '''    private void showTestStripMethodDialog() {
        if (armed) return;
        String[] choices = {
                "SCOPRIRE — parti con 1 fascia e ne scopri una in più",
                "COPRIRE — parti tutto scoperto e copri una fascia alla volta"
        };
        showAppChoiceDialog("METODO DI PROVINATURA", choices, which -> {
            testStripMethod = which == 1 ? TimingMath.MASK_COVER : TimingMath.MASK_REVEAL;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("testStripMethod", testStripMethod).apply();
            refreshTestStripMethodUi();
        }, "ANNULLA");
    }
''',
    '''    private void showTestStripMethodDialog() {
        if (armed) return;
        String[] choices = {
                "SCOPRIRE — parti con 1 fascia e scoprine una in più",
                "COPRIRE — parti tutto scoperto e copri una fascia alla volta"
        };
        int selected = TimingMath.MASK_COVER.equals(TimingMath.normalizeMaskingMethod(testStripMethod)) ? 1 : 0;
        int accent = isSplitProvino() ? splitPhaseAccent() : PROVINO_ACCENT;
        showSelectedChoiceDialog("METODO DEL PROVINO", choices, selected, accent, which -> {
            testStripMethod = which == 1 ? TimingMath.MASK_COVER : TimingMath.MASK_REVEAL;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("testStripMethod", testStripMethod).apply();
            refreshTestStripMethodUi();
        }, "ANNULLA");
    }

    private void showSelectedChoiceDialog(String title, String[] choices, int selectedIndex,
                                          int accent, ChoiceAction action, String cancelLabel) {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        final int visualAccent = darkroomMode ? RED : accent;
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, visualAccent));

        TextView heading = text(title, 18, visualAccent, true);
        panel.addView(heading, margin(lp(-1, -2), 0, 0, 0, 12));
        for (int i = 0; i < choices.length; i++) {
            final int index = i;
            boolean selected = index == selectedIndex;
            Button option = compactButton((selected ? "✓  " : "") + choices[i]);
            option.setTextColor(actionInk(visualAccent));
            option.setBackground(roundRect(visualAccent, 9, 0, 0));
            option.setAlpha(selected ? 1f : 0.84f);
            option.setOnClickListener(v -> {
                dialog.dismiss();
                action.choose(index);
            });
            panel.addView(option, margin(lp(-1, dp(62)), 0, 0, 0, 7));
        }
        Button cancel = compactButton(cancelLabel);
        cancel.setTextColor(darkroomMode ? RED : MUTED);
        cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel, margin(lp(-1, dp(48)), 0, 6, 0, 0));

        dialog.setContentView(panel);
        Window w = dialog.getWindow();
        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f),
                ViewGroup.LayoutParams.WRAP_CONTENT);
    }
''',
    "selected masking method dialog",
)

# Settings use one coloured outline/fill family per group; ON/OFF remains the stored state.
main = rep(
    main,
    '''    private LinearLayout settingsGroup(String heading) {
        LinearLayout g = card();
        g.setPadding(dp(12), dp(10), dp(12), dp(12));
        TextView h = text(heading, 11, MUTED, true);
        h.setPadding(dp(4), 0, dp(4), dp(8));
        g.addView(h, lp(-1,-2));
        return g;
    }
''',
    '''    private LinearLayout settingsGroup(String heading, int accent) {
        int visualAccent = darkroomMode ? RED : accent;
        LinearLayout g = informationCard(visualAccent);
        g.setPadding(dp(12), dp(10), dp(12), dp(12));
        TextView h = text(heading, 12, visualAccent, true);
        h.setPadding(dp(4), 0, dp(4), dp(8));
        g.addView(h, lp(-1,-2));
        return g;
    }

    private void styleSettingsAction(Button button, int accent) {
        int visualAccent = darkroomMode ? RED : accent;
        button.setBackground(roundRect(visualAccent, 8, 0, 0));
        button.setTextColor(actionInk(visualAccent));
        button.setAlpha(1f);
    }

    private void styleSettingsToggle(Button button, boolean active, int accent) {
        styleSettingsAction(button, accent);
        button.setAlpha(active ? 1f : 0.76f);
    }
''',
    "settings visual helpers",
)
main = rep(main, 'LinearLayout timingGroup = settingsGroup("TEMPORIZZAZIONE");', 'LinearLayout timingGroup = settingsGroup("TEMPORIZZAZIONE", PROVINO_ACCENT);', "timing group")
main = rep(main, 'Button timing = compactButton("METODO DI TEMPORIZZAZIONE: " + timingMethod);', 'Button timing = compactButton("METODO DI TEMPORIZZAZIONE: " + timingMethod);\n        styleSettingsAction(timing, PROVINO_ACCENT);', "timing action")
main = rep(main, 'LinearLayout darkroomGroup = settingsGroup("CAMERA OSCURA E LUCE ROSSA");', 'LinearLayout darkroomGroup = settingsGroup("CAMERA OSCURA E LUCE ROSSA", AMBER);', "darkroom group")
main = rep(main, 'Button safelightToggle = compactButton("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));', 'Button safelightToggle = compactButton("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));\n        styleSettingsToggle(safelightToggle, safelightAuto, AMBER);', "safelight toggle")
main = rep(main, 'safelightToggle.setText("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));\n            updateSafelightStatus();', 'safelightToggle.setText("LUCE ROSSA AUTOMATICA: " + (safelightAuto ? "ON" : "OFF"));\n            styleSettingsToggle(safelightToggle, safelightAuto, AMBER);\n            updateSafelightStatus();', "safelight refresh")
main = rep(main, 'Button safePick = compactButton(safeCfg.isValid() ? "CAMBIA SONOFF SAFELIGHT" : "SCEGLI SONOFF SAFELIGHT");', 'Button safePick = compactButton(safeCfg.isValid() ? "CAMBIA SONOFF SAFELIGHT" : "SCEGLI SONOFF SAFELIGHT");\n        styleSettingsAction(safePick, AMBER);', "safelight picker")
main = rep(main, 'Button dark = compactButton("MODALITÀ CAMERA OSCURA: " + (darkroomMode ? "ON" : "OFF"));', 'Button dark = compactButton("MODALITÀ CAMERA OSCURA: " + (darkroomMode ? "ON" : "OFF"));\n        styleSettingsToggle(dark, darkroomMode, AMBER);', "darkroom toggle")
main = rep(main, 'Button protection = compactButton("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));', 'Button protection = compactButton("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));\n        styleSettingsToggle(protection, darkroomProtection, AMBER);', "notification toggle")
main = rep(main, 'protection.setText("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));\n            syncDarkroomProtection();', 'protection.setText("PROTEZIONE NOTIFICHE: " + (darkroomProtection ? "ON" : "OFF"));\n            styleSettingsToggle(protection, darkroomProtection, AMBER);\n            syncDarkroomProtection();', "notification refresh")
main = rep(main, 'authorizeDnd.setTextColor(AMBER);', 'styleSettingsAction(authorizeDnd, AMBER);', "DND permission")
main = rep(main, 'LinearLayout feedbackGroup = settingsGroup("FEEDBACK DURANTE IL LAVORO");', 'LinearLayout feedbackGroup = settingsGroup("FEEDBACK DURANTE IL LAVORO", PRINT_ACCENT);', "feedback group")
main = rep(main, 'Button beep = compactButton("BEEP FINE CICLO: " + (feedbackBeep ? "ON" : "OFF"));', 'Button beep = compactButton("BEEP FINE CICLO: " + (feedbackBeep ? "ON" : "OFF"));\n        styleSettingsToggle(beep, feedbackBeep, PRINT_ACCENT);', "beep toggle")
main = rep(main, 'beep.setOnClickListener(v -> { feedbackBeep=!feedbackBeep; getSharedPreferences("ui",MODE_PRIVATE).edit().putBoolean("feedbackBeep",feedbackBeep).apply(); beep.setText("BEEP FINE CICLO: "+(feedbackBeep?"ON":"OFF")); });', 'beep.setOnClickListener(v -> { feedbackBeep=!feedbackBeep; getSharedPreferences("ui",MODE_PRIVATE).edit().putBoolean("feedbackBeep",feedbackBeep).apply(); beep.setText("BEEP FINE CICLO: "+(feedbackBeep?"ON":"OFF")); styleSettingsToggle(beep, feedbackBeep, PRINT_ACCENT); });', "beep refresh")
main = rep(main, 'Button voice = compactButton("GUIDA VOCALE PIANO: " + (voiceGuide ? "ON" : "OFF"));', 'Button voice = compactButton("GUIDA VOCALE PIANO: " + (voiceGuide ? "ON" : "OFF"));\n        styleSettingsToggle(voice, voiceGuide, PRINT_ACCENT);', "voice toggle")
main = rep(main, 'voice.setOnClickListener(v -> { voiceGuide=!voiceGuide; getSharedPreferences("ui",MODE_PRIVATE).edit().putBoolean("voiceGuide",voiceGuide).apply(); voice.setText("GUIDA VOCALE PIANO: "+(voiceGuide?"ON":"OFF")); });', 'voice.setOnClickListener(v -> { voiceGuide=!voiceGuide; getSharedPreferences("ui",MODE_PRIVATE).edit().putBoolean("voiceGuide",voiceGuide).apply(); voice.setText("GUIDA VOCALE PIANO: "+(voiceGuide?"ON":"OFF")); styleSettingsToggle(voice, voiceGuide, PRINT_ACCENT); });', "voice refresh")
main = rep(main, 'LinearLayout diagnosticsGroup = settingsGroup("DIAGNOSTICA");', 'LinearLayout diagnosticsGroup = settingsGroup("DIAGNOSTICA", LOG_ACCENT);', "diagnostics group")
main = rep(main, 'Button diagnostics = compactButton("CRONOLOGIA TECNICA");', 'Button diagnostics = compactButton("CRONOLOGIA TECNICA");\n        styleSettingsAction(diagnostics, LOG_ACCENT);', "diagnostics action")
main = rep(main, 'LinearLayout hardwareGroup = settingsGroup("HARDWARE INGRANDITORE");', 'LinearLayout hardwareGroup = settingsGroup("HARDWARE INGRANDITORE", ENLARGEMENT_ACCENT);', "hardware group")
main = rep(main, 'Button change = compactButton(selectedDeviceId == null || selectedDeviceId.isEmpty() ? "SCEGLI SONOFF" : "CAMBIA SONOFF");', 'Button change = compactButton(selectedDeviceId == null || selectedDeviceId.isEmpty() ? "SCEGLI SONOFF" : "CAMBIA SONOFF");\n        styleSettingsAction(change, ENLARGEMENT_ACCENT);', "hardware action")
main = rep(main, 'TextView lplTitle = text("JOBO/LPL 7451 · CALIBRAZIONE COLONNA", 12, TEXT_PRIMARY, true);', 'TextView lplTitle = text("JOBO/LPL 7451 · CALIBRAZIONE COLONNA", 12, darkroomMode ? RED : ENLARGEMENT_ACCENT, true);', "calibration identity")

# Archive actions remain filled, while selected/unselected controls no longer look disabled.
main = rep(main, "        LinearLayout intro = card();\n        TextView title = text(\"ARCHIVIO DI STAMPA\", 18, TEXT_PRIMARY, true);", "        LinearLayout intro = informationCard(LOG_ACCENT);\n        TextView title = text(\"ARCHIVIO DI STAMPA\", 18, darkroomMode ? RED : LOG_ACCENT, true);", "Log intro")
main = rep(main, 'Button add = compactButton("+  NUOVA SCHEDA");', 'Button add = functionalButton("+  NUOVA SCHEDA", LOG_ACCENT);', "new Log entry")
main = rep(main, 'logSearchField.setTextSize(13);', 'logSearchField.setTextSize(13);\n        logSearchField.setBackground(roundRect(BACKGROUND, 8, 1, darkroomMode ? RED : LOG_ACCENT));', "Log search outline")
main = rep(main, 'Button exportBackup = compactButton("ESPORTA BACKUP");\n        Button importBackup = compactButton("IMPORTA BACKUP");', 'Button exportBackup = functionalButton("ESPORTA BACKUP", LOG_ACCENT);\n        Button importBackup = functionalButton("IMPORTA BACKUP", LOG_ACCENT);\n        exportBackup.setAlpha(0.84f);\n        importBackup.setAlpha(0.84f);', "Log backup actions")
main = rep(main, 'logFavoritesButton.setAlpha(logFavoritesOnly ? 1f : 0.58f);', 'logFavoritesButton.setAlpha(logFavoritesOnly ? 1f : 0.84f);', "favorite opacity")
main = rep(main, 'logGroupingButton.setAlpha(logGroupingEnabled ? 1f : 0.58f);', 'logGroupingButton.setAlpha(logGroupingEnabled ? 1f : 0.84f);', "grouping opacity")
main = rep(main, 'b.setAlpha(selected ? 1f : 0.58f);', 'b.setAlpha(selected ? 1f : 0.84f);', "Log filter opacity")
main = rep(main, "            LinearLayout empty = card();", "            LinearLayout empty = informationCard(LOG_ACCENT);", "Log empty states", 2)

# Enlargement gets a compact two-level header and an outlined derived orientation.
enlargement = rep(
    enlargement,
    "    // ENLARGEMENT_VISUAL_062 — Timer subpage identity; calculation logic is unchanged.\n",
    "    // ENLARGEMENT_VISUAL_062 — Timer subpage identity; calculation logic is unchanged.\n"
    "    // ENLARGEMENT_COMPACT_063 — compact phone header and outlined derived information.\n",
    "enlargement marker",
)
enlargement = rep(enlargement, 'begin(resize ? "RIDIMENSIONA STAMPA · JOBO/LPL 7451" : "IMPOSTA INGRANDIMENTO · JOBO/LPL 7451",', 'begin(resize ? "RIDIMENSIONA STAMPA" : "IMPOSTA INGRANDIMENTO",', "main enlargement title")
enlargement = rep(enlargement, 'begin("RIDIMENSIONA STAMPA · JOBO/LPL 7451",', 'begin("RIDIMENSIONA STAMPA",', "legacy enlargement title")
enlargement = rep(
    enlargement,
    '''        TextView landscape = label("ORIENTAMENTO · ORIZZONTALE", 12, MUTED, true);
        root.addView(landscape, margin(lp(-1, -2), 0, dp(4), 0, dp(10)));
''',
    '''        TextView landscape = label("ORIENTAMENTO · ORIZZONTALE", 12, ACCENT, true);
        landscape.setGravity(Gravity.CENTER_VERTICAL);
        landscape.setPadding(dp(13), 0, dp(13), 0);
        landscape.setBackground(bg(BG, 10, ACCENT, 1));
        root.addView(landscape, margin(lp(-1, dp(44)), 0, dp(4), 0, dp(10)));
''',
    "orientation information",
)
enlargement = rep(
    enlargement,
    '''        Button back = new Button(this);
        back.setText("‹");
        back.setTextSize(34);
        back.setTextColor(IVORY);
        back.setBackgroundColor(Color.TRANSPARENT);
        back.setContentDescription("Torna al Timer");
        back.setOnClickListener(v -> finish());
        TextView heading = label(title, 21, ACCENT, true);
        heading.setGravity(Gravity.CENTER);
        heading.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
        header.addView(back, lp(dp(52), dp(52)));
        header.addView(heading, lp(0, -2, 1f));
        header.addView(new View(this), lp(dp(52), dp(52)));
        root.addView(header, lp(-1, -2));

        TextView sub = label(subtitle, 12, MUTED, false);
        sub.setGravity(Gravity.CENTER);
        root.addView(sub, margin(lp(-1, -2), dp(20), 0, dp(20), dp(14)));
''',
    '''        Button back = new Button(this);
        back.setText("‹");
        back.setTextSize(32);
        back.setTextColor(IVORY);
        back.setBackgroundColor(Color.TRANSPARENT);
        back.setContentDescription("Torna al Timer");
        back.setOnClickListener(v -> finish());
        TextView heading = label(title, 19, ACCENT, true);
        heading.setSingleLine(true);
        heading.setGravity(Gravity.CENTER);
        heading.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
        header.addView(back, lp(dp(44), dp(48)));
        header.addView(heading, lp(0, dp(48), 1f));
        header.addView(new View(this), lp(dp(44), dp(48)));
        root.addView(header, lp(-1, dp(48)));

        TextView model = label("JOBO/LPL 7451", 11, ACCENT, true);
        model.setGravity(Gravity.CENTER);
        root.addView(model, margin(lp(-1, -2), dp(20), 0, dp(20), dp(2)));
        TextView sub = label(subtitle, 12, MUTED, false);
        sub.setGravity(Gravity.CENTER);
        root.addView(sub, margin(lp(-1, -2), dp(20), 0, dp(20), dp(12)));
''',
    "compact enlargement header",
)

# Every pre-existing operational callback and calculation entry point remains present.
for token in (
    "testStripMethod = which == 1 ? TimingMath.MASK_COVER : TimingMath.MASK_REVEAL;",
    'putString("testStripMethod", testStripMethod)',
    "showLogEditor(newEntryFromSession(), true)",
    "exportLogBackup()",
    "importLogBackup()",
    "timingMethod = TimingMath.isFStop(timingMethod)",
    "SafelightConfig.load(this)",
    "ensureSafelightIdleOn()",
    "setDarkroomModeFromSettings(!darkroomMode, dialog)",
    "darkroomProtection = !darkroomProtection",
    "showTechnicalLogDialog()",
    "showDevicePicker()",
):
    if main.count(token) != main_before.count(token):
        raise SystemExit(f"v0.6.3 Timer behaviour changed around {token}")

for token in (
    "void calculateSetup()",
    "void calculateResize(String format)",
    "Calc calc(String format, double W, double H, int fillIndex)",
    "double factor = Math.pow((c.beta+1)/(b1+1),2);",
    "static int snap(double ms) { return (int) Math.round(ms / 500.0) * 500; }",
    '.putBoolean("enlargementReloadPending", true)',
):
    if enlargement.count(token) != enlargement_before.count(token):
        raise SystemExit(f"v0.6.3 enlargement behaviour changed around {token}")

MAIN.write_text(main, encoding="utf-8")
ENLARGEMENT.write_text(enlargement, encoding="utf-8")
VISUAL.write_text(visual, encoding="utf-8")

print(f"main_source_chars_before={len(main_before)}")
print(f"main_source_chars_after={len(main)}")
print(f"enlargement_source_chars_before={len(enlargement_before)}")
print(f"enlargement_source_chars_after={len(enlargement)}")
print(f"visual_source_chars_before={len(visual_before)}")
print(f"visual_source_chars_after={len(visual)}")
print("ui_polish_063=PASS")
print("timer_process_changes=ZERO")
print("enlargement_calculation_changes=ZERO")
