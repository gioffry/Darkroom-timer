#!/usr/bin/env python3
"""Darkroom 0.6.2: refine the approved Timer visual system without changing behaviour."""

from pathlib import Path


MAIN = Path("combined/src/main/java/it/darkroom/timer/MainActivity.java")
ENLARGEMENT = Path("combined/src/main/java/it/darkroom/timer/EnlargementActivity.java")


def rep(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)
    if found != count:
        raise SystemExit(f"v0.6.2 {label}: expected {count}, found {found}")
    return text.replace(old, new)


main = MAIN.read_text(encoding="utf-8")
enlargement = ENLARGEMENT.read_text(encoding="utf-8")

if "TIMER_REFINEMENT_062" in main and "ENLARGEMENT_VISUAL_062" in enlargement:
    print("timer_refinement_062=ALREADY_APPLIED")
    raise SystemExit(0)
if "ACTION_INFORMATION_HIERARCHY_061" not in main or 'APP_VERSION = "0.13.14"' not in main:
    raise SystemExit("v0.6.2: exact v0.6.1 Timer source not recognized")
if "GRAPHIC_SYSTEM_061" not in enlargement and "DarkroomVisualSystem" in enlargement:
    raise SystemExit("v0.6.2: unexpected enlargement visual baseline")

main_before = main
enlargement_before = enlargement

main = rep(
    main,
    "    // GRAPHIC_SYSTEM_061 — stable identity for every operational family.\n",
    "    // GRAPHIC_SYSTEM_061 — stable identity for every operational family.\n"
    "    // TIMER_REFINEMENT_062 — phone-verified hierarchy and phase identity.\n",
    "Timer marker",
)
main = rep(main, 'APP_VERSION = "0.13.14"', 'APP_VERSION = "0.13.15"', "Timer version")

# Unselected controls remain clearly actionable; selection is still conveyed by saturation.
main = rep(main, "testSingleModeButton.setAlpha(active ? 1f : 0.62f);", "testSingleModeButton.setAlpha(active ? 1f : 0.84f);", "single selector opacity")
main = rep(main, "testSplitModeButton.setAlpha(active ? 1f : 0.62f);", "testSplitModeButton.setAlpha(active ? 1f : 0.84f);", "Split selector opacity")
main = rep(main, "b.setAlpha(selected ? 1f : 0.68f);", "b.setAlpha(selected ? 1f : 0.84f);", "contact preset opacity")
main = rep(main, "contact35WorkspaceButton.setAlpha(active ? 1f : 0.68f);", "contact35WorkspaceButton.setAlpha(active ? 1f : 0.84f);", "contact selector opacity")
main = rep(main, "testSingleModeButton.setAlpha(0.62f);", "testSingleModeButton.setAlpha(0.84f);", "contact single opacity")

# Active configuration buttons and the ARM action use the current single/Y/M colour.
main = rep(
    main,
    '''        if (testPendingChoiceButton != null) {
            testPendingChoiceButton.setBackground(roundRect(flowAccent, 9, 0, 0));
            testPendingChoiceButton.setTextColor(actionInk(flowAccent));
        }
''',
    '''        if (testBaseFilterButton != null) {
            testBaseFilterButton.setBackground(roundRect(flowAccent, 9, 0, 0));
            testBaseFilterButton.setTextColor(actionInk(flowAccent));
        }
        if (testStripMethodButton != null) {
            testStripMethodButton.setBackground(roundRect(flowAccent, 9, 0, 0));
            testStripMethodButton.setTextColor(actionInk(flowAccent));
        }
        if (testPendingChoiceButton != null) {
            testPendingChoiceButton.setBackground(roundRect(flowAccent, 9, 0, 0));
            testPendingChoiceButton.setTextColor(actionInk(flowAccent));
        }
''',
    "phase configuration actions",
)
main = rep(
    main,
    '''        if (actionButton != null && mode == MODE_TEST && !armed) {
            if (provinoFlow == PROVINO_SPLIT_SOFT) actionButton.setText("ARMA FASE 1 · MORBIDO · " + testCount + " STRISCE");
            else if (provinoFlow == PROVINO_SPLIT_HARD) actionButton.setText("ARMA FASE 2 · BASE MORBIDA + DURO");
        }
''',
    '''        if (actionButton != null && mode == MODE_TEST && !armed && !contact35Mode) {
            actionButton.setBackground(roundRect(flowAccent, 10, 0, 0));
            actionButton.setTextColor(actionInk(flowAccent));
            if (provinoFlow == PROVINO_SPLIT_SOFT) actionButton.setText("ARMA FASE 1 · MORBIDO · " + testCount + " STRISCE");
            else if (provinoFlow == PROVINO_SPLIT_HARD) actionButton.setText("ARMA FASE 2 · BASE MORBIDA + DURO");
        }
''',
    "phase ARM identity",
)

