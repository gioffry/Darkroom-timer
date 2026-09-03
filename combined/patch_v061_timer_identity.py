#!/usr/bin/env python3
"""Darkroom 0.6.1: apply each functional identity consistently in Timer."""

from pathlib import Path


MAIN = Path("combined/src/main/java/it/darkroom/timer/MainActivity.java")


def rep(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)
    if found != count:
        raise SystemExit(f"v0.6.1 {label}: expected {count}, found {found}")
    return text.replace(old, new)


main = MAIN.read_text(encoding="utf-8")
if "TIMER_IDENTITY_061" in main:
    print("timer_identity_061=ALREADY_APPLIED")
    raise SystemExit(0)
if "GRAPHIC_SYSTEM_061" not in main:
    raise SystemExit("v0.6.1: graphic-system patch must run first")

main = rep(main, "    private int currentModeAccent() {", "    // TIMER_IDENTITY_061 — one stable colour for each operational family.\n    private int currentModeAccent() {", "identity marker")

main = rep(main, "                    accent = BLUE;\n                    transientCompletion = true;\n                    refreshPendingTestStripChoiceUi();", "                    accent = CONTACT_ACCENT;\n                    transientCompletion = true;\n                    refreshPendingTestStripChoiceUi();", "contact completion")
main = rep(main, "                    accent = BLUE;\n                    transientCompletion = true;\n                    new Handler", "                    accent = currentModeAccent();\n                    transientCompletion = true;\n                    new Handler", "provino completion")
main = rep(main, "                accent = GREEN;\n                transientCompletion = true;\n            } else if (detail.toLowerCase(Locale.ITALY).contains(\"provino completato\"))", "                accent = currentModeAccent();\n                transientCompletion = true;\n            } else if (detail.toLowerCase(Locale.ITALY).contains(\"provino completato\"))", "print completion")
main = rep(main, "                    accent = GREEN;\n                } else {\n                    title = \"ATTESA SONOFF\";", "                    accent = currentModeAccent();\n                } else {\n                    title = \"ATTESA SONOFF\";", "ready runtime")

for old, new, label in (
    ('''        setStatusPresentation("RIFAI PROVINO SINGOLO",
                "Filtro e tempo correnti sono solo valori iniziali modificabili. La ricetta precedente resta intatta finché non scegli una nuova striscia.", BLUE);''', '''        setStatusPresentation("RIFAI PROVINO SINGOLO",
                "Filtro e tempo correnti sono solo valori iniziali modificabili. La ricetta precedente resta intatta finché non scegli una nuova striscia.", PROVINO_ACCENT);''', "single revision"),
    ('''        setStatusPresentation("SPLIT GRADE — TROVA I TEMPI",
                "Il tempo singolo precedente è usato solo per suggerire un centro iniziale T/2, liberamente modificabile. Non è una conversione né una compensazione.", BLUE);''', '''        setStatusPresentation("SPLIT GRADE — TROVA I TEMPI",
                "Il tempo singolo precedente è usato solo per suggerire un centro iniziale T/2, liberamente modificabile. Non è una conversione né una compensazione.", SPLIT_ACCENT);''', "Split start"),
    ('''                hardOnly
                        ? "Il morbido corrente resta valido e verrà applicato su tutta la nuova striscia. Il vecchio duro è solo il centro iniziale modificabile."
                        : "Riparti dal morbido con i valori correnti come riferimento. La vecchia coppia resta intatta finché il nuovo procedimento non è completato.",
                BLUE);''', '''                hardOnly
                        ? "Il morbido corrente resta valido e verrà applicato su tutta la nuova striscia. Il vecchio duro è solo il centro iniziale modificabile."
                        : "Riparti dal morbido con i valori correnti come riferimento. La vecchia coppia resta intatta finché il nuovo procedimento non è completato.",
                SPLIT_ACCENT);''', "Split revision"),
):
    main = rep(main, old, new, label)

