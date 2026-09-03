#!/usr/bin/env python3
"""Darkroom 0.6.1: filled controls, outlined non-clickable information."""

from pathlib import Path


MAIN = Path("combined/src/main/java/it/darkroom/timer/MainActivity.java")


def rep(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)
    if found != count:
        raise SystemExit(f"v0.6.1 {label}: expected {count}, found {found}")
    return text.replace(old, new)


main = MAIN.read_text(encoding="utf-8")
if "ACTION_INFORMATION_HIERARCHY_061" in main:
    print("action_information_hierarchy_061=ALREADY_APPLIED")
    raise SystemExit(0)
if "SPLIT_PHASE_COLOURS_061" not in main:
    raise SystemExit("v0.6.1: Split phase-colour patch must run first")

main = rep(
    main,
    "    private LinearLayout actionDock;\n",
    '''    private LinearLayout actionDock;
    private LinearLayout testExposureCard;
    private LinearLayout testSettingsCard;
''',
    "dynamic information surfaces",
)

# The state strip contains information, so it never receives a filled function colour.
main = rep(main, "if (stateCard != null) stateCard.setBackground(roundRect(CARD, 12, 1, accent));", "if (stateCard != null) stateCard.setBackground(roundRect(BACKGROUND, 12, 1, accent));", "outlined state")
main = rep(main, "        stateCard = card();\n        stateCard.setPadding(dp(12), dp(8), dp(12), dp(8));", "        stateCard = informationCard(currentModeAccent());\n        stateCard.setPadding(dp(12), dp(8), dp(12), dp(8));", "initial state surface")
main = rep(main, "        deviceCard.setBackground(roundRect(CARD, 13, 1, BORDER));", "        deviceCard.setBackground(roundRect(BACKGROUND, 13, 1, darkroomMode ? BORDER : DarkroomVisualSystem.IVORY));", "outlined hardware information")
main = rep(main, "        normalButton.setTextColor(TEXT_PRIMARY);", "        normalButton.setTextColor(actionInk(RED));", "emergency action ink")
main = rep(main, "        normalButton.setBackground(roundRect(CARD, 10, 1, RED));", "        normalButton.setBackground(roundRect(RED, 10, 0, 0));", "filled emergency action")

# Main Timer information groups use outlines; their actions remain independent filled controls.
main = rep(main, "        LinearLayout box = card();\n        Button resizePrint", "        LinearLayout box = informationCard(PRINT_ACCENT);\n        Button resizePrint", "print information surface")
main = rep(main, "        LinearLayout exposure = card();\n        testPromptText", "        LinearLayout exposure = informationCard(PROVINO_ACCENT);\n        testExposureCard = exposure;\n        testPromptText", "provino information surface")
main = rep(main, "        LinearLayout settings = card();\n        settings.addView(stepperRow", "        LinearLayout settings = informationCard(PROVINO_ACCENT);\n        testSettingsCard = settings;\n        settings.addView(stepperRow", "provino settings surface")
main = rep(main, "        LinearLayout intro = card();\n        TextView title = text(\"PROVINO A CONTATTO · 35 mm\"", "        LinearLayout intro = informationCard(CONTACT_ACCENT);\n        TextView title = text(\"PROVINO A CONTATTO · 35 mm\"", "contact information surface")
main = rep(main, "        LinearLayout selected = card();\n        contact35SelectedLabel", "        LinearLayout selected = informationCard(CONTACT_ACCENT);\n        contact35SelectedLabel", "selected contact information")
main = rep(main, "        LinearLayout info = card();\n        info.setPadding(dp(12), dp(10), dp(12), dp(10));", "        LinearLayout info = informationCard(SPLIT_ACCENT);\n        info.setPadding(dp(12), dp(10), dp(12), dp(10));", "Split guide information")
main = rep(main, "        LinearLayout panel = card();\n        panel.setPadding(dp(12), dp(10), dp(12), dp(10));", "        LinearLayout panel = informationCard(SPLIT_ACCENT);\n        panel.setPadding(dp(12), dp(10), dp(12), dp(10));", "Split known-times information")