# Contact preset values retain labels even when defaults are already populated.
main = rep(
    main,
    "    private void showContact35PresetEditor(final Contact35Preset existing) {",
    '''    private LinearLayout contactPresetField(String caption, EditText field) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        TextView label = text(caption, 11, CONTACT_ACCENT, true);
        label.setPadding(dp(3), 0, dp(3), dp(4));
        box.addView(label, lp(-1, -2));
        box.addView(field, lp(-1, dp(52)));
        return box;
    }

    private void showContact35PresetEditor(final Contact35Preset existing) {''',
    "contact field helper",
)
main = rep(main, 'EditText film = editField("Pellicola — es. FP4+",', 'EditText film = editField("es. FP4+",', "film hint")
main = rep(main, 'EditText iso = editField("ISO — es. 125",', 'EditText iso = editField("es. 125",', "ISO hint")
main = rep(main, 'EditText column = editField("Colonna LPL — predefinito 57",', 'EditText column = editField("predefinito 57",', "column hint")
main = rep(main, 'EditText aperture = editField("Diaframma — predefinito f/8",', 'EditText aperture = editField("predefinito f/8",', "aperture hint")
main = rep(main, 'EditText contrast = editField("Contrasto — predefinito Y0 / M10",', 'EditText contrast = editField("predefinito Y0 / M10",', "filtration hint")
main = rep(main, 'EditText seconds = editField("Tempo (s) — es. 11,5",', 'EditText seconds = editField("es. 11,5",', "time hint")
main = rep(
    main,
    '''        panel.addView(film, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(iso, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(column, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(aperture, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(contrast, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(seconds, margin(lp(-1, dp(52)), 0, 0, 0, 12));
''',
    '''        panel.addView(contactPresetField("PELLICOLA", film), margin(lp(-1, -2), 0, 0, 0, 8));
        panel.addView(contactPresetField("ISO", iso), margin(lp(-1, -2), 0, 0, 0, 8));
        panel.addView(contactPresetField("SCALA COLONNA LPL", column), margin(lp(-1, -2), 0, 0, 0, 8));
        panel.addView(contactPresetField("DIAFRAMMA", aperture), margin(lp(-1, -2), 0, 0, 0, 8));
        panel.addView(contactPresetField("FILTRAZIONE", contrast), margin(lp(-1, -2), 0, 0, 0, 8));
        panel.addView(contactPresetField("TEMPO (s)", seconds), margin(lp(-1, -2), 0, 0, 0, 12));
''',
    "persistent contact labels",
)
main = rep(
    main,
    '''        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f),
                (int)(getResources().getDisplayMetrics().heightPixels * 0.88f));
    }

    private LinearLayout buildContact35Panel() {''',
    '''        if (w != null) w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show();
        if (w != null) {
            w.addFlags(android.view.WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            android.view.WindowManager.LayoutParams attributes = w.getAttributes();
            attributes.dimAmount = 0.82f;
            w.setAttributes(attributes);
            w.setLayout((int)(getResources().getDisplayMetrics().widthPixels * 0.94f),
                    (int)(getResources().getDisplayMetrics().heightPixels * 0.88f));
        }
    }

    private LinearLayout buildContact35Panel() {''',
    "contact modal backdrop",
)
main = rep(
    main,
    '''        LinearLayout selected = informationCard(CONTACT_ACCENT);
        contact35SelectedLabel = text("NESSUN PRESET SELEZIONATO", 14, MUTED, true);
        contact35SelectedLabel.setGravity(Gravity.CENTER);
        selected.addView(contact35SelectedLabel);
        contact35SelectedSetup = text("24×30 · 50 mm · H57 · f/8 · Y0 / M10", 12, MUTED, true);
        contact35SelectedSetup.setGravity(Gravity.CENTER);
        contact35SelectedSetup.setPadding(dp(4), dp(6), dp(4), 0);
        selected.addView(contact35SelectedSetup);
        contact35SelectedTime = text("—", 44, CONTACT_ACCENT, true);
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
''',
    '''        LinearLayout selected = informationCard(CONTACT_ACCENT);
        selected.setPadding(dp(12), dp(10), dp(12), dp(10));
        contact35SelectedLabel = text("NESSUN PRESET SELEZIONATO", 14, MUTED, true);
        contact35SelectedLabel.setGravity(Gravity.CENTER);
        selected.addView(contact35SelectedLabel);
        contact35SelectedSetup = text("24×30 · 50 mm · H57 · f/8 · Y0 / M10", 11, MUTED, true);
        contact35SelectedSetup.setGravity(Gravity.CENTER);
        contact35SelectedSetup.setPadding(dp(4), dp(4), dp(4), 0);
        selected.addView(contact35SelectedSetup);
        contact35SelectedTime = text("—", 36, CONTACT_ACCENT, true);
        contact35SelectedTime.setGravity(Gravity.CENTER);
        contact35SelectedTime.setPadding(0, dp(3), 0, 0);
        selected.addView(contact35SelectedTime, lp(-1, dp(50)));
        outer.addView(selected, margin(lp(-1, -2), 0, 0, 0, 8));

        TextView presetsTitle = text("PRESET SALVATI", 12, MUTED, true);
        presetsTitle.setPadding(dp(4), 0, 0, dp(2));
        outer.addView(presetsTitle, lp(-1, -2));
        TextView presetsHint = text("Tocca per richiamare · tieni premuto per modificare o eliminare", 10, MUTED, false);
        presetsHint.setPadding(dp(4), 0, 0, dp(5));
        outer.addView(presetsHint, lp(-1, -2));
''',
    "compact selected contact preset",
)