simple = (
    ('setStatusPresentation("SPLIT GRADE — FASE 1 DI 2", "Trova sperimentalmente il tempo morbido. Nessuna conversione automatica.", BLUE);', 'setStatusPresentation("SPLIT GRADE — FASE 1 DI 2", "Trova sperimentalmente il tempo morbido. Nessuna conversione automatica.", SPLIT_ACCENT);', "Split phase one"),
    ('setStatusPresentation("PROVINO SINGOLO", "Valori precedenti ripristinati. Nessuna ricetta di stampa modificata.", BLUE);', 'setStatusPresentation("PROVINO SINGOLO", "Valori precedenti ripristinati. Nessuna ricetta di stampa modificata.", PROVINO_ACCENT);', "single restore"),
    ('setStatusPresentation("RIVEDI IL MORBIDO", "La precedente scelta dura è stata invalidata e deve essere ricontrollata.", BLUE);', 'setStatusPresentation("RIVEDI IL MORBIDO", "La precedente scelta dura è stata invalidata e deve essere ricontrollata.", SPLIT_ACCENT);', "review soft"),
    ('"Morbido conservato. Modifica tempo centrale, intervallo o magenta; usa una nuova striscia e premi ARMA.", BLUE);', '"Morbido conservato. Modifica tempo centrale, intervallo o magenta; usa una nuova striscia e premi ARMA.", SPLIT_ACCENT);', "redo hard"),
    ('"Modifica tempo, intervallo o giallo e ripeti il provino. Nessuna stampa è stata creata.", BLUE);', '"Modifica tempo, intervallo o giallo e ripeti il provino. Nessuna stampa è stata creata.", SPLIT_ACCENT);', "reset soft"),
    ('setStatusPresentation("PROVINO A CONTATTO 35 mm", "Crea un nuovo preset oppure richiamane uno già salvato", BLUE);', 'setStatusPresentation("PROVINO A CONTATTO 35 mm", "Crea un nuovo preset oppure richiamane uno già salvato", CONTACT_ACCENT);', "contact empty"),
    ('setStatusPresentation("CONTATTO 35 mm — " + selected.title(), selected.setupLine(), BLUE);', 'setStatusPresentation("CONTATTO 35 mm — " + selected.title(), selected.setupLine(), CONTACT_ACCENT);', "contact selected"),
    ('setStatusPresentation("CONTATTO 35 mm — " + preset.title(), preset.setupLine(), BLUE);', 'setStatusPresentation("CONTATTO 35 mm — " + preset.title(), preset.setupLine(), CONTACT_ACCENT);', "contact preset"),
    ('testSplitPhaseText = text("", 14, BLUE, true);', 'testSplitPhaseText = text("", 14, SPLIT_ACCENT, true);', "Split phase label"),
    ('setStatusPresentation("CONTATTO 35 mm", "Seleziona prima un preset", BLUE);', 'setStatusPresentation("CONTATTO 35 mm", "Seleziona prima un preset", CONTACT_ACCENT);', "contact validation"),
    ('final TextView selectedText = text("Nessuna striscia selezionata", 12, BLUE, true);', 'final TextView selectedText = text("Nessuna striscia selezionata", 12, currentModeAccent(), true);', "provino selection"),
    ('setStatusPresentation("REIMPOSTA PROVINO", "Modifica filtrazione, tempo, passo o numero di strisce e ripeti. Nessuna stampa è stata creata.", BLUE);', 'setStatusPresentation("REIMPOSTA PROVINO", "Modifica filtrazione, tempo, passo o numero di strisce e ripeti. Nessuna stampa è stata creata.", PROVINO_ACCENT);', "retry provino"),
    ('"Tempo e filtrazione trasferiti alla stampa.",GREEN);', '"Tempo e filtrazione trasferiti alla stampa.",PRINT_ACCENT);', "transfer print"),
    ('"MORBIDO · "+sy+"Y / 0M · "+formatTime(softMs)+"  +  DURO · 0Y / "+hm+"M · "+formatTime(hardMs)+". Due esposizioni consecutive, tempi indipendenti.", GREEN);', '"MORBIDO · "+sy+"Y / 0M · "+formatTime(softMs)+"  +  DURO · 0Y / "+hm+"M · "+formatTime(hardMs)+". Due esposizioni consecutive, tempi indipendenti.", SPLIT_ACCENT);', "created Split print"),
)
for old, new, label in simple:
    main = rep(main, old, new, label)

main = rep(main, '''        setStatusPresentation("SPLIT GRADE — FASE 2 DI 2",
                "Usa una nuova striscia. Il morbido scelto verrà applicato prima su tutta la carta; poi partirà il provino duro.", BLUE);''', '''        setStatusPresentation("SPLIT GRADE — FASE 2 DI 2",
                "Usa una nuova striscia. Il morbido scelto verrà applicato prima su tutta la carta; poi partirà il provino duro.", SPLIT_ACCENT);''', "Split phase two")

main = rep(main, 'panel.setBackground(roundRect(CARD, 14, 1, BORDER));\n        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));\n\n        panel.addView(text(existing == null ? "NUOVO PRESET · CONTATTO 35 mm"', 'panel.setBackground(roundRect(CARD, 14, 1, CONTACT_ACCENT));\n        sc.addView(panel, new ScrollView.LayoutParams(-1, -2));\n\n        panel.addView(text(existing == null ? "NUOVO PRESET · CONTATTO 35 mm"', "contact editor surface")
main = rep(main, 'panel.addView(text(existing == null ? "NUOVO PRESET · CONTATTO 35 mm" : "MODIFICA PRESET · CONTATTO 35 mm", 19, TEXT_PRIMARY, true)', 'panel.addView(text(existing == null ? "NUOVO PRESET · CONTATTO 35 mm" : "MODIFICA PRESET · CONTATTO 35 mm", 19, CONTACT_ACCENT, true)', "contact editor title")
main = rep(main, "save.setBackground(roundRect(BLUE, 9, 0, 0));\n        save.setTextColor(Color.BLACK);", "save.setBackground(roundRect(CONTACT_ACCENT, 9, 0, 0));\n        save.setTextColor(Color.BLACK);", "contact save")

