#!/usr/bin/env python3
from pathlib import Path
import shutil


ROOT = Path("combined/src/main/java/it/darkroom/timer")
ASSETS = Path("combined/v046_assets")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.4.6 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


def replace_count(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"v0.4.6 {label}: expected {expected} markers, found {count}")
    return text.replace(old, new)


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str, label: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"v0.4.6 {label}: start marker missing")
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f"v0.4.6 {label}: end marker missing")
    return text[:start] + replacement + text[end:]


enlargement_target = ROOT / "EnlargementActivity.java"
migration_target = ROOT / "Lpl7451Migration.java"
if not enlargement_target.exists():
    raise SystemExit("v0.4.6 generated EnlargementActivity missing")
shutil.copyfile(ASSETS / "EnlargementActivity.java", enlargement_target)
shutil.copyfile(ASSETS / "Lpl7451Migration.java", migration_target)


# Run the one-time print-state migration from both supported entry paths.
home_path = ROOT / "home/HomeActivity.java"
home = home_path.read_text(encoding="utf-8")
home = replace_once(
    home,
    "import it.darkroom.timer.MainActivity;\n",
    "import it.darkroom.timer.MainActivity;\nimport it.darkroom.timer.Lpl7451Migration;\n",
    "Home migration import",
)
home = replace_once(
    home,
    "        super.onCreate(savedInstanceState);\n        getWindow().setStatusBarColor(Color.BLACK);",
    "        super.onCreate(savedInstanceState);\n        Lpl7451Migration.run(this);\n        getWindow().setStatusBarColor(Color.BLACK);",
    "Home migration call",
)
home_path.write_text(home, encoding="utf-8")


main_path = ROOT / "MainActivity.java"
main = main_path.read_text(encoding="utf-8")
main = replace_once(
    main,
    "        super.onCreate(savedInstanceState);\n        SharedPreferences p = getSharedPreferences(\"ui\", MODE_PRIVATE);",
    "        super.onCreate(savedInstanceState);\n        Lpl7451Migration.run(this);\n        SharedPreferences p = getSharedPreferences(\"ui\", MODE_PRIVATE);",
    "Timer migration call",
)

# LPL grade 5 is M130. The Split Grade workflow remains two independent phases.
main = replace_count(main, "splitHardMagenta = 180;", "splitHardMagenta = 130;", 3, "Split hard defaults")
main = replace_once(
    main,
    'p.getInt("splitProvinoHardMagenta", 180)',
    'p.getInt("splitProvinoHardMagenta", 130)',
    "persisted Split hard default",
)
main = replace_once(main, ": 180};", ": 130};", "manual Split hard default")
main = replace_once(main, "Y0 / M180", "Y0 / M130", "Split instructions")

main = replace_once(
    main,
    "    private Button logFilter66Button;\n    private Button logFavoritesButton;",
    "    private Button logFilter66Button;\n    private Button logFilter45Button;\n    private Button logFavoritesButton;",
    "4x5 log filter field",
)