# The print plan explains and colours the procedure actually shown.
old_howto_start = main.index("    private LinearLayout buildSplitHowToCard() {")
old_howto_end = main.index("    private LinearLayout buildManualSplitEditor", old_howto_start)
old_howto = main[old_howto_start:old_howto_end]
new_howto = '''    private LinearLayout buildPrintPlanHowToCard(boolean split) {
        int accent = split ? SPLIT_ACCENT : PRINT_ACCENT;
        LinearLayout info = informationCard(accent);
        info.setPadding(dp(12), dp(10), dp(12), dp(10));
        info.addView(text(split ? "COME SI USA · SPLIT GRADE" : "COME SI USA · STAMPA SINGOLA", 13, accent, true), lp(-1,-2));
        TextView body = text(split
                ? "Lo Split Grade usa due esposizioni distinte, non due filtri contemporaneamente.\\n"
                    + "1. Morbido: prova Y60 / M0 e scegli il tempo che rende soprattutto i toni chiari.\\n"
                    + "2. Duro: su una nuova striscia applica il morbido scelto su tutta la carta, poi prova Y0 / M130 e scegli il miglior equilibrio di ombre e neri.\\n"
                    + "3. Stampa: esegui le due esposizioni una dopo l’altra. Se cambi il morbido, devi ricontrollare il duro."
                : "Usa come base il tempo scelto nel provino singolo. Le correzioni locali DODGE e BURN restano separate; Allunga tempi diventa disponibile dopo la prima stampa e Correzione globale interviene sull’intera ricetta.",
                11, MUTED, false);
        body.setLineSpacing(0, 1.08f);
        body.setPadding(0, dp(5), 0, 0);
        info.addView(body, lp(-1,-2));
        return info;
    }

'''
main = main[:old_howto_start] + new_howto + main[old_howto_end:]