# Non-clickable badges and explanations are outlined, never filled.
main = rep(main, "        int fill = darkroomMode ? Color.BLACK : Color.rgb(31, 29, 24);\n", "", "legacy badge fill")
main = rep(main, "        badge.setBackground(roundRect(fill, compact ? 10 : 13, 1, accent));", "        badge.setBackground(roundRect(BACKGROUND, compact ? 10 : 13, 1, accent));", "outlined F-stop information")
main = rep(main, "testContrastGuide.setBackground(roundRect(darkroomMode ? Color.rgb(28,0,0) : Color.rgb(35,40,44), 9, 1, darkroomMode ? RED : BORDER));", "testContrastGuide.setBackground(roundRect(BACKGROUND, 9, 1, darkroomMode ? RED : PROVINO_ACCENT));", "outlined contrast information")
main = rep(main, "testSplitPhaseText.setBackground(roundRect(darkroomMode ? Color.rgb(24,0,0) : Color.rgb(32,36,40), 9, 1, darkroomMode ? RED : SPLIT_YELLOW_ACCENT));", "testSplitPhaseText.setBackground(roundRect(BACKGROUND, 9, 1, darkroomMode ? RED : SPLIT_YELLOW_ACCENT));", "outlined soft information")
main = rep(main, "testSplitPhaseText.setBackground(roundRect(darkroomMode ? Color.rgb(24,0,0) : Color.rgb(32,36,40), 9, 1, darkroomMode ? RED : SPLIT_MAGENTA_ACCENT));", "testSplitPhaseText.setBackground(roundRect(BACKGROUND, 9, 1, darkroomMode ? RED : SPLIT_MAGENTA_ACCENT));", "outlined hard information")

main = rep(
    main,
    '''        int flowAccent = split ? splitPhaseAccent() : PROVINO_ACCENT;
        if (testTimeText != null) testTimeText.setTextColor(flowAccent);
''',
    '''        int flowAccent = split ? splitPhaseAccent() : PROVINO_ACCENT;
        if (testExposureCard != null) testExposureCard.setBackground(roundRect(BACKGROUND, 12, 1, flowAccent));
        if (testSettingsCard != null) testSettingsCard.setBackground(roundRect(BACKGROUND, 12, 1, flowAccent));
        if (testContrastGuide != null) testContrastGuide.setBackground(roundRect(BACKGROUND, 9, 1, flowAccent));
        if (testTimeText != null) testTimeText.setTextColor(flowAccent);
''',
    "dynamic information outlines",
)

# A visible button is always a filled surface. Colour plus opacity communicates family/state.
main = rep(
    main,
    '''        if (testSingleModeButton != null) {
            boolean active = provinoFlow == PROVINO_SINGLE;
            testSingleModeButton.setBackground(roundRect(active ? BLUE : BUTTON, 9, 1, active ? BLUE : BORDER));
            testSingleModeButton.setTextColor(active ? Color.BLACK : TEXT_PRIMARY);
        }
        if (testSplitModeButton != null) {
            boolean active = split;
            testSplitModeButton.setBackground(roundRect(active ? SPLIT_ACCENT : BUTTON, 9, 1, active ? SPLIT_ACCENT : BORDER));
            testSplitModeButton.setTextColor(active ? Color.BLACK : TEXT_PRIMARY);
        }
''',
    '''        if (testSingleModeButton != null) {
            boolean active = provinoFlow == PROVINO_SINGLE;
            int accent = darkroomMode ? RED : PROVINO_ACCENT;
            testSingleModeButton.setBackground(roundRect(accent, 9, 0, 0));
            testSingleModeButton.setTextColor(actionInk(accent));
            testSingleModeButton.setAlpha(active ? 1f : 0.62f);
        }
        if (testSplitModeButton != null) {
            boolean active = split;
            int accent = darkroomMode ? RED : SPLIT_ACCENT;
            testSplitModeButton.setBackground(roundRect(accent, 9, 0, 0));
            testSplitModeButton.setTextColor(actionInk(accent));
            testSplitModeButton.setAlpha(active ? 1f : 0.62f);
        }
''',
    "filled provino selectors",
)
main = rep(main, "            testPendingChoiceButton.setTextColor(darkroomMode || provinoFlow == PROVINO_SPLIT_SOFT ? Color.BLACK : Color.WHITE);", "            testPendingChoiceButton.setTextColor(actionInk(flowAccent));", "filled choice ink")