old_filter_label = '''    private String testBaseFilterButtonLabel() {
        String f = ExposureRecipe.filterLabel(testBaseFilterType, testBaseFilterValue);
        return "FILTRO BASE · " + ("NESSUNO".equals(f) ? "NESSUNO" : f);
    }
'''
new_filter_label = '''    private String testBaseFilterButtonLabel() {
        String f = ExposureRecipe.filterLabel(testBaseFilterType, testBaseFilterValue);
        int grade = lplGradeFor(testBaseFilterType, testBaseFilterValue);
        if (provinoFlow == PROVINO_SINGLE && grade >= 0)
            return "CONTRASTO LPL · GRADO " + grade + " · " + lplGradeFilters(grade);
        return "FILTRO BASE · " + ("NESSUNO".equals(f) ? "NESSUNO" : f);
    }

    private int lplGradeFor(String type, int value) {
        int[] yellow = {60, 30, 0, 0, 0, 0};
        int[] magenta = {0, 0, 10, 40, 90, 130};
        String t = ExposureRecipe.normalizeFilter(type);
        int v = ExposureRecipe.snap5(value);
        for (int grade = 0; grade <= 5; grade++) {
            if (yellow[grade] > 0 && ExposureRecipe.FILTER_YELLOW.equals(t) && v == yellow[grade]) return grade;
            if (magenta[grade] > 0 && ExposureRecipe.FILTER_MAGENTA.equals(t) && v == magenta[grade]) return grade;
        }
        return -1;
    }

    private String lplGradeFilters(int grade) {
        String[] filters = {"Y60 / M0", "Y30 / M0", "Y0 / M10", "Y0 / M40", "Y0 / M90", "Y0 / M130"};
        return filters[Math.max(0, Math.min(5, grade))];
    }

    private void showLplGradeDialog() {
        String[] choices = {
                "GRADO 0 · Y60 / M0", "GRADO 1 · Y30 / M0", "GRADO 2 · Y0 / M10",
                "GRADO 3 · Y0 / M40", "GRADO 4 · Y0 / M90", "GRADO 5 · Y0 / M130",
                "VALORE MANUALE M/Y", "NESSUNO"
        };
        showAppChoiceDialog("CONTRASTO JOBO/LPL 7451", choices, which -> {
            if (which >= 0 && which <= 5) {
                int[] yellow = {60, 30, 0, 0, 0, 0};
                int[] magenta = {0, 0, 10, 40, 90, 130};
                testBaseFilterType = yellow[which] > 0 ? ExposureRecipe.FILTER_YELLOW : ExposureRecipe.FILTER_MAGENTA;
                testBaseFilterValue = yellow[which] > 0 ? yellow[which] : magenta[which];
                persistTestBaseFilter();
            } else if (which == 6) {
                showAppChoiceDialog("VALORE MANUALE LPL", new String[]{"MAGENTA (M)", "GIALLO (Y)"},
                        channel -> showTestBaseFilterValueDialog(channel == 0 ? ExposureRecipe.FILTER_MAGENTA : ExposureRecipe.FILTER_YELLOW), "ANNULLA");
            } else {
                testBaseFilterType = ExposureRecipe.FILTER_NONE;
                testBaseFilterValue = 0;
                persistTestBaseFilter();
            }
        }, "ANNULLA");
    }
'''
main = replace_once(main, old_filter_label, new_filter_label, "LPL contrast helpers")

old_dialog = '''    private void showTestBaseFilterDialog() {
        if (darkroomMode || armed) return;
        if (provinoFlow == PROVINO_SPLIT_SOFT) { showTestBaseFilterValueDialog(ExposureRecipe.FILTER_YELLOW); return; }
        if (provinoFlow == PROVINO_SPLIT_HARD) { showTestBaseFilterValueDialog(ExposureRecipe.FILTER_MAGENTA); return; }
        String[] choices = {"NESSUNO", "MAGENTA (M)", "GIALLO (Y)"};
        showAppChoiceDialog("FILTRO BASE DEL PROVINO", choices, which -> {
            if (which == 0) {
                testBaseFilterType = ExposureRecipe.FILTER_NONE;
                testBaseFilterValue = 0;
                persistTestBaseFilter();
                return;
            }
            showTestBaseFilterValueDialog(which == 1 ? ExposureRecipe.FILTER_MAGENTA : ExposureRecipe.FILTER_YELLOW);
        }, "ANNULLA");
    }
'''
new_dialog = '''    private void showTestBaseFilterDialog() {
        if (darkroomMode || armed) return;
        if (provinoFlow == PROVINO_SPLIT_SOFT) { showTestBaseFilterValueDialog(ExposureRecipe.FILTER_YELLOW); return; }
        if (provinoFlow == PROVINO_SPLIT_HARD) { showTestBaseFilterValueDialog(ExposureRecipe.FILTER_MAGENTA); return; }
        showLplGradeDialog();
    }
'''
main = replace_once(main, old_dialog, new_dialog, "LPL contrast dialog")
main = replace_once(
    main,
    '        plus.setOnClickListener(v -> { value[0]=Math.min(200,value[0]+5); number.setText(type+value[0]); });',
    '        plus.setOnClickListener(v -> { int max=ExposureRecipe.FILTER_MAGENTA.equals(type)?170:200; value[0]=Math.min(max,value[0]+5); number.setText(type+value[0]); });',
    "LPL filter range",
)