main = rep(main, "TextView baseInfo=text(base,13,darkroomMode?RED:GREEN,true);", "TextView baseInfo=text(base,13,darkroomMode?RED:PRINT_ACCENT,true);", "print base identity")
main = rep(
    main,
    '''                Button hard=compactButton("RIFAI SOLO IL DURO"); hard.setOnClickListener(v->{dialog.dismiss();beginSplitRevisionFromPrint(true);}); panel.addView(hard,margin(lp(-1,dp(48)),0,0,0,6));
                Button both=compactButton("RIFAI ENTRAMBI"); both.setOnClickListener(v->{dialog.dismiss();beginSplitRevisionFromPrint(false);}); panel.addView(both,margin(lp(-1,dp(48)),0,0,0,6));
                Button known=compactButton("MODIFICA / INSERISCI TEMPI GIÀ NOTI"); known.setOnClickListener(v->manualEditor.setVisibility(View.VISIBLE)); panel.addView(known,margin(lp(-1,dp(48)),0,0,0,9));
''',
    '''                Button hard=compactButton("RIFAI SOLO IL DURO"); hard.setTextColor(actionInk(SPLIT_MAGENTA_ACCENT)); hard.setBackground(roundRect(SPLIT_MAGENTA_ACCENT,8,0,0)); hard.setOnClickListener(v->{dialog.dismiss();beginSplitRevisionFromPrint(true);}); panel.addView(hard,margin(lp(-1,dp(48)),0,0,0,6));
                Button both=compactButton("RIFAI MORBIDO E DURO"); both.setTextColor(actionInk(SPLIT_YELLOW_ACCENT)); both.setBackground(roundRect(SPLIT_YELLOW_ACCENT,8,0,0)); both.setOnClickListener(v->{dialog.dismiss();beginSplitRevisionFromPrint(false);}); panel.addView(both,margin(lp(-1,dp(48)),0,0,0,6));
                Button known=compactButton("SPLIT GRADE · INSERISCI TEMPI NOTI"); known.setTextColor(actionInk(SPLIT_ACCENT)); known.setBackground(roundRect(SPLIT_ACCENT,8,0,0)); known.setOnClickListener(v->manualEditor.setVisibility(View.VISIBLE)); panel.addView(known,margin(lp(-1,dp(48)),0,0,0,9));
''',
    "existing Split actions",
)
main = rep(
    main,
    '''                Button guided=compactButton("TROVA I TEMPI CON UN PROVINO  ·  CONSIGLIATO"); guided.setTextColor(Color.BLACK); guided.setBackground(roundRect(SPLIT_ACCENT,8,0,0)); guided.setOnClickListener(v->{dialog.dismiss();beginSplitFromSingleWithProvino();}); panel.addView(guided,margin(lp(-1,dp(52)),0,0,0,6));
                Button known=compactButton("INSERISCI TEMPI GIÀ NOTI"); known.setOnClickListener(v->manualEditor.setVisibility(View.VISIBLE)); panel.addView(known,margin(lp(-1,dp(48)),0,0,0,6));
                Button retest=compactButton("RIFAI PROVINO SINGOLO"); retest.setOnClickListener(v->{dialog.dismiss();beginSingleRevisionFromPrint();}); panel.addView(retest,margin(lp(-1,dp(48)),0,0,0,9));
''',
    '''                Button guided=compactButton("SPLIT GRADE CON PROVINO · CONSIGLIATO"); guided.setTextColor(actionInk(SPLIT_ACCENT)); guided.setBackground(roundRect(SPLIT_ACCENT,8,0,0)); guided.setOnClickListener(v->{dialog.dismiss();beginSplitFromSingleWithProvino();}); panel.addView(guided,margin(lp(-1,dp(52)),0,0,0,6));
                Button known=compactButton("SPLIT GRADE · INSERISCI TEMPI NOTI"); known.setTextColor(actionInk(SPLIT_ACCENT)); known.setBackground(roundRect(SPLIT_ACCENT,8,0,0)); known.setOnClickListener(v->manualEditor.setVisibility(View.VISIBLE)); panel.addView(known,margin(lp(-1,dp(48)),0,0,0,6));
                Button retest=compactButton("RIFAI PROVINO SINGOLO"); retest.setTextColor(actionInk(PROVINO_ACCENT)); retest.setBackground(roundRect(PROVINO_ACCENT,8,0,0)); retest.setOnClickListener(v->{dialog.dismiss();beginSingleRevisionFromPrint();}); panel.addView(retest,margin(lp(-1,dp(48)),0,0,0,9));
''',
    "single print-plan actions",
)
main = rep(main, "panel.addView(buildSplitHowToCard(), margin(lp(-1,-2),0,2,0,10));", "panel.addView(buildPrintPlanHowToCard(printSequence != null && printSequence.hasSplit()), margin(lp(-1,-2),0,2,0,10));", "contextual print guide")
main = rep(
    main,
    'Button global=compactButton("CORREZIONE GLOBALE · "+(exposureRecipe==null?"0":exposureRecipe.globalLabel())); global.setTextColor(Color.WHITE); global.setBackground(roundRect(Color.rgb(55,60,64),8,0,0));',
    'Button global=compactButton("CORREZIONE GLOBALE · "+(exposureRecipe==null?"0":exposureRecipe.globalLabel())); global.setTextColor(actionInk(GLOBAL_ACCENT)); global.setBackground(roundRect(GLOBAL_ACCENT,8,0,0));',
    "global correction colour",
)
main = rep(main, '"Morbido e duro restano due esposizioni indipendenti e consecutive. Nessuna compensazione applicata.", GREEN);', '"Morbido e duro restano due esposizioni indipendenti e consecutive. Nessuna compensazione applicata.", SPLIT_ACCENT);', "manual Split status")
main = rep(
    main,
    '''                hardOnly
                        ? "Il morbido corrente resta valido e verrà applicato su tutta la nuova striscia. Il vecchio duro è solo il centro iniziale modificabile."
                        : "Riparti dal morbido con i valori correnti come riferimento. La vecchia coppia resta intatta finché il nuovo procedimento non è completato.",
                SPLIT_ACCENT);''',
    '''                hardOnly
                        ? "Il morbido corrente resta valido e verrà applicato su tutta la nuova striscia. Il vecchio duro è solo il centro iniziale modificabile."
                        : "Riparti dal morbido con i valori correnti come riferimento. La vecchia coppia resta intatta finché il nuovo procedimento non è completato.",
                hardOnly ? SPLIT_MAGENTA_ACCENT : SPLIT_YELLOW_ACCENT);''',
    "Split revision status",
)

