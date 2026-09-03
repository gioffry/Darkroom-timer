#!/usr/bin/env python3
"""Darkroom 0.6.1: Split Grade owns a neutral identity; Y/M own their phases."""

from pathlib import Path


MAIN = Path("combined/src/main/java/it/darkroom/timer/MainActivity.java")
VISUAL = Path("combined/src/main/java/it/darkroom/ui/DarkroomVisualSystem.java")


def rep(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)
    if found != count:
        raise SystemExit(f"v0.6.1 {label}: expected {count}, found {found}")
    return text.replace(old, new)


main = MAIN.read_text(encoding="utf-8")
visual = VISUAL.read_text(encoding="utf-8")
if "SPLIT_PHASE_COLOURS_061" in main:
    print("split_phase_colours_061=ALREADY_APPLIED")
    raise SystemExit(0)
if "TIMER_IDENTITY_061" not in main:
    raise SystemExit("v0.6.1: Timer identity patch must run first")

main = rep(
    main,
    "    private int SPLIT_ACCENT;\n",
    "    private int SPLIT_ACCENT;\n    private int SPLIT_YELLOW_ACCENT;\n    private int SPLIT_MAGENTA_ACCENT;\n",
    "Split phase palette fields",
)
main = rep(
    main,
    '''    // TIMER_IDENTITY_061 — one stable colour for each operational family.
    private int currentModeAccent() {
''',
    '''    // TIMER_IDENTITY_061 — one stable colour for each operational family.
    // SPLIT_PHASE_COLOURS_061 — process identity is neutral; active work follows Y or M.
    private int splitPhaseAccent() {
        if (darkroomMode) return RED;
        return provinoFlow == PROVINO_SPLIT_HARD ? SPLIT_MAGENTA_ACCENT : SPLIT_YELLOW_ACCENT;
    }

    private int currentModeAccent() {
''',
    "Split phase helper",
)
main = rep(main, "            if (isSplitProvino()) return SPLIT_ACCENT;", "            if (isSplitProvino()) return splitPhaseAccent();", "active Split phase identity")

# The selector and combined recipes retain the neutral process identity.
main = rep(main, "            testSplitModeButton.setTextColor(active ? Color.WHITE : TEXT_PRIMARY);", "            testSplitModeButton.setTextColor(active ? Color.BLACK : TEXT_PRIMARY);", "Split selector contrast")
main = rep(main, "        int flowAccent = split ? SPLIT_ACCENT : PROVINO_ACCENT;", "        int flowAccent = split ? splitPhaseAccent() : PROVINO_ACCENT;", "active Split controls")
main = rep(main, "            testPendingChoiceButton.setTextColor(darkroomMode ? Color.BLACK : Color.WHITE);", "            testPendingChoiceButton.setTextColor(darkroomMode || provinoFlow == PROVINO_SPLIT_SOFT ? Color.BLACK : Color.WHITE);", "active phase action ink")
main = rep(main, "        actionButton.setTextColor(darkroomMode ? Color.BLACK : TEXT_PRIMARY);", "        actionButton.setTextColor(darkroomMode || (mode == MODE_TEST && provinoFlow == PROVINO_SPLIT_SOFT) ? Color.BLACK : TEXT_PRIMARY);", "ARMA phase ink", 2)
main = rep(main, "        testSplitPhaseText = text(\"\", 14, SPLIT_ACCENT, true);", "        testSplitPhaseText = text(\"\", 14, SPLIT_YELLOW_ACCENT, true);", "initial Split phase label")

# Phase 1 is physically yellow; phase 2 is physically magenta.
main = rep(main, "darkroomMode ? RED : AMBER));", "darkroomMode ? RED : SPLIT_YELLOW_ACCENT));", "soft phase card", 1)
main = rep(main, "darkroomMode ? RED : SPLIT_ACCENT));", "darkroomMode ? RED : SPLIT_MAGENTA_ACCENT));", "hard phase card", 1)
main = rep(main, 'TextView yv=text(sy[0]+"Y / 0M",22,SPLIT_ACCENT,true);', 'TextView yv=text(sy[0]+"Y / 0M",22,SPLIT_YELLOW_ACCENT,true);', "known soft filter")
main = rep(main, "TextView stv=text(formatTime(sm[0]),24,SPLIT_ACCENT,true);", "TextView stv=text(formatTime(sm[0]),24,SPLIT_YELLOW_ACCENT,true);", "known soft time")
main = rep(main, 'TextView mv=text("0Y / "+hm[0]+"M",22,SPLIT_ACCENT,true);', 'TextView mv=text("0Y / "+hm[0]+"M",22,SPLIT_MAGENTA_ACCENT,true);', "known hard filter")
main = rep(main, "TextView htv=text(formatTime(ht[0]),24,SPLIT_ACCENT,true);", "TextView htv=text(formatTime(ht[0]),24,SPLIT_MAGENTA_ACCENT,true);", "known hard time")
main = rep(main, "int accent = ExposureRecipe.FILTER_MAGENTA.equals(type) ? SPLIT_ACCENT : AMBER;", "int accent = ExposureRecipe.FILTER_MAGENTA.equals(type) ? SPLIT_MAGENTA_ACCENT : SPLIT_YELLOW_ACCENT;", "filter editor identity")