old_filter_row = '''        LinearLayout filterRow = new LinearLayout(this);
        filterRow.setOrientation(LinearLayout.HORIZONTAL);
        logFilterAllButton = compactButton("TUTTE");
        logFilter35Button = compactButton("35 mm");
        logFilter66Button = compactButton("6×6");
        logFilterAllButton.setOnClickListener(v -> setLogFilter("ALL"));
        logFilter35Button.setOnClickListener(v -> setLogFilter("35mm"));
        logFilter66Button.setOnClickListener(v -> setLogFilter("6x6"));
        filterRow.addView(logFilterAllButton, margin(lp(0, dp(43), 1f), 0, 0, dp(4), 0));
        filterRow.addView(logFilter35Button, margin(lp(0, dp(43), 1f), dp(4), 0, dp(4), 0));
        filterRow.addView(logFilter66Button, margin(lp(0, dp(43), 1f), dp(4), 0, 0, 0));
'''
new_filter_row = '''        LinearLayout filterRow = new LinearLayout(this);
        filterRow.setOrientation(LinearLayout.HORIZONTAL);
        logFilterAllButton = compactButton("TUTTE");
        logFilter35Button = compactButton("35 mm");
        logFilter66Button = compactButton("6×6");
        logFilter45Button = compactButton("4×5");
        logFilterAllButton.setOnClickListener(v -> setLogFilter("ALL"));
        logFilter35Button.setOnClickListener(v -> setLogFilter("35mm"));
        logFilter66Button.setOnClickListener(v -> setLogFilter("6x6"));
        logFilter45Button.setOnClickListener(v -> setLogFilter("4x5"));
        filterRow.addView(logFilterAllButton, margin(lp(0, dp(43), 1f), 0, 0, dp(3), 0));
        filterRow.addView(logFilter35Button, margin(lp(0, dp(43), 1f), dp(3), 0, dp(3), 0));
        filterRow.addView(logFilter66Button, margin(lp(0, dp(43), 1f), dp(3), 0, dp(3), 0));
        filterRow.addView(logFilter45Button, margin(lp(0, dp(43), 1f), dp(3), 0, 0, 0));
'''
main = replace_once(main, old_filter_row, new_filter_row, "4x5 log filter row")
main = replace_once(
    main,
    '        styleLogFilterButton(logFilter66Button, "6x6".equals(logFilter));\n',
    '        styleLogFilterButton(logFilter66Button, "6x6".equals(logFilter));\n        styleLogFilterButton(logFilter45Button, "4x5".equals(logFilter));\n',
    "4x5 log filter state",
)

old_group_match = '''    private boolean groupMatchesFormat(LogGroup group) {
        if ("ALL".equals(logFilter)) return true;
        for (LogEntry e : group.entries) {
            String neg = e.negative == null ? "" : e.negative.trim();
            if ("35mm".equals(logFilter) && "35mm".equalsIgnoreCase(neg)) return true;
            if ("6x6".equals(logFilter) && "6x6".equalsIgnoreCase(neg)) return true;
        }
        return false;
    }
'''
new_group_match = '''    private static String canonicalLogNegative(String raw) {
        String n = raw == null ? "" : raw.trim().toLowerCase(Locale.ITALY).replace(" ", "").replace("×", "x").replace("mm", "");
        if (n.equals("35") || n.equals("24x36") || n.equals("36x24")) return "35mm";
        if (n.equals("66") || n.equals("6x6") || n.equals("56x56")) return "6x6";
        if (n.equals("45") || n.equals("4x5") || n.equals("101,6x127") || n.equals("101.6x127")) return "4x5";
        return raw == null ? "" : raw.trim();
    }

    private static String displayLogNegative(String raw) {
        String n = canonicalLogNegative(raw);
        if ("35mm".equals(n)) return "35 mm";
        if ("6x6".equals(n)) return "6×6";
        if ("4x5".equals(n)) return "4×5";
        return n;
    }

    private boolean groupMatchesFormat(LogGroup group) {
        if ("ALL".equals(logFilter)) return true;
        for (LogEntry e : group.entries) if (logFilter.equals(canonicalLogNegative(e.negative))) return true;
        return false;
    }
'''
main = replace_once(main, old_group_match, new_group_match, "4x5 log matching")
main = replace_count(
    main,
    '"6x6".equals(e.negative) ? "6×6" : e.negative',
    'displayLogNegative(e.negative)',
    1,
    "log card format label",
)
main = replace_count(
    main,
    '"6x6".equals(item.negative) ? "6×6" : item.negative',
    'displayLogNegative(item.negative)',
    1,
    "log history format label",
)