# Enlargement keeps every calculation and persistence path, but adopts the Timer visual language.
enlargement = rep(
    enlargement,
    "import java.util.List;",
    "import it.darkroom.ui.DarkroomVisualSystem;\n\nimport java.util.List;",
    "enlargement visual import",
)
enlargement = rep(
    enlargement,
    '''    static final int BG = Color.BLACK;
    static final int PANEL = Color.rgb(24, 24, 24);
    static final int BUTTON = Color.rgb(55, 60, 64);
    static final int BORDER = Color.rgb(67, 67, 67);
    static final int MUTED = Color.rgb(170, 166, 162);
    static final int GREEN = Color.rgb(82, 190, 82);
    static final int TEXT = Color.rgb(246, 243, 238);
''',
    '''    // ENLARGEMENT_VISUAL_062 — Timer subpage identity; calculation logic is unchanged.
    static final int BG = DarkroomVisualSystem.BACKGROUND;
    static final int PANEL = DarkroomVisualSystem.SURFACE_ELEVATED;
    static final int BUTTON = DarkroomVisualSystem.SURFACE_ELEVATED;
    static final int BORDER = DarkroomVisualSystem.BORDER;
    static final int MUTED = DarkroomVisualSystem.MUTED;
    static final int GREEN = DarkroomVisualSystem.SUCCESS;
    static final int TEXT = DarkroomVisualSystem.TEXT;
    static final int IVORY = DarkroomVisualSystem.IVORY;
    static final int ACCENT = DarkroomVisualSystem.ENLARGEMENT;
''',
    "enlargement palette",
)
enlargement = rep(enlargement, 'Button calc = button("CALCOLA", BUTTON);', 'Button calc = button("CALCOLA", ACCENT);', "calculate actions", 2)
enlargement = rep(enlargement, 'Button save = button("SALVA E CONTINUA", GREEN);', 'Button save = button("SALVA E CONTINUA", ACCENT);', "legacy save action")
enlargement = rep(enlargement, 'Button create = button("CREA", GREEN);', 'Button create = button("CREA", ACCENT);', "resize create action")
enlargement = rep(enlargement, 'TextView ok = label("Registrato nella ricetta corrente.", 13, GREEN, true);', 'TextView ok = label("Registrato nella ricetta corrente.", 13, ACCENT, true);', "setup confirmation")
enlargement = rep(
    enlargement,
    '''    void addCalibrationNotice() {
        root.addView(section("CONFIGURAZIONE ATTIVA",
                "JOBO/LPL 7451 calibrato con misura meccanica: scala 67, piano negativo–base 73 cm, marginatore 6 mm. "
                        + "La distanza negativo–carta è scala + 5,4 cm; il valore calcolato è il punto iniziale per la messa a fuoco fine."));
    }
''',
    '''    void addCalibrationNotice() {
        root.addView(section("CONFIGURAZIONE ATTIVA",
                "JOBO/LPL 7451 · calibrazione meccanica\\n"
                        + "Scala di riferimento 67 · piano negativo–base 73 cm\\n"
                        + "Marginatore 6 mm · offset scala +5,4 cm\\n"
                        + "Il risultato è il punto iniziale per la messa a fuoco fine."),
                margin(lp(-1, -2), 0, 0, 0, 12));
    }
''',
    "calibration summary",
)
enlargement = rep(enlargement, "fixed.setBackground(bg(PANEL, 10, BORDER, 1));", "fixed.setBackground(bg(BG, 10, ACCENT, 1));", "fixed negative information")