main = rep(main, 'setStatusPresentation("SPLIT GRADE — FASE 1 DI 2", "Trova sperimentalmente il tempo morbido. Nessuna conversione automatica.", SPLIT_ACCENT);', 'setStatusPresentation("SPLIT GRADE — FASE 1 DI 2", "Trova sperimentalmente il tempo morbido. Nessuna conversione automatica.", SPLIT_YELLOW_ACCENT);', "phase one status")
main = rep(main, '''        setStatusPresentation("SPLIT GRADE — FASE 2 DI 2",
                "Usa una nuova striscia. Il morbido scelto verrà applicato prima su tutta la carta; poi partirà il provino duro.", SPLIT_ACCENT);''', '''        setStatusPresentation("SPLIT GRADE — FASE 2 DI 2",
                "Usa una nuova striscia. Il morbido scelto verrà applicato prima su tutta la carta; poi partirà il provino duro.", SPLIT_MAGENTA_ACCENT);''', "phase two status")
main = rep(main, 'setStatusPresentation("RIVEDI IL MORBIDO", "La precedente scelta dura è stata invalidata e deve essere ricontrollata.", SPLIT_ACCENT);', 'setStatusPresentation("RIVEDI IL MORBIDO", "La precedente scelta dura è stata invalidata e deve essere ricontrollata.", SPLIT_YELLOW_ACCENT);', "review soft status")
main = rep(main, '"Morbido conservato. Modifica tempo centrale, intervallo o magenta; usa una nuova striscia e premi ARMA.", SPLIT_ACCENT);', '"Morbido conservato. Modifica tempo centrale, intervallo o magenta; usa una nuova striscia e premi ARMA.", SPLIT_MAGENTA_ACCENT);', "redo hard status")
main = rep(main, '"Modifica tempo, intervallo o giallo e ripeti il provino. Nessuna stampa è stata creata.", SPLIT_ACCENT);', '"Modifica tempo, intervallo o giallo e ripeti il provino. Nessuna stampa è stata creata.", SPLIT_YELLOW_ACCENT);', "redo soft status")

# The transition explicitly targets the M phase; the final plan again represents both.
main = rep(main, 'next.setBackground(roundRect(SPLIT_ACCENT,9,0,0)); next.setTextColor(Color.WHITE);', 'next.setBackground(roundRect(SPLIT_MAGENTA_ACCENT,9,0,0)); next.setTextColor(Color.WHITE);', "continue to hard action")
main = rep(main, 'create.setBackground(roundRect(SPLIT_ACCENT,9,0,0)); create.setTextColor(Color.WHITE);', 'create.setBackground(roundRect(SPLIT_ACCENT,9,0,0)); create.setTextColor(Color.BLACK);', "create combined plan action")
main = rep(main, 'Button save=compactButton("SALVA TEMPI SPLIT GRADE"); save.setTextColor(Color.WHITE); save.setBackground(roundRect(SPLIT_ACCENT,9,0,0));', 'Button save=compactButton("SALVA TEMPI SPLIT GRADE"); save.setTextColor(Color.BLACK); save.setBackground(roundRect(SPLIT_ACCENT,9,0,0));', "save combined Split recipe")
main = rep(main, 'splitRow.setTextColor(Color.WHITE); splitRow.setBackground(roundRect(darkroomMode?RED:SPLIT_ACCENT,8,0,0));', 'splitRow.setTextColor(Color.BLACK); splitRow.setBackground(roundRect(darkroomMode?RED:SPLIT_ACCENT,8,0,0));', "combined Split summary")
main = rep(main, 'guided.setTextColor(Color.WHITE); guided.setBackground(roundRect(SPLIT_ACCENT,8,0,0));', 'guided.setTextColor(Color.BLACK); guided.setBackground(roundRect(SPLIT_ACCENT,8,0,0));', "start Split process")

main = rep(main, "            SPLIT_ACCENT = RED;\n", "            SPLIT_ACCENT = RED;\n            SPLIT_YELLOW_ACCENT = RED;\n            SPLIT_MAGENTA_ACCENT = RED;\n", "darkroom Split phase palette")
main = rep(main, "            SPLIT_ACCENT = DarkroomVisualSystem.SPLIT_GRADE;\n", "            SPLIT_ACCENT = DarkroomVisualSystem.SPLIT_GRADE;\n            SPLIT_YELLOW_ACCENT = DarkroomVisualSystem.SPLIT_YELLOW;\n            SPLIT_MAGENTA_ACCENT = DarkroomVisualSystem.SPLIT_MAGENTA;\n", "normal Split phase palette")

visual = rep(
    visual,
    "    public static final int SPLIT_GRADE = Color.rgb(196, 88, 171);\n",
    '''    // The process is neutral because it contains both filtration channels.
    public static final int SPLIT_GRADE = Color.rgb(173, 167, 184);
    public static final int SPLIT_YELLOW = Color.rgb(214, 178, 73);
    public static final int SPLIT_MAGENTA = Color.rgb(196, 88, 171);
''',
    "Split palette semantics",
)

MAIN.write_text(main, encoding="utf-8")
VISUAL.write_text(visual, encoding="utf-8")

for marker in (
    "SPLIT_PHASE_COLOURS_061",
    "private int splitPhaseAccent()",
    "int flowAccent = split ? splitPhaseAccent() : PROVINO_ACCENT;",
    "SPLIT_YELLOW_ACCENT = DarkroomVisualSystem.SPLIT_YELLOW;",
    "SPLIT_MAGENTA_ACCENT = DarkroomVisualSystem.SPLIT_MAGENTA;",
):
    if marker not in main:
        raise SystemExit(f"v0.6.1 missing phase marker: {marker}")
if "SPLIT_GRADE = Color.rgb(196, 88, 171)" in visual:
    raise SystemExit("v0.6.1 Split Grade process is still magenta")

print("split_phase_colours_061=PASS")
print("split_process=NEUTRAL_SILVER_VIOLET")
print("split_phase_1=YELLOW")
print("split_phase_2=MAGENTA")
print("darkroom_palette=RED_ONLY")
