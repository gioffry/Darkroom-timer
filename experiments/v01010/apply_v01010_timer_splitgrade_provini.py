#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
split_grade = java / 'SplitGradePlan.java'
build = work / 'build_darkroom.py'
gradle = project / 'app/build.gradle'
manifest = project / 'app/src/main/AndroidManifest.xml'


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p, s): Path(p).write_text(s, encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rep(p, old, new, label, count=1):
    s = rd(p); n = s.count(old)
    if n < count:
        raise SystemExit(f'v0.10.10 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old, new, count))
    print('v0.10.10 OK', label, flush=True)
def edit_method(p, start, end, editor, label):
    s = rd(p); a = s.find(start)
    if a < 0: raise SystemExit(f'v0.10.10 {label}: inizio non trovato')
    b = s.find(end, a)
    if b < 0: raise SystemExit(f'v0.10.10 {label}: fine non trovata')
    block = s[a:b]
    new = editor(block)
    if new == block: raise SystemExit(f'v0.10.10 {label}: nessuna modifica')
    wr(p, s[:a] + new + s[b:])
    print('v0.10.10 OK', label, flush=True)

# Guardrail: questa release Timer puo' toccare solo MainActivity e SplitGradePlan,
# oltre ai metadati di versione. SONOFF, log e Assistant devono restare byte-identici.
protected_before = {
    p.relative_to(java).as_posix(): sha(p)
    for p in java.rglob('*.java')
    if p.name not in {'MainActivity.java', 'SplitGradePlan.java'}
}

# -----------------------------------------------------------------------------
# Versione 0.10.10 / code 55
# -----------------------------------------------------------------------------
rep(build, 'VERSION_NAME = "0.10.9"', 'VERSION_NAME = "0.10.10"', 'version name build')
rep(build, 'VERSION_CODE = "54"', 'VERSION_CODE = "55"', 'version code build')
rep(build, '[Darkroom v0.10.9]', '[Darkroom v0.10.10]', 'build log tag')
rep(build, r'versionCode\s+54\b', r'versionCode\s+55\b', 'preflight code regex')
rep(build, r'0\.10\.9', r'0\.10\.10', 'preflight name regex')
rep(build, 'versionCode 54 / versionName 0.10.9', 'versionCode 55 / versionName 0.10.10', 'preflight message')
rep(build, 'Preflight v0.10.9 OK', 'Preflight v0.10.10 OK', 'preflight log')
rep(gradle, "versionCode 54\n        versionName '0.10.9'", "versionCode 55\n        versionName '0.10.10'", 'gradle version')
rep(manifest, 'android:versionCode="54"\n    android:versionName="0.10.9"', 'android:versionCode="55"\n    android:versionName="0.10.10"', 'manifest version')
rep(main, 'private static final String APP_VERSION = "0.10.9";', 'private static final String APP_VERSION = "0.10.10";', 'Timer UI version')

# -----------------------------------------------------------------------------
# 1+2. Split Grade: spiegazione corretta + default Foma Variant / Meopta.
# I dati gia' salvati continuano a essere decodificati con i valori memorizzati:
# cambiano solo i default dei nuovi piani.
# -----------------------------------------------------------------------------
rep(split_grade,
'''    public int softYellow = 0;\n    public int softMs = 500;\n    public int hardMagenta = 0;\n    public int hardMs = 500;''',
'''    public int softYellow = 60;\n    public int softMs = 500;\n    public int hardMagenta = 180;\n    public int hardMs = 500;''', 'default Split Grade Foma/Meopta')
rep(split_grade,
'''    public String softLine() { return "SPLIT · MORBIDA · Y " + softYellow + " · " + seconds(softMs); }\n    public String hardLine() { return "SPLIT · DURA · M " + hardMagenta + " · " + seconds(hardMs); }\n    public String softPrompt() { return "Imposta Giallo " + softYellow + ". Poi premi il pulsante."; }\n    public String hardPrompt() { return "Imposta Magenta " + hardMagenta + ". Poi premi il pulsante."; }''',
'''    public String softLine() { return "SPLIT · MORBIDA · " + softYellow + "Y / 0M · " + seconds(softMs); }\n    public String hardLine() { return "SPLIT · DURA · 0Y / " + hardMagenta + "M · " + seconds(hardMs); }\n    public String softPrompt() { return "Imposta " + softYellow + "Y / 0M. Poi premi il pulsante."; }\n    public String hardPrompt() { return "Imposta 0Y / " + hardMagenta + "M. Poi premi il pulsante."; }''', 'etichette Split Grade esplicite')


def edit_split(block):
    old = '''            draft.softYellow = 0;\n            draft.hardMagenta = 0;'''
    new = '''            // Default operativo di riferimento: Fomaspeed Variant 311 RC + testa colore Meopta.\n            draft.softYellow = 60;\n            draft.hardMagenta = 180;'''
    if old not in block: raise SystemExit('v0.10.10 split editor: default creazione non trovato')
    block = block.replace(old, new, 1)

    old = '''        panel.addView(text("SPLIT GRADE", 20, SPLIT_VIVA_MAGENTA, true), lp(-1, -2));\n        TextView note = text("Due esposizioni separate. Dopo la fase morbida la guida vocale ti indica il filtro successivo; la seconda fase parte solo quando premi il pulsante fisico.", 12, MUTED, false);\n        note.setPadding(0, dp(4), 0, dp(12));\n        panel.addView(note, lp(-1, -2));'''
    new = '''        panel.addView(text("SPLIT GRADE", 20, SPLIT_VIVA_MAGENTA, true), lp(-1, -2));\n        TextView note = text("Foma Variant + Meopta · MORBIDA 60Y / 0M · DURA 0Y / 180M · valori modificabili", 12, MUTED, false);\n        note.setPadding(0, dp(4), 0, dp(6));\n        panel.addView(note, lp(-1, -2));\n        Button splitInfo = compactButton("ⓘ  COME FUNZIONA");\n        splitInfo.setTextSize(11);\n        splitInfo.setOnClickListener(v -> showAppConfirmDialog(\n                "COME FUNZIONA LO SPLIT GRADE",\n                "MORBIDO / GIALLO: agisce soprattutto sulla resa dei toni chiari e produce una risposta a contrasto più basso.\\n\\n"\n                        + "DURO / MAGENTA: aumenta soprattutto la separazione delle ombre e la profondità dei neri.\\n\\n"\n                        + "Le due esposizioni NON sono indipendenti: modificare la dura può influire anche sui toni chiari e viceversa. Non significa quindi ‘giallo = solo luci’ o ‘magenta = solo ombre’.",\n                null, null, "CHIUDI"));\n        panel.addView(splitInfo, margin(lp(-1, dp(42)), 0, 0, 0, 10));'''
    if old not in block: raise SystemExit('v0.10.10 split editor: nota introduttiva non trovata')
    block = block.replace(old, new, 1)

    old = '''final TextView syValue = text("Y " + sy[0], 26, SPLIT_VIVA_MAGENTA, true);'''
    new = '''final TextView syValue = text(sy[0] + "Y / 0M", 24, SPLIT_VIVA_MAGENTA, true);'''
    if old not in block: raise SystemExit('v0.10.10 split editor: valore Y non trovato')
    block = block.replace(old, new, 1)
    block = block.replace('syValue.setText("Y " + sy[0]);', 'syValue.setText(sy[0] + "Y / 0M");')

    old = '''final TextView hmValue = text("M " + hm[0], 26, SPLIT_VIVA_MAGENTA, true);'''
    new = '''final TextView hmValue = text("0Y / " + hm[0] + "M", 24, SPLIT_VIVA_MAGENTA, true);'''
    if old not in block: raise SystemExit('v0.10.10 split editor: valore M non trovato')
    block = block.replace(old, new, 1)
    block = block.replace('hmValue.setText("M " + hm[0]);', 'hmValue.setText("0Y / " + hm[0] + "M");')
    return block

edit_method(main,
            '    private void showSplitGradeEditor(final boolean creating) {',
            '    private void showPrintCorrectionEditor(final int index) {',
            edit_split, 'Split Grade UI/default/info')

# Anche nell'editor DODGE/BURN, se esiste uno Split, rendi espliciti i due estremi.
rep(main,
'''final Button soft=compactButton("MORBIDA · Y " + printSequence.split.softYellow); final Button hard=compactButton("DURA · M " + printSequence.split.hardMagenta);''',
'''final Button soft=compactButton("MORBIDA · " + printSequence.split.softYellow + "Y / 0M"); final Button hard=compactButton("DURA · 0Y / " + printSequence.split.hardMagenta + "M");''', 'etichette fase Split nelle correzioni')

# -----------------------------------------------------------------------------
# 3. STAMPA -> PROVINO: migrazione aggiuntiva e non distruttiva.
# Il normale PROVINO mantiene il comportamento storico. Solo il provino creato
# esplicitamente dalla stampa usa la stampa corrente come primo punto e conserva
# il piano Split Grade separato in PrintSequence, senza sommarlo in un tempo unico.
# -----------------------------------------------------------------------------
rep(main,
'''    private TextView testFStopBadge;\n''',
'''    private TextView testFStopBadge;\n    private TextView testMigrationSummary;\n''', 'campo riepilogo migrazione')
rep(main,
'''    private int testPauseMs = 2000;\n''',
'''    private int testPauseMs = 2000;\n    private boolean testFromPrint = false;\n''', 'stato migrazione stampa-provino')
rep(main,
'''        testPauseMs = p.getInt("testPauseMs", 2000);\n''',
'''        testPauseMs = p.getInt("testPauseMs", 2000);\n        testFromPrint = p.getBoolean("testFromPrint", false);\n''', 'carica stato migrazione')

# Il tap diretto sulla tab PROVINO resta il percorso storico e chiude l'eventuale
# contesto di migrazione. Il nuovo comando usa invece returnPrintToTest().
rep(main,
'''        testModeButton.setOnClickListener(v -> setMode(MODE_TEST));''',
'''        testModeButton.setOnClickListener(v -> {\n            testFromPrint = false;\n            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("testFromPrint", false).apply();\n            setMode(MODE_TEST);\n            updateTimingUi();\n        });''', 'tab PROVINO storico invariato')


def edit_print_panel(block):
    needle = '''        updatePrintSequenceUi();\n        return box;'''
    replacement = '''        updatePrintSequenceUi();\n\n        Button backToTest = compactButton("NUOVO PROVINO DA QUESTA STAMPA");\n        backToTest.setTextColor(BLUE);\n        backToTest.setOnClickListener(v -> returnPrintToTest());\n        box.addView(backToTest, margin(lp(-1, dp(50)), 0, 10, 0, 0));\n        return box;'''
    if needle not in block: raise SystemExit('v0.10.10 buildPrintPanel: punto inserimento non trovato')
    return block.replace(needle, replacement, 1)

edit_method(main, '    private LinearLayout buildPrintPanel() {', '    private void updatePrintSequenceUi() {', edit_print_panel, 'pulsante STAMPA -> PROVINO')


def edit_test_panel(block):
    needle = '''        outer.addView(note, lp(-1, -2));\n        return outer;'''
    replacement = '''        outer.addView(note, lp(-1, -2));\n        testMigrationSummary = text("", 12, BLUE, true);\n        testMigrationSummary.setGravity(Gravity.CENTER);\n        testMigrationSummary.setPadding(dp(8), dp(10), dp(8), dp(4));\n        testMigrationSummary.setVisibility(View.GONE);\n        outer.addView(testMigrationSummary, lp(-1, -2));\n        return outer;'''
    if needle not in block: raise SystemExit('v0.10.10 buildTestPanel: punto riepilogo non trovato')
    return block.replace(needle, replacement, 1)

edit_method(main, '    private LinearLayout buildTestPanel() {', '    private LinearLayout buildLogPanel() {', edit_test_panel, 'riepilogo provino derivato')

migration_methods = r'''    private void returnPrintToTest() {
        if (armed) return;
        testFromPrint = true;
        // Il tempo di stampa diventa il primo punto del nuovo provino. In SECONDI
        // le strisce successive crescono di 0,5 s; in F-STOP di 1/4 stop.
        testWidthMs = snap(printWidthMs, 500, 36_000_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putBoolean("testFromPrint", true)
                .putInt("testWidthMs", testWidthMs)
                .apply();
        setMode(MODE_TEST);
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        updateTimingUi();
        updateTestMigrationUi();
        if (printSequence != null && printSequence.hasSplit()) {
            setStatusPresentation("PROVINO DA SPLIT GRADE",
                    "Mantenuti separatamente " + printSequence.split.softLine() + " / " + printSequence.split.hardLine(), BLUE);
        } else {
            setStatusPresentation("PROVINO DALLA STAMPA — " + formatTime(testWidthMs),
                    "Tempo di stampa mantenuto come primo punto; metodo e passo restano invariati.", BLUE);
        }
    }

    private void updateTestMigrationUi() {
        if (testMigrationSummary == null) return;
        if (!testFromPrint) {
            testMigrationSummary.setText("");
            testMigrationSummary.setVisibility(View.GONE);
            return;
        }
        String method = TimingMath.normalizeMethod(timingMethod);
        String step = TimingMath.stepLabel(timingMethod);
        if (printSequence != null && printSequence.hasSplit()) {
            testMigrationSummary.setText("DA STAMPA SPLIT GRADE\n"
                    + printSequence.split.softLine() + "\n"
                    + printSequence.split.hardLine() + "\n"
                    + "Tempi e filtrazioni restano separati · nessuna conversione in esposizione singola\n"
                    + method + " · passo " + step);
        } else {
            testMigrationSummary.setText("DA STAMPA · punto di partenza " + formatTime(testWidthMs)
                    + " · " + method + " · passo " + step);
        }
        testMigrationSummary.setVisibility(View.VISIBLE);
    }

'''
rep(main, '    private void setMode(int newMode) {', migration_methods + '    private void setMode(int newMode) {', 'metodi migrazione')

# Mantieni il riepilogo sincronizzato senza cambiare l'abilitazione dei controlli.
rep(main,
'''        boolean log = mode == MODE_LOG;\n        printPanel.setVisibility(print ? View.VISIBLE : View.GONE);''',
'''        boolean log = mode == MODE_LOG;\n        updateTestMigrationUi();\n        printPanel.setVisibility(print ? View.VISIBLE : View.GONE);''', 'sync riepilogo migrazione')

# Se il provino nasce da una stampa, non reinterpretare il tempo come "incremento":
# il primo target e' la stampa corrente. Il normale algoritmo resta intatto.
rep(main,
'''    private int[] currentTestStripTargets() {\n        return TimingMath.cumulativeSeries(timingMethod, testWidthMs, testCount);\n    }''',
'''    private int[] currentTestStripTargets() {\n        if (!testFromPrint) return TimingMath.cumulativeSeries(timingMethod, testWidthMs, testCount);\n        if (TimingMath.isFStop(timingMethod)) return TimingMath.cumulativeFStopSeries(testWidthMs, testCount);\n        int n = Math.max(0, testCount);\n        int[] out = new int[n];\n        int first = snap(testWidthMs, 500, 36_000_000);\n        for (int i = 0; i < n; i++) out[i] = snap(first + i * 500, 500, 36_000_000);\n        return out;\n    }''', 'targets provino dalla stampa')
rep(main,
'''    private String cumulativeTimes() {\n        return "TEMPI CUMULATIVI  " + TimingMath.seriesLabel(currentTestStripTargets());\n    }''',
'''    private String cumulativeTimes() {\n        return (testFromPrint ? "TEMPI DAL PUNTO DI STAMPA  " : "TEMPI CUMULATIVI  ") + TimingMath.seriesLabel(currentTestStripTargets());\n    }''', 'label serie derivata')
rep(main,
'''    private String testPromptDescription() {\n        return TimingMath.isFStop(timingMethod) ? "Tempo prima striscia" : "Incremento del provino";\n    }''',
'''    private String testPromptDescription() {\n        if (testFromPrint) return "Punto di partenza dalla stampa";\n        return TimingMath.isFStop(timingMethod) ? "Tempo prima striscia" : "Incremento del provino";\n    }''', 'prompt provino derivato')
rep(main,
'''    private String testStepDescription() {\n        return TimingMath.isFStop(timingMethod) ? "Progressione cumulativa • passo ¼ stop" : "Ogni esposizione ha lo stesso tempo";\n    }''',
'''    private String testStepDescription() {\n        if (testFromPrint) return TimingMath.isFStop(timingMethod)\n                ? "Dalla stampa corrente • progressione ¼ stop"\n                : "Dalla stampa corrente • progressione 0,5 s";\n        return TimingMath.isFStop(timingMethod) ? "Progressione cumulativa • passo ¼ stop" : "Ogni esposizione ha lo stesso tempo";\n    }''', 'descrizione passo derivato')

# La soglia 30 s del provino storico resta invariata. Solo un provino esplicitamente
# derivato da una stampa puo' mantenere una base piu' lunga.
rep(main,
'''        if (TimingMath.isFStop(timingMethod)) setTestTime(TimingMath.quarterStop(testWidthMs, direction, 500, 30_000));''',
'''        if (TimingMath.isFStop(timingMethod)) setTestTime(TimingMath.quarterStop(testWidthMs, direction, 500, testFromPrint ? 36_000_000 : 30_000));''', 'regolazione f-stop provino derivato')
rep(main,
'''        testWidthMs = snap(ms, 500, 30_000);''',
'''        testWidthMs = snap(ms, 500, testFromPrint ? 36_000_000 : 30_000);''', 'tempo provino derivato senza clamp distruttivo')

# Aggiornare metodo/tempo deve aggiornare anche il banner, senza toccare il flusso.
rep(main,
'''        updateCumulativeTimes();\n        applyModeUi();\n    }\n\n    private TextView fStopBadge(boolean compact) {''',
'''        updateCumulativeTimes();\n        updateTestMigrationUi();\n        applyModeUi();\n    }\n\n    private TextView fStopBadge(boolean compact) {''', 'sync banner su cambio metodo')
rep(main,
'''        testTimeText.setText(formatTime(testWidthMs));\n        updateCumulativeTimes();\n        applyModeUi();''',
'''        testTimeText.setText(formatTime(testWidthMs));\n        updateCumulativeTimes();\n        updateTestMigrationUi();\n        applyModeUi();''', 'sync banner su cambio tempo')

# -----------------------------------------------------------------------------
# Guardrail e verifiche di accettazione.
# -----------------------------------------------------------------------------
protected_after = {
    p.relative_to(java).as_posix(): sha(p)
    for p in java.rglob('*.java')
    if p.name not in {'MainActivity.java', 'SplitGradePlan.java'}
}
if protected_before != protected_after:
    bad = [n for n in sorted(set(protected_before) | set(protected_after)) if protected_before.get(n) != protected_after.get(n)]
    raise SystemExit('v0.10.10 GUARDRAIL: file non autorizzati modificati: ' + ', '.join(bad))

checks = {
    build: ['VERSION_NAME = "0.10.10"', 'VERSION_CODE = "55"'],
    gradle: ["versionCode 55", "versionName '0.10.10'"],
    manifest: ['android:versionCode="55"', 'android:versionName="0.10.10"', 'package="it.darkroom.timer"'],
    split_grade: ['public int softYellow = 60;', 'public int hardMagenta = 180;', 'softYellow + "Y / 0M', '"SPLIT · DURA · 0Y / " + hardMagenta + "M'],
    main: [
        'private static final String APP_VERSION = "0.10.10";',
        'Foma Variant + Meopta · MORBIDA 60Y / 0M · DURA 0Y / 180M',
        'Le due esposizioni NON sono indipendenti',
        'NUOVO PROVINO DA QUESTA STAMPA',
        'private boolean testFromPrint = false;',
        'Punto di partenza dalla stampa',
        'Tempi e filtrazioni restano separati · nessuna conversione in esposizione singola',
        'if (!testFromPrint) return TimingMath.cumulativeSeries',
        'first + i * 500',
        'maybeShowTestResultChooser',
        'setMode(MODE_PRINT);',
        'showPrintCorrectionEditor',
        'persistPrintSequence'
    ]
}
for p, needles in checks.items():
    t = rd(p)
    for needle in needles:
        if needle not in t: raise SystemExit(f'v0.10.10 verifica fallita: {needle} in {p}')

print('v0.10.10 TIMER SPLIT GRADE + STAMPA->PROVINO — VERIFICHE SORGENTE OK', flush=True)