paper_start = enlargement.index("    void addPaperFields(String meta) {")
paper_end = enlargement.index("    static final class Dims", paper_start)
paper_old = enlargement[paper_start:paper_end]
paper_new = '''    void addPaperFields(String meta) {
        paper = spinner(PAPERS);
        w = input("Larghezza carta cm");
        h = input("Altezza carta cm");
        root.addView(label("FORMATO CARTA FOMA", 12, MUTED, true));
        root.addView(paper, margin(lp(-1, dp(50)), 0, 0, 0, 10));
        root.addView(label("LARGHEZZA CARTA (cm)", 12, MUTED, true));
        root.addView(w, margin(lp(-1, dp(50)), 0, 0, 0, 8));
        root.addView(label("ALTEZZA CARTA (cm)", 12, MUTED, true));
        root.addView(h, margin(lp(-1, dp(50)), 0, 0, 0, 8));
        TextView landscape = label("ORIENTAMENTO · ORIZZONTALE", 12, MUTED, true);
        root.addView(landscape, margin(lp(-1, -2), 0, dp(4), 0, dp(10)));
        paper.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            public void onNothingSelected(AdapterView<?> a) {}
            public void onItemSelected(AdapterView<?> a, View v, int pos, long id) {
                if (pos < PD.length) {
                    w.setText(fmt(Math.max(PD[pos][0], PD[pos][1])));
                    h.setText(fmt(Math.min(PD[pos][0], PD[pos][1])));
                    w.setEnabled(false);
                    h.setEnabled(false);
                } else {
                    w.setEnabled(true);
                    h.setEnabled(true);
                }
            }
        });
        double[] dims = metaDims(meta);
        int pi = presetIndex(dims[0], dims[1]);
        if (pi >= 0) paper.setSelection(pi);
        else if (dims[0] > 0 && dims[1] > 0) {
            paper.setSelection(PAPERS.length - 1);
            w.setText(fmt(Math.max(dims[0], dims[1])));
            h.setText(fmt(Math.min(dims[0], dims[1])));
        } else paper.setSelection(2);
    }

'''
enlargement = enlargement[:paper_start] + paper_new + enlargement[paper_end:]

begin_start = enlargement.index("    void begin(String title, String subtitle) {")
begin_end = enlargement.index("    LinearLayout section", begin_start)
begin_old = enlargement[begin_start:begin_end]
begin_new = '''    void begin(String title, String subtitle) {
        ScrollView sc = new ScrollView(this);
        sc.setFillViewport(true);
        sc.setBackgroundColor(BG);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(14), dp(8), dp(14), dp(28));
        root.setBackgroundColor(BG);
        sc.addView(root, new ScrollView.LayoutParams(-1, -2));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        Button back = new Button(this);
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
        setContentView(sc);
    }

'''
enlargement = enlargement[:begin_start] + begin_new + enlargement[begin_end:]