main = rep(
    main,
    '''        if (testSplitPhaseText != null) {
            testSplitPhaseText.setVisibility(split ? View.VISIBLE : View.GONE);
''',
    '''        int flowAccent = split ? SPLIT_ACCENT : PROVINO_ACCENT;
        if (testTimeText != null) testTimeText.setTextColor(flowAccent);
        if (testCumulativeText != null) testCumulativeText.setTextColor(flowAccent);
        if (testCountText != null) testCountText.setTextColor(flowAccent);
        if (testPauseText != null) testPauseText.setTextColor(flowAccent);
        if (testPendingChoiceButton != null) {
            testPendingChoiceButton.setBackground(roundRect(flowAccent, 9, 0, 0));
            testPendingChoiceButton.setTextColor(darkroomMode ? Color.BLACK : Color.WHITE);
        }
        if (testSplitPhaseText != null) {
            testSplitPhaseText.setTextColor(flowAccent);
            testSplitPhaseText.setVisibility(split ? View.VISIBLE : View.GONE);
''',
    "dynamic provino identity",
)
main = rep(main, 'TextView value = text(isCount ? String.valueOf(testCount) : formatTime(testPauseMs), 22, BLUE, true);', 'TextView value = text(isCount ? String.valueOf(testCount) : formatTime(testPauseMs), 22, currentModeAccent(), true);', "provino steppers")

main = rep(main, '''        panel.addView(text("PIANO DI STAMPA", 19, TEXT_PRIMARY, true), lp(-1,-2));
''', '''        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, PLAN_ACCENT));
        panel.addView(text("PIANO DI STAMPA", 19, PLAN_ACCENT, true), lp(-1,-2));
''', "print plan surface")
main = rep(main, 'panel.addView(text("CORREZIONE GLOBALE",19,TEXT_PRIMARY,true),lp(-1,-2));', 'panel.addView(text("CORREZIONE GLOBALE",19,GLOBAL_ACCENT,true),lp(-1,-2));', "global correction title")
main = rep(main, 'b.setTextColor(Color.WHITE); b.setBackground(roundRect(Color.rgb(55,60,64),9,0,0));', 'b.setTextColor(darkroomMode ? Color.BLACK : Color.WHITE); b.setBackground(roundRect(GLOBAL_ACCENT,9,0,0));', "global correction buttons")

main = rep(main, 'TextView summary = text(joinBits(mainBits), 14, e.exposureMs > 0 ? GREEN : TEXT_PRIMARY, true);', 'TextView summary = text(joinBits(mainBits), 14, e.exposureMs > 0 ? PRINT_ACCENT : TEXT_PRIMARY, true);', "Log print summary")
main = rep(main, 'TextView test = text(provino, 11, BLUE, false);', 'TextView test = text(provino, 11, PROVINO_ACCENT, false);', "Log provino detail")
main = rep(main, '                accent = GREEN;\n            } else if (item.testMs > 0)', '                accent = PrintSequence.decode(item.printSequence).isEmpty() ? PRINT_ACCENT : PLAN_ACCENT;\n            } else if (item.testMs > 0)', "Log print history")
main = rep(main, '                accent = BLUE;\n            } else {', '                accent = PROVINO_ACCENT;\n            } else {', "Log provino history")
main = rep(main, 'b35.setBackground(roundRect("35mm".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));', 'b35.setBackground(roundRect("35mm".equals(negative[0]) ? LOG_ACCENT : BUTTON, 8, 1, BORDER));', "Log 35")
main = rep(main, 'b66.setBackground(roundRect("6x6".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));', 'b66.setBackground(roundRect("6x6".equals(negative[0]) ? LOG_ACCENT : BUTTON, 8, 1, BORDER));', "Log 6x6")
main = rep(main, 'b45.setBackground(roundRect("4x5".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));', 'b45.setBackground(roundRect("4x5".equals(negative[0]) ? LOG_ACCENT : BUTTON, 8, 1, BORDER));', "Log 4x5")
main = rep(main, 'useForPrint.setBackground(roundRect(GREEN, 9, 0, 0));', 'useForPrint.setBackground(roundRect(PLAN_ACCENT, 9, 0, 0));', "Log reuse plan")

MAIN.write_text(main, encoding="utf-8")

for marker in (
    "TIMER_IDENTITY_061",
    "int flowAccent = split ? SPLIT_ACCENT : PROVINO_ACCENT;",
    'setStatusPresentation("CONTATTO 35 mm — " + preset.title(), preset.setupLine(), CONTACT_ACCENT)',
    'setStatusPresentation("SPLIT GRADE — FASE 1 DI 2", "Trova sperimentalmente il tempo morbido. Nessuna conversione automatica.", SPLIT_ACCENT)',
):
    if marker not in main:
        raise SystemExit(f"v0.6.1 missing Timer identity marker: {marker}")

print("timer_identity_061=PASS")
print("provino_split_contact=DEDICATED_COLOURS")
print("plan_dodge_burn=DEDICATED_COLOURS")
print("darkroom_palette=RED_ONLY")