main = rep(
    main,
    '''            b.setBackground(roundRect(selected ? BLUE : BUTTON, 9, 1, selected ? BLUE : BORDER));
            b.setTextColor(selected ? Color.BLACK : TEXT_PRIMARY);
            b.setOnClickListener''',
    '''            int accent = darkroomMode ? RED : CONTACT_ACCENT;
            b.setBackground(roundRect(accent, 9, 0, 0));
            b.setTextColor(actionInk(accent));
            b.setAlpha(selected ? 1f : 0.68f);
            b.setOnClickListener''',
    "filled contact presets",
)
main = rep(
    main,
    '''            boolean active = contact35Mode;
            contact35WorkspaceButton.setBackground(roundRect(active ? BLUE : BUTTON, 9, 1, active ? BLUE : BORDER));
            contact35WorkspaceButton.setTextColor(active ? Color.BLACK : TEXT_PRIMARY);
''',
    '''            boolean active = contact35Mode;
            int accent = darkroomMode ? RED : CONTACT_ACCENT;
            contact35WorkspaceButton.setBackground(roundRect(accent, 9, 0, 0));
            contact35WorkspaceButton.setTextColor(actionInk(accent));
            contact35WorkspaceButton.setAlpha(active ? 1f : 0.68f);
''',
    "filled contact action",
)
main = rep(
    main,
    '''        if (contact35Mode && testSingleModeButton != null) {
            testSingleModeButton.setBackground(roundRect(BUTTON, 9, 1, BORDER));
            testSingleModeButton.setTextColor(TEXT_PRIMARY);
        }
''',
    '''        if (contact35Mode && testSingleModeButton != null) {
            int accent = darkroomMode ? RED : PROVINO_ACCENT;
            testSingleModeButton.setBackground(roundRect(accent, 9, 0, 0));
            testSingleModeButton.setTextColor(actionInk(accent));
            testSingleModeButton.setAlpha(0.62f);
        }
''',
    "filled inactive single action",
)
main = rep(main, 'contact35NewPresetButton = compactButton("+  NUOVO PRESET");', 'contact35NewPresetButton = functionalButton("+  NUOVO PRESET", CONTACT_ACCENT);', "filled new preset action")

# Some legacy summaries were implemented as disabled Buttons. They keep their
# layout, but are deliberately drawn as outlined information.
main = rep(main, 'splitRow.setTextColor(Color.BLACK); splitRow.setBackground(roundRect(darkroomMode?RED:SPLIT_ACCENT,8,0,0)); splitRow.setEnabled(false);', 'splitRow.setTextColor(darkroomMode ? RED : SPLIT_ACCENT); splitRow.setBackground(roundRect(BACKGROUND,8,1,darkroomMode ? RED : SPLIT_ACCENT)); splitRow.setEnabled(false);', "outlined combined Split summary")
main = rep(main, 'Button single=compactButton(label); single.setTextColor(Color.WHITE); single.setBackground(roundRect(darkroomMode?Color.rgb(45,0,0):Color.rgb(55,60,64),8,0,0)); single.setEnabled(false);', 'Button single=compactButton(label); single.setTextColor(darkroomMode ? RED : PRINT_ACCENT); single.setBackground(roundRect(BACKGROUND,8,1,darkroomMode ? RED : PRINT_ACCENT)); single.setEnabled(false);', "outlined single-exposure summary")