section_start = enlargement.index("    LinearLayout section(String title, String body) {")
section_end = enlargement.index("    void info(String x)", section_start)
section_old = enlargement[section_start:section_end]
section_new = '''    LinearLayout section(String title, String body) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(13), dp(11), dp(13), dp(11));
        box.setBackground(bg(BG, 12, ACCENT, 1));
        box.addView(label(title, 12, ACCENT, true));
        TextView v = label(body, 14, TEXT, false);
        v.setLineSpacing(0, 1.10f);
        v.setPadding(0, dp(5), 0, 0);
        box.addView(v);
        return box;
    }

'''
enlargement = enlargement[:section_start] + section_new + enlargement[section_end:]
enlargement = rep(enlargement, "TextView v = label(x, 14, Color.rgb(230, 196, 150), false);", "TextView v = label(x, 14, ACCENT, false);", "enlargement notices", 2)
enlargement = rep(enlargement, "e.setBackground(bg(PANEL, 10, BORDER, 1));", "e.setBackground(bg(BG, 10, ACCENT, 1));", "enlargement input")
enlargement = rep(enlargement, "t.setTextColor(TEXT);\n                t.setTextSize(15);", "t.setTextColor(actionInk(ACCENT));\n                t.setTextSize(15);", "spinner selected text")
enlargement = rep(enlargement, "sp.setBackground(bg(PANEL, 10, BORDER, 1));", "sp.setBackground(bg(ACCENT, 10, ACCENT, 0));", "spinner filled action")
enlargement = rep(
    enlargement,
    '''        b.setTextColor(TEXT);
        b.setTextSize(15);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setBackground(bg(color, 10, BORDER, 1));
''',
    '''        b.setTextColor(actionInk(color));
        b.setTextSize(15);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setBackground(bg(color, 10, color, 0));
''',
    "filled enlargement buttons",
)
enlargement = rep(
    enlargement,
    "    TextView label(String x, float z, int color, boolean bold) {",
    '''    int actionInk(int color) {
        int luminance = (299 * Color.red(color) + 587 * Color.green(color) + 114 * Color.blue(color)) / 1000;
        return luminance >= 145 ? Color.BLACK : Color.WHITE;
    }

    TextView label(String x, float z, int color, boolean bold) {''',
    "enlargement action ink",
)
enlargement = rep(
    enlargement,
    "    LinearLayout.LayoutParams lp(int width, int height) { return new LinearLayout.LayoutParams(width, height); }",
    '''    LinearLayout.LayoutParams lp(int width, int height) { return new LinearLayout.LayoutParams(width, height); }
    LinearLayout.LayoutParams lp(int width, int height, float weight) { return new LinearLayout.LayoutParams(width, height, weight); }''',
    "weighted enlargement layout",
)

# Keep all operational entry points and the 0.5 s calculations intact.
for token in (
    "beginSplitFromSingleWithProvino();",
    "beginSingleRevisionFromPrint();",
    "beginSplitRevisionFromPrint(true);",
    "beginSplitRevisionFromPrint(false);",
    "showGlobalCorrectionDialog();",
    "showLengthenTimesDialog();",
    "EXTRA_CONTACT_SHEET_35",
):
    if main.count(token) != main_before.count(token):
        raise SystemExit(f"v0.6.2 Timer behaviour changed around {token}")

for token in (
    "void calculateSetup()",
    "void calculateResize(String format)",
    "Calc calc(String format, double W, double H, int fillIndex)",
    "double factor = Math.pow((c.beta+1)/(b1+1),2);",
    "static int snap(double ms) { return (int) Math.round(ms / 500.0) * 500; }",
    ".putBoolean(\"enlargementReloadPending\", true)",
):
    if enlargement.count(token) != enlargement_before.count(token):
        raise SystemExit(f"v0.6.2 enlargement behaviour changed around {token}")

MAIN.write_text(main, encoding="utf-8")
ENLARGEMENT.write_text(enlargement, encoding="utf-8")

print("timer_refinement_062=PASS")
print("split_phase_arm=YELLOW_THEN_MAGENTA")
print("contact_labels=PERSISTENT")
print("print_plan_help=CONTEXTUAL")
print("inactive_actions=FILLED_AND_LEGIBLE")
print("enlargement_subpage=VISUAL_SYSTEM_APPLIED")
print("timer_process_changes=ZERO")
print("enlargement_calculation_changes=ZERO")