old_neg_editor = '''        final String[] negative = {entry.negative == null ? "" : entry.negative};
        final Button b35 = compactButton("35mm");
        final Button b66 = compactButton("6×6");
        View.OnClickListener negRefresh = v -> {
            negative[0] = v == b35 ? "35mm" : "6x6";
            b35.setBackground(roundRect("35mm".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b66.setBackground(roundRect("6x6".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b35.setTextColor("35mm".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
            b66.setTextColor("6x6".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
        };
        b35.setOnClickListener(negRefresh);
        b66.setOnClickListener(negRefresh);
        negRow.addView(b35, margin(lp(0, dp(46), 1f), 0, 0, dp(4), 0));
        negRow.addView(b66, margin(lp(0, dp(46), 1f), dp(4), 0, 0, 0));
        panel.addView(negRow, margin(lp(-1, -2), 0, 0, 0, 8));
        if ("35mm".equals(negative[0])) b35.performClick();
        else if ("6x6".equals(negative[0])) b66.performClick();
'''
new_neg_editor = '''        final String[] negative = {canonicalLogNegative(entry.negative)};
        final Button b35 = compactButton("35mm");
        final Button b66 = compactButton("6×6");
        final Button b45 = compactButton("4×5");
        View.OnClickListener negRefresh = v -> {
            negative[0] = v == b35 ? "35mm" : (v == b66 ? "6x6" : "4x5");
            b35.setBackground(roundRect("35mm".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b66.setBackground(roundRect("6x6".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b45.setBackground(roundRect("4x5".equals(negative[0]) ? GREEN : BUTTON, 8, 1, BORDER));
            b35.setTextColor("35mm".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
            b66.setTextColor("6x6".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
            b45.setTextColor("4x5".equals(negative[0]) ? Color.BLACK : TEXT_PRIMARY);
        };
        b35.setOnClickListener(negRefresh);
        b66.setOnClickListener(negRefresh);
        b45.setOnClickListener(negRefresh);
        negRow.addView(b35, margin(lp(0, dp(46), 1f), 0, 0, dp(3), 0));
        negRow.addView(b66, margin(lp(0, dp(46), 1f), dp(3), 0, dp(3), 0));
        negRow.addView(b45, margin(lp(0, dp(46), 1f), dp(3), 0, 0, 0));
        panel.addView(negRow, margin(lp(-1, -2), 0, 0, 0, 8));
        if ("35mm".equals(negative[0])) b35.performClick();
        else if ("6x6".equals(negative[0])) b66.performClick();
        else if ("4x5".equals(negative[0])) b45.performClick();
'''
main = replace_once(main, old_neg_editor, new_neg_editor, "4x5 log editor")

main = replace_once(main, '        final EditText column = editField("Altezza colonna cm", entry.columnHeight);\n', "", "remove column editor field")
main = replace_once(main, '        panel.addView(column, margin(lp(-1, dp(52)), 0, 0, 0, 8));\n', "", "remove column editor view")
main = replace_count(main, 'entry.columnHeight = column.getText().toString().trim();', 'entry.columnHeight = "";', 3, "clear legacy column values")
main = replace_once(main, '                .putString("columnHeight", entry.columnHeight == null ? "" : entry.columnHeight)\n', "", "remove reprint column")
main = replace_once(main, '        entry.columnHeight = template.getString("columnHeight", "");', '        entry.columnHeight = "";', "clear template column")

snapshot_start = "    private static boolean applyEnlargementSnapshotToVisibleLogFields(LogEntry entry) {"
summary_start = "    private String enlargementLogSummary(String meta) {"
new_snapshot = '''    private static boolean applyEnlargementSnapshotToVisibleLogFields(LogEntry entry) {
        if (entry == null || entry.enlargementMeta == null || entry.enlargementMeta.trim().isEmpty()) return false;
        boolean changed = false;
        String neg = enlargementMetaValue(entry.enlargementMeta, "neg");
        String canonical = "35".equals(neg) ? "35mm" : ("66".equals(neg) ? "6x6" : ("45".equals(neg) ? "4x5" : ""));
        if (!canonical.isEmpty() && !canonical.equals(canonicalLogNegative(entry.negative))) {
            entry.negative = canonical;
            changed = true;
        }
        if (entry.columnHeight != null && !entry.columnHeight.trim().isEmpty()) {
            entry.columnHeight = "";
            changed = true;
        }
        String paper = enlargementMetaValue(entry.enlargementMeta, "paper");
        if (!paper.isEmpty()) {
            String format = paper.replace('.', ',').replace("x", " × ") + " cm";
            String current = entry.paper == null ? "" : entry.paper.trim();
            if (current.isEmpty()) {
                entry.paper = format;
                changed = true;
            } else if (!current.contains(format) && !current.contains(paper)) {
                entry.paper = current + " · " + format;
                changed = true;
            }
        }
        return changed;
    }

'''
main = replace_between(main, snapshot_start, summary_start, new_snapshot, "LPL log snapshot")