# Log selectors are actions too: selection is conveyed by opacity, never by
# switching an actionable control into an outlined information style.
main = rep(
    main,
    '''        logFavoritesButton.setTextColor(logFavoritesOnly ? Color.BLACK : MUTED);
        logFavoritesButton.setBackground(roundRect(logFavoritesOnly ? accent : BUTTON, 8, logFavoritesOnly ? 0 : 1, BORDER));
''',
    '''        logFavoritesButton.setTextColor(actionInk(accent));
        logFavoritesButton.setBackground(roundRect(accent, 8, 0, 0));
        logFavoritesButton.setAlpha(logFavoritesOnly ? 1f : 0.58f);
''',
    "filled Log favorite action",
)
main = rep(
    main,
    '''        logGroupingButton.setBackground(roundRect(logGroupingEnabled ? accent : BUTTON, 8,
                logGroupingEnabled ? 0 : 1, BORDER));
        logGroupingButton.setTextColor(logGroupingEnabled
                ? (darkroomMode ? Color.BLACK : Color.WHITE)
                : MUTED);
''',
    '''        logGroupingButton.setBackground(roundRect(accent, 8, 0, 0));
        logGroupingButton.setTextColor(actionInk(accent));
        logGroupingButton.setAlpha(logGroupingEnabled ? 1f : 0.58f);
''',
    "filled Log grouping action",
)
main = rep(
    main,
    '''        b.setBackground(roundRect(selected ? accent : BUTTON, 8, selected ? 0 : 1, BORDER));
        b.setTextColor(selected ? (darkroomMode ? Color.BLACK : Color.WHITE) : MUTED);
''',
    '''        b.setBackground(roundRect(accent, 8, 0, 0));
        b.setTextColor(actionInk(accent));
        b.setAlpha(selected ? 1f : 0.58f);
''',
    "filled Log filter actions",
)
main = rep(
    main,
    '''            b35.setBackground(roundRect("35mm".equals(negative[0]) ? LOG_ACCENT : BUTTON, 8, 1, BORDER));
            b66.setBackground(roundRect("6x6".equals(negative[0]) ? LOG_ACCENT : BUTTON, 8, 1, BORDER));
            b45.setBackground(roundRect("4x5".equals(negative[0]) ? LOG_ACCENT : BUTTON, 8, 1, BORDER));
            b35.setTextColor("35mm".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
            b66.setTextColor("6x6".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
            b45.setTextColor("4x5".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
''',
    '''            int accent = darkroomMode ? RED : LOG_ACCENT;
            b35.setBackground(roundRect(accent, 8, 0, 0));
            b66.setBackground(roundRect(accent, 8, 0, 0));
            b45.setBackground(roundRect(accent, 8, 0, 0));
            b35.setTextColor(actionInk(accent));
            b66.setTextColor(actionInk(accent));
            b45.setTextColor(actionInk(accent));
            b35.setAlpha("35mm".equals(negative[0]) ? 1f : 0.58f);
            b66.setAlpha("6x6".equals(negative[0]) ? 1f : 0.58f);
            b45.setAlpha("4x5".equals(negative[0]) ? 1f : 0.58f);
''',
    "filled negative-format actions",
)
main = rep(main, "        LinearLayout auto = card();\n        auto.addView(text(\"DATI AUTOMATICI\"", "        LinearLayout auto = informationCard(LOG_ACCENT);\n        auto.addView(text(\"DATI AUTOMATICI\"", "outlined automatic Log information")
main = rep(main, "        body.setBackground(roundRect(BUTTON, 8, 1, BORDER));", "        body.setBackground(roundRect(BACKGROUND, 8, 1, darkroomMode ? RED : LOG_ACCENT));", "outlined technical Log information")
main = rep(
    main,
    '''        favoriteButton.setTextColor(favorite[0] ? AMBER : MUTED);
        favoriteButton.setBackground(roundRect(BUTTON, 8, 1, BORDER));
        favoriteButton.setOnClickListener(v -> {
            favorite[0] = !favorite[0];
            favoriteButton.setText(favorite[0] ? "★" : "☆");
            favoriteButton.setTextColor(favorite[0] ? AMBER : MUTED);
            favoriteButton.setContentDescription(favorite[0] ? "Rimuovi dai preferiti" : "Aggiungi ai preferiti");
        });
''',
    '''        int favoriteAccent = darkroomMode ? RED : AMBER;
        favoriteButton.setTextColor(actionInk(favoriteAccent));
        favoriteButton.setBackground(roundRect(favoriteAccent, 8, 0, 0));
        favoriteButton.setAlpha(favorite[0] ? 1f : 0.58f);
        favoriteButton.setOnClickListener(v -> {
            favorite[0] = !favorite[0];
            favoriteButton.setText(favorite[0] ? "★" : "☆");
            favoriteButton.setAlpha(favorite[0] ? 1f : 0.58f);
            favoriteButton.setContentDescription(favorite[0] ? "Rimuovi dai preferiti" : "Aggiungi ai preferiti");
        });
''',
    "filled per-entry favorite action",
)

