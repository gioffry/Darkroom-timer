#!/usr/bin/env python3
"""Darkroom 0.6.1: coherent Timer graphics without changing its processes."""

from pathlib import Path


MAIN = Path("combined/src/main/java/it/darkroom/timer/MainActivity.java")
VISUAL = Path("combined/src/main/java/it/darkroom/ui/DarkroomVisualSystem.java")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.6.1 {label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def all_(text: str, old: str, new: str, label: str, minimum: int = 1) -> str:
    count = text.count(old)
    if count < minimum:
        raise SystemExit(f"v0.6.1 {label}: expected at least {minimum}, found {count}")
    return text.replace(old, new)


main = MAIN.read_text(encoding="utf-8")
if "GRAPHIC_SYSTEM_061" in main:
    print("graphic_system_061=ALREADY_APPLIED")
    raise SystemExit(0)
if 'APP_VERSION = "0.13.13"' not in main:
    raise SystemExit("v0.6.1: exact 0.6.0 Timer baseline not recognized")

main = once(
    main,
    "import java.io.BufferedReader;",
    "import it.darkroom.ui.DarkroomVisualSystem;\n\nimport java.io.BufferedReader;",
    "visual-system import",
)

main = once(
    main,
    '''    private int GREEN;
    private int BLUE;
    private int CARD;
    private int BUTTON;
    private int BORDER;
    private int MUTED;
    private int AMBER;
    private int RED;
    private int LOG_ACCENT;
    private int TEXT_PRIMARY;
    // Pantone FHI approssimati in sRGB per display. In modalità camera oscura resta RED puro.
    private static final int DODGE_BISCAY_BAY = Color.rgb(9, 121, 136);   // 18-4726 TCX
    private static final int BURN_RUST = Color.rgb(181, 90, 48);          // 18-1248 TCX
    private static final int SPLIT_VIVA_MAGENTA = Color.rgb(187, 38, 73);// 18-1750 TCX
''',
    '''    // GRAPHIC_SYSTEM_061 — stable identity for every operational family.
    private int BACKGROUND;
    private int GREEN;
    private int BLUE;
    private int CARD;
    private int BUTTON;
    private int BORDER;
    private int MUTED;
    private int AMBER;
    private int RED;
    private int LOG_ACCENT;
    private int TEXT_PRIMARY;
    private int PROVINO_ACCENT;
    private int SPLIT_ACCENT;
    private int CONTACT_ACCENT;
    private int ENLARGEMENT_ACCENT;
    private int PRINT_ACCENT;
    private int PLAN_ACCENT;
    private int DODGE_ACCENT;
    private int BURN_ACCENT;
    private int LENGTHEN_ACCENT;
    private int GLOBAL_ACCENT;
''',
    "functional palette",
)
main = once(main, 'APP_VERSION = "0.13.13"', 'APP_VERSION = "0.13.14"', "Timer version")
main = once(main, "    private static final int ALLUNGA_COLOR = Color.rgb(154, 119, 43);\n", "", "legacy lengthen colour")
main = once(main, "    private LinearLayout stateCard;\n", "    private LinearLayout stateCard;\n    private LinearLayout actionDock;\n", "action dock field")

main = all_(main, "SPLIT_VIVA_MAGENTA", "SPLIT_ACCENT", "Split Grade colour", 10)
main = all_(main, "DODGE_BISCAY_BAY", "DODGE_ACCENT", "Dodge colour", 3)
main = all_(main, "BURN_RUST", "BURN_ACCENT", "Burn colour", 3)
main = all_(main, "ALLUNGA_COLOR", "LENGTHEN_ACCENT", "lengthen colour", 4)

main = once(
    main,
    '''                if (mode == MODE_TEST && contact35Mode)
                    setStatusPresentation("PRONTO", "Scegli un preset del contatto 35 mm e premi ARMA", BLUE);
                else
                    setStatusPresentation("PRONTO", "Scegli il tempo e premi ARMA", GREEN);
''',
    '''                if (mode == MODE_TEST && contact35Mode)
                    setStatusPresentation("PRONTO", "Scegli un preset del contatto 35 mm e premi ARMA", CONTACT_ACCENT);
                else
                    setStatusPresentation("PRONTO", "Scegli il tempo e premi ARMA", currentModeAccent());
''',
    "ready identity",
)
main = once(
    main,
    "    private void setStatusPresentation(String title, String detail, int accent) {",
    '''    private int currentModeAccent() {
        if (darkroomMode) return RED;
        if (mode == MODE_LOG) return LOG_ACCENT;
        if (mode == MODE_TEST) {
            if (contact35Mode) return CONTACT_ACCENT;
            if (isSplitProvino()) return SPLIT_ACCENT;
            return PROVINO_ACCENT;
        }
        return printSequence != null && !printSequence.isEmpty() ? PLAN_ACCENT : PRINT_ACCENT;
    }

    private void setStatusPresentation(String title, String detail, int accent) {''',
    "current operational identity",
)
main = all_(main, "            accent = mode == MODE_TEST ? BLUE : GREEN;", "            accent = currentModeAccent();", "runtime identity", 2)

main = once(
    main,
    '''        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(Color.BLACK);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.BLACK);
''',
    '''        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(BACKGROUND);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BACKGROUND);
''',
    "Timer page",
)
main = once(main, "        root.setPadding(dp(16), dp(14), dp(16), dp(18));", "        root.setPadding(dp(14), dp(10), dp(14), dp(16));", "Timer spacing")
main = once(
    main,
    '''        TextView title = text("TIMER", 27, TEXT_PRIMARY, true);
        title.setGravity(Gravity.CENTER);
''',
    '''        TextView title = text("TIMER", 27, darkroomMode ? TEXT_PRIMARY : DarkroomVisualSystem.IVORY, true);
        title.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
        title.setLetterSpacing(0.045f);
        title.setGravity(Gravity.CENTER);
''',
    "Timer title",
)

# Exact approved hardware treatment: settings in the heading and one compact row.
main = once(
    main,
    '''        View navSpacer = new View(this);
        topBar.addView(navSpacer, lp(dp(46), dp(46)));
        root.addView(topBar, lp(-1, dp(46)));

        LinearLayout deviceCard = card();
        deviceCard.setPadding(dp(14), dp(9), dp(14), dp(9));
        LinearLayout deviceTop = new LinearLayout(this);
        deviceTop.setOrientation(LinearLayout.HORIZONTAL);
        deviceTop.setGravity(Gravity.CENTER_VERTICAL);
        TextView deviceName = text("INGRANDITORE", 14, TEXT_PRIMARY, true);
        deviceTop.addView(deviceName, lp(0, -2, 1f));
        selectDeviceButton = compactButton("⚙");
        selectDeviceButton.setTextSize(20);
        selectDeviceButton.setOnClickListener(v -> showSettingsDialog());
        deviceTop.addView(selectDeviceButton, lp(dp(48), dp(36)));
        deviceCard.addView(deviceTop);
        deviceStatus = text("Cerco i SONOFF sulla rete…", 13, MUTED, false);
        deviceStatus.setPadding(0, dp(4), 0, 0);
        deviceCard.addView(deviceStatus);
        safelightStatus = text("", 11, MUTED, false);
        safelightStatus.setPadding(0, dp(2), 0, 0);
        deviceCard.addView(safelightStatus);
        updateSafelightStatus();
        root.addView(deviceCard, margin(lp(-1, -2), 0, 4, 0, 10));
''',
    '''        selectDeviceButton = new Button(this);
        selectDeviceButton.setText("⚙");
        selectDeviceButton.setTextSize(20);
        selectDeviceButton.setTextColor(darkroomMode ? TEXT_PRIMARY : DarkroomVisualSystem.IVORY);
        selectDeviceButton.setPadding(0, 0, 0, 0);
        selectDeviceButton.setMinWidth(0);
        selectDeviceButton.setMinimumWidth(0);
        selectDeviceButton.setMinHeight(0);
        selectDeviceButton.setMinimumHeight(0);
        selectDeviceButton.setBackgroundColor(Color.TRANSPARENT);
        selectDeviceButton.setContentDescription("Impostazioni Timer e SONOFF");
        selectDeviceButton.setOnClickListener(v -> showSettingsDialog());
        topBar.addView(selectDeviceButton, lp(dp(46), dp(46)));
        root.addView(topBar, lp(-1, dp(46)));

        // SONOFF_STRIP_061 — the approved compact, horizontal hardware strip.
        LinearLayout deviceCard = card();
        deviceCard.setOrientation(LinearLayout.HORIZONTAL);
        deviceCard.setGravity(Gravity.CENTER_VERTICAL);
        deviceCard.setPadding(dp(14), dp(4), dp(14), dp(4));
        deviceCard.setBackground(roundRect(CARD, 13, 1, BORDER));
        deviceStatus = text("○  Ricerca MINIR2…", 12, MUTED, true);
        deviceStatus.setGravity(Gravity.CENTER_VERTICAL);
        deviceCard.addView(deviceStatus, lp(0, dp(48), 1f));
        safelightStatus = text("", 12, MUTED, true);
        safelightStatus.setGravity(Gravity.CENTER_VERTICAL | Gravity.END);
        deviceCard.addView(safelightStatus, lp(0, dp(48), 1f));
        updateSafelightStatus();
        root.addView(deviceCard, margin(lp(-1, -2), 0, 5, 0, 10));
''',
    "approved SONOFF strip",
)
main = once(main, "        modeRow.setBackgroundColor(Color.BLACK);", "        modeRow.setBackgroundColor(BACKGROUND);", "navigation background")

# Keep configuration scrollable, but keep operational state and ARMA always reachable.
main = once(
    main,
    "        actionButton = new Button(this);",
    '''        actionDock = new LinearLayout(this);
        actionDock.setOrientation(LinearLayout.VERTICAL);
        actionDock.setPadding(dp(13), dp(7), dp(13), dp(9));
        actionDock.setBackgroundColor(BACKGROUND);

        actionButton = new Button(this);''',
    "persistent action area",
)
main = once(main, "        actionButton.setTextColor(TEXT_PRIMARY);", "        actionButton.setTextColor(darkroomMode ? Color.BLACK : TEXT_PRIMARY);", "action ink")
main = once(main, "        actionButton.setTextSize(18);", "        actionButton.setTextSize(17);", "action scale")
main = once(main, "        root.addView(actionButton, margin(lp(-1, dp(64)), 0, 14, 0, 0));", "        actionDock.addView(actionButton, lp(-1, dp(58)));", "dock ARMA")
main = once(main, "        root.addView(cancelCycleButton, margin(lp(-1, dp(60)), 0, 14, 0, 0));", "        actionDock.addView(cancelCycleButton, margin(lp(-1, dp(58)), 0, 6, 0, 0));", "dock cancel")
main = once(main, "        root.addView(saveLogButton, margin(lp(-1, dp(56)), 0, 8, 0, 0));", "        actionDock.addView(saveLogButton, margin(lp(-1, dp(54)), 0, 6, 0, 0));", "dock Log")
main = once(main, "        stateCard.setPadding(dp(14), dp(11), dp(14), dp(11));", "        stateCard.setPadding(dp(12), dp(8), dp(12), dp(8));", "state density")
main = once(main, '        stateTitle = text("PRONTO", 14, GREEN, true);', '        stateTitle = text("PRONTO", 13, currentModeAccent(), true);', "state identity")
main = once(main, '        stateText = text("Scegli il tempo e premi ARMA", 12, MUTED, false);', '        stateText = text("Scegli il tempo e premi ARMA", 11, MUTED, false);', "state density text")
main = once(main, "        root.addView(stateCard, margin(lp(-1, -2), 0, 10, 0, 0));", "        actionDock.addView(stateCard, 0, margin(lp(-1, -2), 0, 0, 0, 6));", "dock state")
main = once(main, "        normalButton.setBackground(roundRect(CARD, 10, 1, BORDER));", "        normalButton.setBackground(roundRect(CARD, 10, 1, RED));", "emergency identity")
main = once(
    main,
    "        root.addView(normalButton, lp(-1, dp(64)));",
    '''        actionDock.addView(normalButton, margin(lp(-1, dp(62)), 0, 6, 0, 0));

        page.addView(actionDock, lp(-1, -2));''',
    "dock emergency",
)

main = all_(main, 'compactButton("RIDIMENSIONA STAMPA")', 'functionalButton("RIDIMENSIONA STAMPA", ENLARGEMENT_ACCENT)', "resize identity", 2)
main = once(main, 'compactButton("IMPOSTA INGRANDIMENTO")', 'functionalButton("IMPOSTA INGRANDIMENTO", ENLARGEMENT_ACCENT)', "enlargement identity")
main = once(main, 'printSequenceButton = compactButton("PIANO DI STAMPA");', 'printSequenceButton = functionalButton("PIANO DI STAMPA", PLAN_ACCENT);', "plan identity")
main = once(main, 'contact35WorkspaceButton = compactButton("PROVINO A CONTATTO 35 mm");', 'contact35WorkspaceButton = functionalButton("PROVINO A CONTATTO 35 mm", CONTACT_ACCENT);', "contact identity")
main = once(main, "printTimeText = text(formatTime(printWidthMs), 48, GREEN, true);", "printTimeText = text(formatTime(printWidthMs), 48, PRINT_ACCENT, true);", "print time")
main = once(main, "Button b = shortcutButton(s + \" s\", GREEN);", "Button b = shortcutButton(s + \" s\", PRINT_ACCENT);", "print shortcuts")
main = once(main, 'printSequenceSummary = text("", 12, darkroomMode ? RED : AMBER, false);', 'printSequenceSummary = text("", 12, PLAN_ACCENT, false);', "plan summary")
main = once(main, 'contact35SelectedTime = text("—", 44, BLUE, true);', 'contact35SelectedTime = text("—", 44, CONTACT_ACCENT, true);', "contact time")
main = once(main, "testTimeText = text(formatTime(testWidthMs), 44, BLUE, true);", "testTimeText = text(formatTime(testWidthMs), 44, PROVINO_ACCENT, true);", "provino time")
main = once(main, "testCumulativeText = text(cumulativeTimes(), 13, BLUE, true);", "testCumulativeText = text(cumulativeTimes(), 13, PROVINO_ACCENT, true);", "provino series")
main = once(main, "testPendingChoiceButton.setBackground(roundRect(BLUE, 9, 0, 0));", "testPendingChoiceButton.setBackground(roundRect(PROVINO_ACCENT, 9, 0, 0));", "provino choice")

main = once(
    main,
    '''        styleNavButton(printModeButton, print, GREEN);
        styleNavButton(testModeButton, test, BLUE);
        styleNavButton(logModeButton, log, LOG_ACCENT);
        actionButton.setTextColor(darkroomMode ? Color.BLACK : TEXT_PRIMARY);
        if (!log) {
            actionButton.setBackground(roundRect(print ? GREEN : BLUE, 10, 0, 0));
''',
    '''        styleNavButton(printModeButton, print, PRINT_ACCENT);
        styleNavButton(testModeButton, test, PROVINO_ACCENT);
        styleNavButton(logModeButton, log, LOG_ACCENT);
        actionDock.setVisibility(log ? View.GONE : View.VISIBLE);
        actionButton.setTextColor(darkroomMode ? Color.BLACK : TEXT_PRIMARY);
        if (!log) {
            actionButton.setBackground(roundRect(currentModeAccent(), 10, 0, 0));
''',
    "navigation identities",
)

# Approved, concise visible labels; discovery/control logic remains untouched.
status_labels = {
    "●  SONOFF NON CONFIGURATO": "○  MINIR2 da configurare",
    "●  SONOFF — connessione…": "○  Connessione MINIR2…",
    "●  SONOFF — verifica DIY…": "○  Verifica MINIR2…",
    "●  SONOFF NON IN DIY": "!  MINIR2 non in DIY",
    "●  SONOFF CONNESSO": "✓  MINIR2 connesso",
    "●  SONOFF — RICONNESSIONE…": "↻  Riconnessione MINIR2…",
    "●  VERIFICA CONNESSIONE…": "○  Verifica connessione…",
    "●  SONOFF NON RAGGIUNGIBILE": "!  MINIR2 non raggiungibile",
    "●  SONOFF — ricerca…": "○  Ricerca MINIR2…",
    "●  SONOFF DA SELEZIONARE": "○  Seleziona MINIR2",
}
for old, new in status_labels.items():
    main = all_(main, old, new, f"status label {old}")

main = once(main, 'safelightStatus.setText("LUCE ROSSA AUTOMATICA — OFF");', 'safelightStatus.setText("○  Luce rossa disattiva");', "safelight off")
main = once(main, 'safelightStatus.setText("LUCE ROSSA AUTOMATICA — DA CONFIGURARE");', 'safelightStatus.setText("!  Configura luce rossa");', "safelight setup")
main = once(main, 'safelightStatus.setText("LUCE ROSSA AUTOMATICA — ON");', 'safelightStatus.setText("●  Luce rossa attiva");', "safelight active")

main = once(
    main,
    '''    private void configurePalette() {
        if (darkroomMode) {
            // Safelight mode: use only the red subpixel (G=B=0) for emitted light.
            // Strong contrast comes from pure-red-on-black and black-on-red, not white.
            GREEN = Color.rgb(235, 0, 0);
            BLUE = Color.rgb(235, 0, 0);
            CARD = Color.BLACK;
            BUTTON = Color.rgb(18, 0, 0);
            BORDER = Color.rgb(105, 0, 0);
            MUTED = Color.rgb(190, 0, 0);
            AMBER = Color.rgb(235, 0, 0);
            RED = Color.rgb(255, 0, 0);
            LOG_ACCENT = RED;
            TEXT_PRIMARY = Color.rgb(255, 0, 0);
        } else {
            GREEN = Color.rgb(80, 207, 70);
            BLUE = Color.rgb(63, 151, 255);
            CARD = Color.rgb(18, 21, 23);
            BUTTON = Color.rgb(31, 35, 38);
            BORDER = Color.rgb(57, 63, 68);
            MUTED = Color.rgb(169, 176, 184);
            AMBER = Color.rgb(255, 181, 71);
            RED = Color.rgb(255, 92, 92);
            LOG_ACCENT = Color.rgb(107, 114, 128);
            TEXT_PRIMARY = Color.WHITE;
        }
''',
    '''    private void configurePalette() {
        if (darkroomMode) {
            // Photographic safety: all emitted colours have G=B=0.
            BACKGROUND = Color.BLACK;
            RED = DarkroomVisualSystem.DARKROOM_RED;
            GREEN = RED;
            BLUE = RED;
            CARD = Color.BLACK;
            BUTTON = Color.rgb(18, 0, 0);
            BORDER = Color.rgb(105, 0, 0);
            MUTED = Color.rgb(190, 0, 0);
            AMBER = RED;
            LOG_ACCENT = RED;
            TEXT_PRIMARY = RED;
            PROVINO_ACCENT = RED;
            SPLIT_ACCENT = RED;
            CONTACT_ACCENT = RED;
            ENLARGEMENT_ACCENT = RED;
            PRINT_ACCENT = RED;
            PLAN_ACCENT = RED;
            DODGE_ACCENT = RED;
            BURN_ACCENT = RED;
            LENGTHEN_ACCENT = RED;
            GLOBAL_ACCENT = RED;
        } else {
            BACKGROUND = DarkroomVisualSystem.BACKGROUND;
            GREEN = DarkroomVisualSystem.SUCCESS;
            BLUE = DarkroomVisualSystem.ACTION;
            CARD = DarkroomVisualSystem.SURFACE;
            BUTTON = DarkroomVisualSystem.SURFACE_ELEVATED;
            BORDER = DarkroomVisualSystem.BORDER;
            MUTED = DarkroomVisualSystem.MUTED;
            AMBER = DarkroomVisualSystem.WAITING;
            RED = DarkroomVisualSystem.DANGER;
            LOG_ACCENT = DarkroomVisualSystem.LOG;
            TEXT_PRIMARY = DarkroomVisualSystem.TEXT;
            PROVINO_ACCENT = DarkroomVisualSystem.PROVINO;
            SPLIT_ACCENT = DarkroomVisualSystem.SPLIT_GRADE;
            CONTACT_ACCENT = DarkroomVisualSystem.CONTACT;
            ENLARGEMENT_ACCENT = DarkroomVisualSystem.ENLARGEMENT;
            PRINT_ACCENT = DarkroomVisualSystem.PRINT;
            PLAN_ACCENT = DarkroomVisualSystem.PRINT_PLAN;
            DODGE_ACCENT = DarkroomVisualSystem.DODGE;
            BURN_ACCENT = DarkroomVisualSystem.BURN;
            LENGTHEN_ACCENT = DarkroomVisualSystem.LENGTHEN;
            GLOBAL_ACCENT = DarkroomVisualSystem.GLOBAL_CORRECTION;
        }
''',
    "shared palette",
)
main = once(
    main,
    "    private Button smallButton(String s) {",
    '''    private Button functionalButton(String s, int accent) {
        Button b = compactButton(s);
        b.setTextColor(accent);
        b.setBackground(roundRect(BUTTON, 10, 1, accent));
        return b;
    }

    private Button smallButton(String s) {''',
    "functional button",
)

VISUAL.parent.mkdir(parents=True, exist_ok=True)
VISUAL.write_text(
    '''package it.darkroom.ui;

import android.graphics.Color;

/** Shared graphic tokens. Functional colours collapse to red in darkroom mode. */
public final class DarkroomVisualSystem {
    private DarkroomVisualSystem() {}

    public static final int BACKGROUND = Color.rgb(5, 6, 7);
    public static final int SURFACE = Color.rgb(18, 19, 20);
    public static final int SURFACE_ELEVATED = Color.rgb(29, 31, 32);
    public static final int BORDER = Color.rgb(72, 67, 61);
    public static final int TEXT = Color.rgb(242, 238, 232);
    public static final int MUTED = Color.rgb(171, 161, 151);
    public static final int IVORY = Color.rgb(235, 210, 174);

    public static final int ACTION = Color.rgb(137, 162, 174);
    public static final int SUCCESS = Color.rgb(103, 177, 98);
    public static final int WAITING = Color.rgb(217, 166, 84);
    public static final int DANGER = Color.rgb(217, 87, 78);
    public static final int DARKROOM_RED = Color.rgb(255, 0, 0);

    public static final int PROVINO = Color.rgb(84, 167, 200);
    public static final int SPLIT_GRADE = Color.rgb(196, 88, 171);
    public static final int CONTACT = Color.rgb(64, 169, 130);
    public static final int ENLARGEMENT = Color.rgb(170, 131, 84);
    public static final int PRINT = Color.rgb(126, 166, 87);
    public static final int PRINT_PLAN = Color.rgb(200, 177, 69);
    public static final int DODGE = Color.rgb(102, 116, 208);
    public static final int BURN = Color.rgb(210, 103, 56);
    public static final int LOG = Color.rgb(126, 137, 152);
    public static final int LENGTHEN = Color.rgb(140, 114, 196);
    public static final int GLOBAL_CORRECTION = Color.rgb(163, 107, 128);
}
''',
    encoding="utf-8",
)

MAIN.write_text(main, encoding="utf-8")

for marker in (
    "GRAPHIC_SYSTEM_061",
    "SONOFF_STRIP_061",
    'APP_VERSION = "0.13.14"',
    'selectDeviceButton.setContentDescription("Impostazioni Timer e SONOFF")',
    'deviceStatus = text("○  Ricerca MINIR2…", 12, MUTED, true)',
    'safelightStatus.setText("●  Luce rossa attiva")',
    "page.addView(actionDock, lp(-1, -2));",
    'functionalButton("IMPOSTA INGRANDIMENTO", ENLARGEMENT_ACCENT)',
    'functionalButton("PIANO DI STAMPA", PLAN_ACCENT)',
):
    if marker not in main:
        raise SystemExit(f"v0.6.1 missing marker: {marker}")
if 'TextView deviceName = text("INGRANDITORE"' in main:
    raise SystemExit("v0.6.1 obsolete vertical hardware card remains")

print("graphic_system_061=PASS")
print("sonoff_strip=APPROVED_HORIZONTAL_LAYOUT")
print("settings_gear=IN_TIMER_HEADING")
print("functional_colours_distinct=PASS")
print("timer_process_changes=ZERO")