split_summary_start = "    private String splitLogSummary(LogEntry entry, PrintSequence savedSequence) {"
new_summary = '''    private String enlargementLogSummary(String meta) {
        if (meta == null || meta.trim().isEmpty()) return "—";
        String neg = enlargementMetaValue(meta, "neg");
        String paper = enlargementMetaValue(meta, "paper").replace('.', ',').replace("x", " × ");
        String lens = enlargementMetaValue(meta, "lens");
        String beta = enlargementMetaValue(meta, "beta");
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
        if (!beta.isEmpty()) {
            try { b.append(b.length() > 0 ? " · " : "").append("β ").append(String.format(Locale.ITALY, "%.3f", Double.parseDouble(beta))); }
            catch (Exception ignored) {}
        }
        if (!mode.isEmpty()) b.append(b.length() > 0 ? " · " : "").append(mode);
        return b.length() == 0 ? "—" : b.toString();
    }

'''
main = replace_between(main, summary_start, split_summary_start, new_summary, "LPL log summary")

settings_start = '        TextView paperPlaneTitle = text("ALTEZZA PIANO CARTA (spessore marginatore)", 12, TEXT_PRIMARY, true);'
settings_end = "\n\n        panel.addView(hardwareGroup"
settings_replacement = '''        TextView lplTitle = text("JOBO/LPL 7451 · CALIBRAZIONE COLONNA", 12, TEXT_PRIMARY, true);
        lplTitle.setPadding(dp(4), dp(10), dp(4), dp(4));
        hardwareGroup.addView(lplTitle, lp(-1,-2));
        TextView lplNote = text("Il calcolo usa il rapporto β. La scala fisica e l’eventuale offset rispetto al piano del negativo verranno attivati solo dopo una misura reale dell’ingranditore.", 11, MUTED, false);
        lplNote.setPadding(dp(4), dp(2), dp(4), dp(6));
        hardwareGroup.addView(lplNote, lp(-1,-2));'''
main = replace_between(main, settings_start, settings_end, settings_replacement, "remove physical column calibration")
main_path.write_text(main, encoding="utf-8")


split_path = ROOT / "SplitGradePlan.java"
split = split_path.read_text(encoding="utf-8")
split = replace_once(split, "    public int hardMagenta = 180;", "    public int hardMagenta = 130;", "SplitGradePlan LPL default")
split_path.write_text(split, encoding="utf-8")


jpeg_path = ROOT / "JpegCardRenderer.java"
jpeg = jpeg_path.read_text(encoding="utf-8")
jpeg = replace_once(jpeg, '"Titolo", "Negativo", "Diaframma", "Altezza colonna", "Magenta", "Yellow",', '"Titolo", "Negativo", "Diaframma", "Ingrandimento β", "Magenta", "Yellow",', "JPG enlargement label")
jpeg = replace_once(jpeg, '                unitLabel(e.columnHeight, "cm"),', '                enlargementBeta(e),', "JPG enlargement value")
jpeg = replace_once(
    jpeg,
    '        if ("6x6".equalsIgnoreCase(v)) return "6×6";\n        return v;',
    '        if ("6x6".equalsIgnoreCase(v)) return "6×6";\n        if ("4x5".equalsIgnoreCase(v)) return "4×5";\n        return v;',
    "JPG 4x5 label",
)
jpeg = replace_once(
    jpeg,
    "    private static String apertureLabel(String value) {",
    '''    private static String enlargementBeta(LogEntry e) {
        String meta = e == null ? "" : e.enlargementMeta;
        if (meta == null || meta.trim().isEmpty()) return "—";
        String raw = "";
        for (String part : meta.split("\\\\|")) if (part.startsWith("beta=")) raw = part.substring(5);
        try { return "β " + String.format(Locale.ITALY, "%.3f", Double.parseDouble(raw)); }
        catch (Exception ignored) { return "—"; }
    }

    private static String apertureLabel(String value) {''',
    "JPG beta helper",
)
jpeg_path.write_text(jpeg, encoding="utf-8")