# Plan summary is information: same family colour, but only as an outline.
main = rep(
    main,
    '''        printSequenceSummary.setGravity(Gravity.CENTER);
        printSequenceSummary.setPadding(dp(6), dp(6), dp(6), 0);
''',
    '''        printSequenceSummary.setGravity(Gravity.CENTER);
        printSequenceSummary.setPadding(dp(10), dp(8), dp(10), dp(8));
        printSequenceSummary.setBackground(roundRect(BACKGROUND, 9, 1, PLAN_ACCENT));
''',
    "outlined print-plan summary",
)

# Shared semantic primitives. Generic controls are still filled, but neutral.
main = rep(main, "    private LinearLayout card() {", '''    // ACTION_INFORMATION_HIERARCHY_061
    private int actionInk(int accent) {
        if (darkroomMode) return Color.BLACK;
        int luminance = (299 * Color.red(accent) + 587 * Color.green(accent) + 114 * Color.blue(accent)) / 1000;
        return luminance >= 145 ? Color.BLACK : Color.WHITE;
    }

    private LinearLayout informationCard(int accent) {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(dp(15), dp(15), dp(15), dp(15));
        l.setBackground(roundRect(BACKGROUND, 12, 1, accent));
        return l;
    }

    private LinearLayout card() {''', "semantic UI primitives")
main = rep(main, "        b.setBackground(roundRect(BUTTON, 8, 1, BORDER));\n        return b;\n    }\n\n    private Button functionalButton", "        b.setBackground(roundRect(BUTTON, 8, 0, 0));\n        return b;\n    }\n\n    private Button functionalButton", "filled generic controls")
main = rep(
    main,
    '''    private Button functionalButton(String s, int accent) {
        Button b = compactButton(s);
        b.setTextColor(accent);
        b.setBackground(roundRect(BUTTON, 10, 1, accent));
        return b;
    }
''',
    '''    private Button functionalButton(String s, int accent) {
        Button b = compactButton(s);
        b.setTextColor(actionInk(accent));
        b.setBackground(roundRect(accent, 10, 0, 0));
        return b;
    }
''',
    "filled functional controls",
)
main = rep(
    main,
    '''        b.setTextColor(accent);
        b.setAllCaps(false);
        b.setBackground(roundRect(BUTTON, 8, 0, 0));
''',
    '''        b.setTextColor(actionInk(accent));
        b.setAllCaps(false);
        b.setBackground(roundRect(accent, 8, 0, 0));
''',
    "filled time shortcuts",
)
main = rep(main, "        actionButton.setTextColor(darkroomMode || (mode == MODE_TEST && provinoFlow == PROVINO_SPLIT_SOFT) ? Color.BLACK : TEXT_PRIMARY);", "        actionButton.setTextColor(actionInk(currentModeAccent()));", "primary action ink", 2)

MAIN.write_text(main, encoding="utf-8")

for marker in (
    "ACTION_INFORMATION_HIERARCHY_061",
    "private int actionInk(int accent)",
    "private LinearLayout informationCard(int accent)",
    "b.setBackground(roundRect(accent, 10, 0, 0));",
    "stateCard.setBackground(roundRect(BACKGROUND, 12, 1, accent))",
    "printSequenceSummary.setBackground(roundRect(BACKGROUND, 9, 1, PLAN_ACCENT))",
):
    if marker not in main:
        raise SystemExit(f"v0.6.1 missing action/information marker: {marker}")

print("action_information_hierarchy_061=PASS")
print("clickable_controls=FILLED")
print("non_clickable_information=OUTLINED")
print("function_colour_pairing=CONSISTENT")
print("timer_process_changes=ZERO")