maint_path = ROOT / "maintenance/UseMaintenanceActivity.java"
maint = maint_path.read_text(encoding="utf-8")
maint = replace_once(
    maint,
    '    private static final String OPEMUS_URL = "https://drive.google.com/file/d/1UgqM5BZ0HQyKHDYZ-LHXlCFeq-HS_Mvg/view";',
    '    private static final String LPL7451_URL = "https://drive.google.com/file/d/1y67xUwISxjz8f4-QFmBUOquabVezXq4A/view?usp=drivesdk";',
    "LPL manual URL",
)

q_lpl = '''    private static final String[] Q_LPL7451 = {
            "Quali formati supporta il JOBO/LPL 7451?",
            "Quali obiettivi associa Darkroom ai tre formati?",
            "Quale portanegativi devo montare?",
            "Come inserisco e blocco il portanegativi?",
            "Come regolo ingrandimento e messa a fuoco?",
            "Quali sono le scale del modulo colore?",
            "A cosa serve la leva della luce bianca?",
            "A cosa serve l’attenuatore della luce?",
            "La ventola deve restare accesa durante l’uso?",
            "Quando va controllata la camera di diffusione?"
    };
    private static final String[] A_LPL7451 = {
            "Il modello 7451 copre negativi dal 24×36 mm al 4×5 pollici. In Darkroom i formati operativi sono 35 mm (24×36), 6×6 (56×56) e 4×5 (101,6×127 mm).",
            "L’associazione automatica concordata è: 35 mm → 50 mm; 6×6 → 75 mm; 4×5 → 150 mm. La lente resta registrata nei metadati della ricetta e del LOG.",
            "Usa sempre il portanegativi a formato singolo corrispondente: 35 mm/24×36, 6×6/56×56 oppure 4×5/101,6×127. Il manuale descrive portanegativi di tipo sandwich e segnala che possono essere accessori opzionali in alcune aree.",
            "Solleva la leva del fermo, inserisci il portanegativi frontalmente o lateralmente e riabbassa la leva per bloccarlo. Prima verifica che la piastra del piano portanegativi sia correttamente posizionata sui perni.",
            "Allenta il blocco del carrello, usa la leva per gli spostamenti rapidi e la manopola per quelli fini, quindi riblocca la testa. Metti a fuoco con una delle due manopole; sul lato destro è disponibile la regolazione fine 1:5.",
            "Il modulo dicroico ha scale di densità giallo e ciano 0–200 cc e magenta 0–170 cc. Per la carta multigrade Darkroom usa la tabella LPL dei gradi 0–5 con Y e M, lasciando il ciano a zero.",
            "Portandola in posizione orizzontale, i filtri escono dal percorso ottico senza cambiare i valori impostati. Serve per facilitare composizione e messa a fuoco; prima di esporre riporta i filtri nel percorso ottico.",
            "Inserisce un attenuatore che riduce la luce a circa un quarto, cioè due stop, così puoi ottenere tempi di esposizione più lunghi senza cambiare la filtrazione di contrasto.",
            "Sì. Il manuale prescrive di tenere sempre in funzione la ventola mentre l’ingranditore è in uso e di utilizzare esclusivamente l’alimentatore previsto. Darkroom non gestisce automaticamente la ventola.",
            "Dopo molte ore il rivestimento in materiale espanso può ingiallire. Il manuale descrive la rimozione della piastra superiore e l’estrazione della camera di diffusione; esegui l’intervento a macchina spenta e fredda."
    };

'''
maint = replace_between(
    maint,
    "    private static final String[] Q_OPEMUS = {",
    "    private static final String[] Q_COLOR3 = {",
    q_lpl,
    "replace enlarger FAQ",
)
maint = replace_once(
    maint,
    '        body.addView(navCard("MEOPTA OPEMUS 6","Ingranditore",()->navigate(()->renderFaqPage("MEOPTA OPEMUS 6","Fonte: Meopta Opemus 6 Standard - Manuale IT",Q_OPEMUS,A_OPEMUS,OPEMUS_URL,"APRI MANUALE COMPLETO"))));',
    '        body.addView(navCard("JOBO/LPL 7451","Ingranditore a diffusione · 35 mm, 6×6 e 4×5",()->navigate(()->renderFaqPage("JOBO/LPL 7451","Fonte: LPL 7451 - manuale completo tradotto in italiano",Q_LPL7451,A_LPL7451,LPL7451_URL,"APRI MANUALE COMPLETO IT"))));',
    "LPL manual card",
)
maint = replace_once(
    maint,
    '        addFaqMatches(hits,"MEOPTA OPEMUS 6",Q_OPEMUS,A_OPEMUS,q);',
    '        addFaqMatches(hits,"JOBO/LPL 7451",Q_LPL7451,A_LPL7451,q);',
    "LPL FAQ search",
)
maintenance_method = '''    private void renderMaintenance(){
        begin("MANUTENZIONE","Procedure JOBO/LPL 7451 ricavate dal manuale italiano.");
        LinearLayout card=card(); card.addView(title("JOBO/LPL 7451",19)); card.addView(subtitle("Controlli meccanici e ottici documentati"));
        card.addView(section("CARRELLO E COLONNA","L’accoppiamento è regolato in fabbrica. Se compare gioco, il manuale prevede una regolazione fine dei dadi e delle viti del carrello: procedere per piccoli incrementi, facendo scorrere la testa e serrando i dadi solo quando il movimento è uniforme."));
        card.addView(section("VENTOLA","Tenerla sempre in funzione durante l’uso dell’ingranditore. Darkroom non effettua alcun comando automatico della ventola."));
        card.addView(section("CAMERA DI DIFFUSIONE","Controllare periodicamente il rivestimento interno: dopo molte ore può ingiallire. Per rimozione e sostituzione seguire la sequenza illustrata nel manuale, a macchina spenta e fredda."));
        card.addView(section("CALIBRAZIONE SCALA","La 0.4.6 calcola β e i tempi ma non converte ancora il risultato nella scala fisica della colonna. L’unico offset verrà aggiunto dopo una misura reale riferita al piano del negativo."));
        body.addView(card);
    }
'''
maint = replace_between(
    maint,
    "    private void renderMaintenance(){",
    "    private void renderCookbook(){",
    maintenance_method,
    "LPL maintenance page",
)
maint_path.write_text(maint, encoding="utf-8")


# Final static acceptance for the materialized v0.4.6 source.
generated = {
    "main": main_path.read_text(encoding="utf-8"),
    "enlargement": enlargement_target.read_text(encoding="utf-8"),
    "maintenance": maint_path.read_text(encoding="utf-8"),
    "migration": migration_target.read_text(encoding="utf-8"),
    "jpeg": jpeg_path.read_text(encoding="utf-8"),
}
all_java = "\n".join(generated.values())
active_java = "\n".join(value for key, value in generated.items() if key != "migration")
for forbidden in ("OPEMUS", "C50={{", "C80={{", "b2c(", "enlargementPaperPlaneHeightMm"):
    if forbidden in active_java:
        raise SystemExit(f"v0.4.6 obsolete enlarger marker survives: {forbidden}")
for required in (
    "JOBO/LPL 7451", "101,6 × 127 mm", "obiettivo 150 mm", "portanegativi 4×5",
    "Math.pow((c.beta+1)/(b1+1),2)", "Math.round(ms / 500.0) * 500",
    "GRADO 0 · Y60 / M0", "GRADO 5 · Y0 / M130", 'setLogFilter("4x5")',
    "lpl7451MigrationV046Done", "LogStore.replaceAll", "columnCalibration=PENDING",
    "1y67xUwISxjz8f4-QFmBUOquabVezXq4A", "Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?",
    "Come posso usare il Sistema Zonale con il Minolta Auto Meter III F?",
):
    if required not in all_java:
        raise SystemExit(f"v0.4.6 required marker missing: {required}")

print("Darkroom v0.4.6 JOBO/LPL 7451 patch ready")
print("formats=35mm,6x6,4x5")
print("lenses=50mm,75mm,150mm")
print("lpl_grade_table=0:Y60/M0,1:Y30/M0,2:Y0/M10,3:Y0/M40,4:Y0/M90,5:Y0/M130")
print("physical_column_calibration=DEFERRED")
print("legacy_print_recipes_and_log_reset=ONCE")
print("ev_zone_work_preserved=PASS")
print("lpl_manual_drive=PASS")
