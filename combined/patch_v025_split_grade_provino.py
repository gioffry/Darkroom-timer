#!/usr/bin/env python3
from pathlib import Path

root = Path('combined')
java = root / 'src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
service = java / 'SonoffArmService.java'


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s,encoding='utf-8')
def rep(p, old, new, label, count=1):
    s=rd(p); n=s.count(old)
    if n < count:
        raise SystemExit(f'v0.2.5 {label}: atteso >= {count}, trovato {n}')
    wr(p, s.replace(old,new,count))
    print('v0.2.5 OK', label, flush=True)

# Exact generated Timer baseline inside Darkroom v0.2.4.
for p, needle in [
    (main, 'private static final String APP_VERSION = "0.13.7";'),
    (main, 'private void maybeShowTestResultChooser(boolean forceManual)'),
    (service, 'public static final String EXTRA_TEST_FILTER_VALUE = "test_filter_value";'),
    (service, 'private void onExposureFinished() {'),
]:
    if needle not in rd(p):
        raise SystemExit('v0.2.5 base v0.2.4/Timer 0.13.7 non riconosciuta: ' + needle)

# This is the first intentional Timer-engine advance after the frozen 0.13.7 baseline.
rep(main, 'private static final String APP_VERSION = "0.13.7";',
          'private static final String APP_VERSION = "0.13.8";', 'Timer footer version')

# -----------------------------------------------------------------------------
# PROVINO state: SINGLE remains default; Split Grade is one guided workflow.
# -----------------------------------------------------------------------------
rep(main,
'''    private static final int MODE_PRINT = 0;\n    private static final int MODE_TEST = 1;\n    private static final int MODE_LOG = 2;\n''',
'''    private static final int MODE_PRINT = 0;\n    private static final int MODE_TEST = 1;\n    private static final int MODE_LOG = 2;\n\n    private static final int PROVINO_SINGLE = 0;\n    private static final int PROVINO_SPLIT_SOFT = 1;\n    private static final int PROVINO_SPLIT_HARD = 2;\n''','provino state constants')

rep(main,
'''    private Button testBaseFilterButton;\n    private Button testStripMethodButton;\n    private Button testPendingChoiceButton;\n''',
'''    private Button testBaseFilterButton;\n    private Button testStripMethodButton;\n    private Button testPendingChoiceButton;\n    private Button testSingleModeButton;\n    private Button testSplitModeButton;\n    private TextView testSplitPhaseText;\n    private TextView testContrastGuide;\n''','provino UI fields')

rep(main,
'''    private String testStripMethod = TimingMath.MASK_REVEAL;\n    private static final int ALLUNGA_COLOR = Color.rgb(154, 119, 43);\n    private int testWidthMs = 2000;\n''',
'''    private String testStripMethod = TimingMath.MASK_REVEAL;\n    private int provinoFlow = PROVINO_SINGLE;\n    private int splitSoftYellow = 60;\n    private int splitSoftChosenMs = 0;\n    private int splitSoftChosenStrip = -1;\n    private int splitHardMagenta = 180;\n    private int splitHardChosenMs = 0;\n    private int splitHardChosenStrip = -1;\n    private String splitReturnFilterType = ExposureRecipe.FILTER_NONE;\n    private int splitReturnFilterValue = 0;\n    private int splitReturnTestWidthMs = 2000;\n    private static final int ALLUNGA_COLOR = Color.rgb(154, 119, 43);\n    private int testWidthMs = 2000;\n''','provino Split Grade state fields')

rep(main,
'''        testPauseMs = p.getInt("testPauseMs", 2000);\n        testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("testStripMethod", TimingMath.MASK_REVEAL));\n''',
'''        testPauseMs = p.getInt("testPauseMs", 2000);\n        testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("testStripMethod", TimingMath.MASK_REVEAL));\n        provinoFlow = Math.max(PROVINO_SINGLE, Math.min(PROVINO_SPLIT_HARD, p.getInt("provinoFlow", PROVINO_SINGLE)));\n        splitSoftYellow = ExposureRecipe.snap5(p.getInt("splitProvinoSoftYellow", 60));\n        splitSoftChosenMs = p.getInt("splitProvinoSoftMs", 0);\n        splitSoftChosenStrip = p.getInt("splitProvinoSoftStrip", -1);\n        splitHardMagenta = ExposureRecipe.snap5(p.getInt("splitProvinoHardMagenta", 180));\n        splitHardChosenMs = p.getInt("splitProvinoHardMs", 0);\n        splitHardChosenStrip = p.getInt("splitProvinoHardStrip", -1);\n        splitReturnFilterType = ExposureRecipe.normalizeFilter(p.getString("splitProvinoReturnFilterType", testBaseFilterType));\n        splitReturnFilterValue = ExposureRecipe.snap5(p.getInt("splitProvinoReturnFilterValue", testBaseFilterValue));\n        splitReturnTestWidthMs = p.getInt("splitProvinoReturnTestWidthMs", testWidthMs);\n        if (provinoFlow == PROVINO_SPLIT_SOFT) {\n            testBaseFilterType = ExposureRecipe.FILTER_YELLOW;\n            testBaseFilterValue = splitSoftYellow;\n        } else if (provinoFlow == PROVINO_SPLIT_HARD) {\n            if (splitSoftChosenMs <= 0) provinoFlow = PROVINO_SPLIT_SOFT;\n            testBaseFilterType = provinoFlow == PROVINO_SPLIT_HARD ? ExposureRecipe.FILTER_MAGENTA : ExposureRecipe.FILTER_YELLOW;\n            testBaseFilterValue = provinoFlow == PROVINO_SPLIT_HARD ? splitHardMagenta : splitSoftYellow;\n        }\n''','load provino Split Grade state')

# Split selection and current-phase instruction live inside PROVINO, not Home.
rep(main,
'''        Button setEnlargement = compactButton("IMPOSTA INGRANDIMENTO");\n        setEnlargement.setOnClickListener(v -> startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup")));\n        outer.addView(setEnlargement, margin(lp(-1, dp(46)), 0, 0, 0, 10));\n\n        LinearLayout exposure = card();\n''',
'''        LinearLayout provinoModeRow = new LinearLayout(this);\n        provinoModeRow.setOrientation(LinearLayout.HORIZONTAL);\n        provinoModeRow.setGravity(Gravity.CENTER);\n        testSingleModeButton = compactButton("SINGOLO");\n        testSplitModeButton = compactButton("SPLIT GRADE");\n        testSingleModeButton.setOnClickListener(v -> requestSingleProvinoMode());\n        testSplitModeButton.setOnClickListener(v -> startSplitProvino());\n        provinoModeRow.addView(testSingleModeButton, margin(lp(0, dp(48), 1f), 0, 0, dp(4), 0));\n        provinoModeRow.addView(testSplitModeButton, margin(lp(0, dp(48), 1f), dp(4), 0, 0, 0));\n        outer.addView(provinoModeRow, margin(lp(-1, -2), 0, 0, 0, 10));\n\n        testSplitPhaseText = text("", 14, BLUE, true);\n        testSplitPhaseText.setGravity(Gravity.CENTER);\n        testSplitPhaseText.setPadding(dp(12), dp(10), dp(12), dp(10));\n        outer.addView(testSplitPhaseText, margin(lp(-1, -2), 0, 0, 0, 10));\n\n        Button setEnlargement = compactButton("IMPOSTA INGRANDIMENTO");\n        setEnlargement.setOnClickListener(v -> startActivity(new Intent(this, EnlargementActivity.class).putExtra("mode", "setup")));\n        outer.addView(setEnlargement, margin(lp(-1, dp(46)), 0, 0, 0, 10));\n\n        LinearLayout exposure = card();\n''','SINGOLO/SPLIT selector and phase card')

rep(main,
'''        TextView contrastGuide = text("Leggi il provino dal CHIARO allo SCURO: se trovi prima i BIANCHI giusti → AUMENTA il contrasto; se trovi prima i NERI giusti → DIMINUISCI il contrasto. Se bianchi e neri sono giusti nello stesso gradino → CONTRASTO GIUSTO.", 12, darkroomMode ? RED : TEXT_PRIMARY, false);\n        contrastGuide.setPadding(dp(12), dp(10), dp(12), dp(10));\n        contrastGuide.setBackground(roundRect(darkroomMode ? Color.rgb(28,0,0) : Color.rgb(35,40,44), 9, 1, darkroomMode ? RED : BORDER));\n        exposure.addView(contrastGuide, margin(lp(-1,-2), 0, 8, 0, 0));\n''',
'''        testContrastGuide = text("Leggi il provino dal CHIARO allo SCURO: se trovi prima i BIANCHI giusti → AUMENTA il contrasto; se trovi prima i NERI giusti → DIMINUISCI il contrasto. Se bianchi e neri sono giusti nello stesso gradino → CONTRASTO GIUSTO.", 12, darkroomMode ? RED : TEXT_PRIMARY, false);\n        testContrastGuide.setPadding(dp(12), dp(10), dp(12), dp(10));\n        testContrastGuide.setBackground(roundRect(darkroomMode ? Color.rgb(28,0,0) : Color.rgb(35,40,44), 9, 1, darkroomMode ? RED : BORDER));\n        exposure.addView(testContrastGuide, margin(lp(-1,-2), 0, 8, 0, 0));\n''','contrast guide field')

rep(main,
'''        outer.addView(note, lp(-1, -2));\n        return outer;\n    }\n\n    private LinearLayout buildLogPanel() {\n''',
'''        outer.addView(note, lp(-1, -2));\n        refreshSplitProvinoUi();\n        return outer;\n    }\n\n    private LinearLayout buildLogPanel() {\n''','initial Split Grade UI refresh')

# -----------------------------------------------------------------------------
# Split Provino state-machine helpers.
# -----------------------------------------------------------------------------
state_helpers = r'''    private boolean isSplitProvino() {
        return provinoFlow == PROVINO_SPLIT_SOFT || provinoFlow == PROVINO_SPLIT_HARD;
    }

    private void persistSplitProvinoState() {
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putInt("provinoFlow", provinoFlow)
                .putInt("splitProvinoSoftYellow", ExposureRecipe.snap5(splitSoftYellow))
                .putInt("splitProvinoSoftMs", splitSoftChosenMs <= 0 ? 0 : snap(splitSoftChosenMs, 500, 36_000_000))
                .putInt("splitProvinoSoftStrip", splitSoftChosenStrip)
                .putInt("splitProvinoHardMagenta", ExposureRecipe.snap5(splitHardMagenta))
                .putInt("splitProvinoHardMs", splitHardChosenMs <= 0 ? 0 : snap(splitHardChosenMs, 500, 36_000_000))
                .putInt("splitProvinoHardStrip", splitHardChosenStrip)
                .putString("splitProvinoReturnFilterType", ExposureRecipe.normalizeFilter(splitReturnFilterType))
                .putInt("splitProvinoReturnFilterValue", ExposureRecipe.snap5(splitReturnFilterValue))
                .putInt("splitProvinoReturnTestWidthMs", snap(splitReturnTestWidthMs, 500, 30_000))
                .apply();
    }

    private void markTestResultHandled(long testAt) {
        if (testAt > 0L) getSharedPreferences("ui", MODE_PRIVATE).edit().putLong("lastTestChooserShownAt", testAt).apply();
        refreshPendingTestStripChoiceUi();
    }

    private void markCurrentTestResultHandled() {
        long testAt = getSharedPreferences("log_session", MODE_PRIVATE).getLong("lastTestAt", 0L);
        markTestResultHandled(testAt);
    }

    private void invalidateSplitHardChoice() {
        splitHardChosenMs = 0;
        splitHardChosenStrip = -1;
    }

    private void startSplitProvino() {
        if (armed || provinoFlow != PROVINO_SINGLE) {
            if (provinoFlow == PROVINO_SPLIT_SOFT || provinoFlow == PROVINO_SPLIT_HARD) refreshSplitProvinoUi();
            return;
        }
        markCurrentTestResultHandled();
        splitReturnFilterType = testBaseFilterType;
        splitReturnFilterValue = testBaseFilterValue;
        splitReturnTestWidthMs = testWidthMs;
        provinoFlow = PROVINO_SPLIT_SOFT;
        splitSoftYellow = 60;
        splitSoftChosenMs = 0;
        splitSoftChosenStrip = -1;
        splitHardMagenta = 180;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.FILTER_YELLOW;
        testBaseFilterValue = splitSoftYellow;
        persistTestBaseFilter();
        persistSplitProvinoState();
        refreshSplitProvinoUi();
        setStatusPresentation("SPLIT GRADE — FASE 1 DI 2", "Trova sperimentalmente il tempo morbido. Nessuna conversione automatica.", BLUE);
    }

    private void requestSingleProvinoMode() {
        if (armed || provinoFlow == PROVINO_SINGLE) return;
        showAppConfirmDialog("ANNULLARE IL PROVINO SPLIT GRADE?",
                "La ricetta di stampa esistente non verrà modificata. Le scelte provvisorie del nuovo provino verranno abbandonate.",
                "TORNA A SINGOLO", this::cancelSplitProvino, "CONTINUA SPLIT");
    }

    private void cancelSplitProvino() {
        provinoFlow = PROVINO_SINGLE;
        splitSoftChosenMs = 0;
        splitSoftChosenStrip = -1;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.normalizeFilter(splitReturnFilterType);
        testBaseFilterValue = ExposureRecipe.snap5(splitReturnFilterValue);
        testWidthMs = snap(splitReturnTestWidthMs, 500, 30_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit()
                .putInt("testWidthMs", testWidthMs)
                .putString("testBaseFilterType", testBaseFilterType)
                .putInt("testBaseFilterValue", testBaseFilterValue)
                .apply();
        persistSplitProvinoState();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        refreshTestBaseFilterUi();
        updateCumulativeTimes();
        refreshSplitProvinoUi();
        setStatusPresentation("PROVINO SINGOLO", "Valori precedenti ripristinati. Nessuna ricetta di stampa modificata.", BLUE);
    }

    private void prepareHardProvinoFromSoftChoice() {
        if (splitSoftChosenMs <= 0) return;
        provinoFlow = PROVINO_SPLIT_HARD;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.FILTER_MAGENTA;
        testBaseFilterValue = splitHardMagenta;
        persistTestBaseFilter();
        persistSplitProvinoState();
        refreshSplitProvinoUi();
        setStatusPresentation("SPLIT GRADE — FASE 2 DI 2",
                "Usa una nuova striscia. Il morbido scelto verrà applicato prima su tutta la carta; poi partirà il provino duro.", BLUE);
    }

    private void reviewSoftProvino() {
        provinoFlow = PROVINO_SPLIT_SOFT;
        invalidateSplitHardChoice();
        testBaseFilterType = ExposureRecipe.FILTER_YELLOW;
        testBaseFilterValue = splitSoftYellow;
        if (splitSoftChosenMs > 0) testWidthMs = snap(splitSoftChosenMs, 500, 30_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("testWidthMs", testWidthMs).apply();
        persistTestBaseFilter();
        persistSplitProvinoState();
        if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
        updateCumulativeTimes();
        refreshSplitProvinoUi();
        setStatusPresentation("RIVEDI IL MORBIDO", "La precedente scelta dura è stata invalidata e deve essere ricontrollata.", BLUE);
    }

    private void redoCurrentProvino(long testAt, boolean hard) {
        markTestResultHandled(testAt);
        if (hard) {
            invalidateSplitHardChoice();
            persistSplitProvinoState();
            setStatusPresentation("RIFAI IL DURO",
                    "Morbido conservato. Modifica tempo centrale, intervallo o magenta; usa una nuova striscia e premi ARMA.", BLUE);
        } else {
            splitSoftChosenMs = 0;
            splitSoftChosenStrip = -1;
            invalidateSplitHardChoice();
            persistSplitProvinoState();
            setStatusPresentation("REIMPOSTA IL MORBIDO",
                    "Modifica tempo, intervallo o giallo e ripeti il provino. Nessuna stampa è stata creata.", BLUE);
        }
        refreshSplitProvinoUi();
    }

    private void refreshSplitProvinoUi() {
        boolean split = isSplitProvino();
        if (testSingleModeButton != null) {
            boolean active = provinoFlow == PROVINO_SINGLE;
            testSingleModeButton.setBackground(roundRect(active ? BLUE : BUTTON, 9, 1, active ? BLUE : BORDER));
            testSingleModeButton.setTextColor(active ? Color.BLACK : TEXT_PRIMARY);
        }
        if (testSplitModeButton != null) {
            boolean active = split;
            testSplitModeButton.setBackground(roundRect(active ? SPLIT_VIVA_MAGENTA : BUTTON, 9, 1, active ? SPLIT_VIVA_MAGENTA : BORDER));
            testSplitModeButton.setTextColor(active ? Color.WHITE : TEXT_PRIMARY);
        }
        if (testSplitPhaseText != null) {
            testSplitPhaseText.setVisibility(split ? View.VISIBLE : View.GONE);
            if (provinoFlow == PROVINO_SPLIT_SOFT) {
                testSplitPhaseText.setText("FASE 1 DI 2 — TROVA IL MORBIDO\nImposta Y" + splitSoftYellow + ", M0. Scegli il tempo che rende soprattutto i toni chiari.");
                testSplitPhaseText.setBackground(roundRect(darkroomMode ? Color.rgb(24,0,0) : Color.rgb(32,36,40), 9, 1, darkroomMode ? RED : AMBER));
            } else if (provinoFlow == PROVINO_SPLIT_HARD) {
                testSplitPhaseText.setText("FASE 2 DI 2 — TROVA IL DURO\nNuova striscia: prima applica il morbido scelto su tutta la carta. Poi imposta Y0, M" + splitHardMagenta + ". Scegli il miglior equilibrio di ombre e neri.");
                testSplitPhaseText.setBackground(roundRect(darkroomMode ? Color.rgb(24,0,0) : Color.rgb(32,36,40), 9, 1, darkroomMode ? RED : SPLIT_VIVA_MAGENTA));
            }
        }
        if (testContrastGuide != null) testContrastGuide.setVisibility(split ? View.GONE : View.VISIBLE);
        if (testPromptText != null) {
            if (provinoFlow == PROVINO_SPLIT_SOFT) testPromptText.setText("Tempo centrale · MORBIDO");
            else if (provinoFlow == PROVINO_SPLIT_HARD) testPromptText.setText("Tempo centrale · DURO");
            else testPromptText.setText(testPromptDescription());
        }
        if (testStepText != null) {
            testStepText.setText(split ? (TimingMath.normalizeMethod(timingMethod) + " · " + TimingMath.stepLabel(timingMethod) + " · " + testCount + " strisce") : testStepDescription());
        }
        if (testPendingChoiceButton != null && hasPendingTestStripChoice()) {
            testPendingChoiceButton.setText(provinoFlow == PROVINO_SPLIT_SOFT ? "SCEGLI IL TEMPO MORBIDO"
                    : (provinoFlow == PROVINO_SPLIT_HARD ? "SCEGLI IL TEMPO DURO" : "SCEGLI STRISCIA DEL PROVINO"));
        }
        if (actionButton != null && mode == MODE_TEST && !armed) {
            if (provinoFlow == PROVINO_SPLIT_SOFT) actionButton.setText("ARMA FASE 1 · MORBIDO · " + testCount + " STRISCE");
            else if (provinoFlow == PROVINO_SPLIT_HARD) actionButton.setText("ARMA FASE 2 · BASE MORBIDA + DURO");
        }
        refreshTestBaseFilterUi();
    }

'''
rep(main,
'''    private String testStripMethodButtonLabel() {\n''',
state_helpers + '''    private String testStripMethodButtonLabel() {\n''','Split Grade state machine helpers')

# In Split mode the filter TYPE is fixed by the phase; its value remains editable.
rep(main,
'''    private void showTestBaseFilterDialog() {\n        if (darkroomMode || armed) return;\n        String[] choices = {"NESSUNO", "MAGENTA (M)", "GIALLO (Y)"};\n''',
'''    private void showTestBaseFilterDialog() {\n        if (darkroomMode || armed) return;\n        if (provinoFlow == PROVINO_SPLIT_SOFT) { showTestBaseFilterValueDialog(ExposureRecipe.FILTER_YELLOW); return; }\n        if (provinoFlow == PROVINO_SPLIT_HARD) { showTestBaseFilterValueDialog(ExposureRecipe.FILTER_MAGENTA); return; }\n        String[] choices = {"NESSUNO", "MAGENTA (M)", "GIALLO (Y)"};\n''','lock Split filter type to current phase')

rep(main,
'''        refreshTestBaseFilterUi();\n    }\n\n    private void showTestBaseFilterDialog() {\n''',
'''        if (provinoFlow == PROVINO_SPLIT_SOFT) {\n            splitSoftYellow = ExposureRecipe.snap5(testBaseFilterValue);\n            invalidateSplitHardChoice();\n            persistSplitProvinoState();\n        } else if (provinoFlow == PROVINO_SPLIT_HARD) {\n            splitHardMagenta = ExposureRecipe.snap5(testBaseFilterValue);\n            persistSplitProvinoState();\n        }\n        refreshTestBaseFilterUi();\n        refreshSplitProvinoUi();\n    }\n\n    private void showTestBaseFilterDialog() {\n''','filter changes update dependent Split state')

# Old invalid total-time constraint must not block experimentally found Split times.
rep(main,
'''        if (printSequence.hasSplit()) {\n            printSequence.split.sanitize();\n            if (printSequence.split.totalMs() > printWidthMs) {\n                setStatusPresentation("ATTENZIONE", "SPLIT GRADE: morbida + dura non possono superare la base " + formatTime(printWidthMs), RED);\n                return false;\n            }\n        }\n''',
'''        if (printSequence.hasSplit()) {\n            // I due tempi Split Grade sono esposizioni sperimentali distinte.\n            // Non esiste alcun vincolo rispetto al vecchio tempo singolo.\n            printSequence.split.sanitize();\n        }\n''','remove invalid Split total-time constraint')

# Keep current phase instruction after generic timing refreshes and navigation updates.
rep(main,
'''        updateCumulativeTimes();\n        applyModeUi();\n    }\n\n    private TextView fStopBadge(boolean compact) {\n''',
'''        updateCumulativeTimes();\n        applyModeUi();\n        refreshSplitProvinoUi();\n    }\n\n    private TextView fStopBadge(boolean compact) {\n''','refresh Split instruction after timing change')

rep(main,
'''        if (!log) {\n            actionButton.setBackground(roundRect(print ? GREEN : BLUE, 10, 0, 0));\n            actionButton.setText(print ? (printSequence != null && !printSequence.isEmpty() ? "ARMA PIANO DI STAMPA" : "ARMA STAMPA • " + formatTime(printWidthMs))\n                    : (TimingMath.isFStop(timingMethod)\n                        ? "ARMA PROVINO • " + testCount + " STRISCE • ¼ stop"\n                        : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs)));\n        }\n    }\n''',
'''        if (!log) {\n            actionButton.setBackground(roundRect(print ? GREEN : BLUE, 10, 0, 0));\n            actionButton.setText(print ? (printSequence != null && !printSequence.isEmpty() ? "ARMA PIANO DI STAMPA" : "ARMA STAMPA • " + formatTime(printWidthMs))\n                    : (TimingMath.isFStop(timingMethod)\n                        ? "ARMA PROVINO • " + testCount + " STRISCE • ¼ stop"\n                        : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs)));\n        }\n        refreshSplitProvinoUi();\n    }\n''','refresh Split instruction after mode UI')

# Pass the preliminary whole-strip soft exposure only in phase 2.
rep(main,
'''            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_TYPE, ExposureRecipe.normalizeFilter(testBaseFilterType));\n            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_VALUE, ExposureRecipe.snap5(testBaseFilterValue));\n''',
'''            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_TYPE, ExposureRecipe.normalizeFilter(testBaseFilterType));\n            i.putExtra(SonoffArmService.EXTRA_TEST_FILTER_VALUE, ExposureRecipe.snap5(testBaseFilterValue));\n            if (provinoFlow == PROVINO_SPLIT_HARD && splitSoftChosenMs > 0) {\n                i.putExtra(SonoffArmService.EXTRA_TEST_PRE_EXPOSURE_MS, snap(splitSoftChosenMs, 500, 36_000_000));\n                i.putExtra(SonoffArmService.EXTRA_TEST_PRE_EXPOSURE_FILTER_TYPE, ExposureRecipe.FILTER_YELLOW);\n                i.putExtra(SonoffArmService.EXTRA_TEST_PRE_EXPOSURE_FILTER_VALUE, ExposureRecipe.snap5(splitSoftYellow));\n            }\n''','phase-2 whole-strip soft exposure extras')

# Completion banner knows whether the finished strip belongs to soft or hard phase.
rep(main,
'''            } else if (detail.toLowerCase(Locale.ITALY).contains("provino completato")) {\n                int countDone = session.getInt("lastTestCount", testCount);\n                title = "✓  PROVINO COMPLETATO — " + countDone + "/" + countDone;\n                detail = "Scegli la striscia da usare come punto di partenza per la stampa";\n                accent = BLUE;\n''',
'''            } else if (detail.toLowerCase(Locale.ITALY).contains("provino completato")) {\n                int countDone = session.getInt("lastTestCount", testCount);\n                if (provinoFlow == PROVINO_SPLIT_SOFT) {\n                    title = "✓  FASE 1 COMPLETATA — MORBIDO";\n                    detail = "Scegli il tempo morbido oppure reimposta la fase";\n                } else if (provinoFlow == PROVINO_SPLIT_HARD) {\n                    title = "✓  FASE 2 COMPLETATA — DURO";\n                    detail = "Ogni striscia comprende già la base morbida scelta";\n                } else {\n                    title = "✓  PROVINO COMPLETATO — " + countDone + "/" + countDone;\n                    detail = "Scegli la striscia da usare come punto di partenza per la stampa";\n                }\n                accent = BLUE;\n''','phase-aware completion banner')

# -----------------------------------------------------------------------------
# Result chooser: no recipe is created until an explicit valid strip is chosen.
# Split soft stays provisional; Split hard creates one four-field Split plan.
# -----------------------------------------------------------------------------
old_chooser_start = '''    private void maybeShowTestResultChooser(boolean forceManual) {\n'''
old_chooser_end = '''    private void disarm() {\n'''
s=rd(main); a=s.find(old_chooser_start); b=s.find(old_chooser_end,a)
if a < 0 or b < 0: raise SystemExit('v0.2.5 chooser method bounds not found')
old_block=s[a:b]
new_block=r'''    private void maybeShowTestResultChooser(boolean forceManual) {
        if (armed || mode != MODE_TEST || isFinishing()) return;
        if (forceManual) testChooserOpen = false;
        else if (testChooserOpen) return;
        if (!hasWindowFocus()) {
            new Handler(Looper.getMainLooper()).postDelayed(() -> maybeShowTestResultChooser(forceManual), 450L);
            return;
        }
        SharedPreferences session = getSharedPreferences("log_session", MODE_PRIVATE);
        long testAt = session.getLong("lastTestAt", 0L);
        if (testAt <= 0) return;
        SharedPreferences ui = getSharedPreferences("ui", MODE_PRIVATE);
        if (ui.getLong("lastTestChooserShownAt", 0L) >= testAt) return;

        final int step = session.getInt("lastTestMs", testWidthMs);
        final int n = Math.max(2, Math.min(20, session.getInt("lastTestCount", testCount)));
        int[] stored = TimingMath.fromCsv(session.getString("lastTestStripTimes", ""));
        final int[] ascending = stored.length == n ? stored : TimingMath.cumulativeSeries(session.getString("lastTestMethod", TimingMath.METHOD_SECONDS), step, n);
        final String masking = TimingMath.normalizeMaskingMethod(session.getString("lastTestStripMethod", testStripMethod));
        final int[] physical = TimingMath.physicalTargets(ascending, masking);
        final String filterType = ExposureRecipe.normalizeFilter(session.getString("lastTestBaseFilterType", ExposureRecipe.FILTER_NONE));
        final int filterValue = ExposureRecipe.snap5(session.getInt("lastTestBaseFilterValue", 0));
        testChooserOpen = true;
        showProvinoResultDialog(testAt, physical, filterType, filterValue);
    }

    private void showProvinoResultDialog(final long testAt, final int[] physical, final String filterType, final int filterValue) {
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(18), dp(16), dp(18), dp(18));
        panel.setBackground(roundRect(darkroomMode ? Color.BLACK : CARD, 14, 1, BORDER));

        String title;
        String help;
        if (provinoFlow == PROVINO_SPLIT_SOFT) {
            title = "SCEGLI IL TEMPO MORBIDO";
            help = "Quale striscia restituisce la resa desiderata soprattutto nei toni chiari?";
        } else if (provinoFlow == PROVINO_SPLIT_HARD) {
            title = "SCEGLI IL TEMPO DURO";
            help = "Ogni striscia comprende già l’esposizione morbida scelta. Quale combinazione produce il miglior equilibrio di ombre e neri?";
        } else {
            title = "PROVINO COMPLETATO — SCEGLI LA STRISCIA";
            help = "Scegli una striscia valida oppure reimposta il provino senza creare una stampa.";
        }
        panel.addView(text(title, 18, darkroomMode ? RED : TEXT_PRIMARY, true), lp(-1,-2));
        TextView note = text(help, 13, MUTED, false);
        note.setPadding(0, dp(5), 0, dp(10)); panel.addView(note, lp(-1,-2));

        final int[] selected = {-1};
        final TextView selectedText = text("Nessuna striscia selezionata", 12, BLUE, true);
        selectedText.setGravity(Gravity.CENTER);
        selectedText.setPadding(dp(6), dp(5), dp(6), dp(8));
        panel.addView(selectedText, lp(-1,-2));
        final String filterLabel = ExposureRecipe.filterLabel(filterType, filterValue);
        for (int i=0;i<physical.length;i++) {
            final int idx=i;
            Button option=compactButton((i+1)+"ª striscia   —   "+formatTime(physical[i])+("NESSUNO".equals(filterLabel)?"":" · "+filterLabel));
            option.setOnClickListener(v -> {
                selected[0]=idx;
                selectedText.setText("SELEZIONATA · "+(idx+1)+"ª · "+formatTime(physical[idx]));
            });
            panel.addView(option, margin(lp(-1,dp(47)),0,0,0,6));
        }

        if (provinoFlow == PROVINO_SINGLE) {
            Button choose=compactButton("SCEGLI LA STRISCIA");
            choose.setBackground(roundRect(BLUE,9,0,0)); choose.setTextColor(Color.BLACK);
            choose.setOnClickListener(v -> {
                if(selected[0]<0){Toast.makeText(this,"Seleziona prima una striscia",Toast.LENGTH_SHORT).show();return;}
                int imported=snap(physical[selected[0]],500,36_000_000);
                markTestResultHandled(testAt);
                exposureRecipe=new ExposureRecipe();
                exposureRecipe.originalBaseMs=imported;
                exposureRecipe.operationalBaseMs=imported;
                exposureRecipe.filterType=filterType;
                exposureRecipe.filterValue=filterValue;
                exposureRecipe.densityQuarterSteps=0;
                exposureRecipe.globalQuarterStops=0;
                exposureRecipe.baseChosenAt=System.currentTimeMillis();
                printSequence=new PrintSequence();
                getSharedPreferences("ui",MODE_PRIVATE).edit()
                        .putString("exposureRecipe",exposureRecipe.encode())
                        .putString("printSequence","").apply();
                dialog.dismiss();
                updatePrintSequenceUi();
                setMode(MODE_PRINT);
                setPrintTime(imported);
                setStatusPresentation("DAL PROVINO — "+formatTime(imported)+("NESSUNO".equals(filterLabel)?"":" · "+filterLabel),
                        "Tempo e filtrazione trasferiti alla stampa.",GREEN);
            });
            panel.addView(choose, margin(lp(-1,dp(52)),0,8,0,0));
            Button reset=compactButton("NESSUNA MI CONVINCE — REIMPOSTA PROVINO");
            reset.setTextColor(darkroomMode?RED:BLUE);
            reset.setOnClickListener(v -> {
                markTestResultHandled(testAt);
                dialog.dismiss();
                setStatusPresentation("REIMPOSTA PROVINO", "Modifica filtrazione, tempo, passo o numero di strisce e ripeti. Nessuna stampa è stata creata.", BLUE);
            });
            panel.addView(reset, margin(lp(-1,dp(50)),0,7,0,0));
            Button later=compactButton("NON ORA"); later.setOnClickListener(v->dialog.dismiss());
            panel.addView(later, margin(lp(-1,dp(47)),0,7,0,0));
        } else if (provinoFlow == PROVINO_SPLIT_SOFT) {
            Button next=compactButton("CONTINUA AL DURO");
            next.setBackground(roundRect(SPLIT_VIVA_MAGENTA,9,0,0)); next.setTextColor(Color.WHITE);
            next.setOnClickListener(v -> {
                if(selected[0]<0){Toast.makeText(this,"Seleziona prima il tempo morbido",Toast.LENGTH_SHORT).show();return;}
                if(!ExposureRecipe.FILTER_YELLOW.equals(filterType)){
                    Toast.makeText(this,"La fase morbida richiede il filtro giallo",Toast.LENGTH_LONG).show();return;
                }
                splitSoftChosenMs=snap(physical[selected[0]],500,36_000_000);
                splitSoftChosenStrip=selected[0]+1;
                splitSoftYellow=filterValue;
                invalidateSplitHardChoice();
                markTestResultHandled(testAt);
                persistSplitProvinoState();
                dialog.dismiss();
                prepareHardProvinoFromSoftChoice();
            });
            panel.addView(next, margin(lp(-1,dp(52)),0,8,0,0));
            Button reset=compactButton("NESSUNA MI CONVINCE — REIMPOSTA");
            reset.setOnClickListener(v->{dialog.dismiss();redoCurrentProvino(testAt,false);});
            panel.addView(reset, margin(lp(-1,dp(49)),0,7,0,0));
            Button cancel=compactButton("ANNULLA");
            cancel.setOnClickListener(v->{markTestResultHandled(testAt);dialog.dismiss();cancelSplitProvino();});
            panel.addView(cancel, margin(lp(-1,dp(47)),0,7,0,0));
        } else {
            Button create=compactButton("CREA STAMPA SPLIT GRADE");
            create.setBackground(roundRect(SPLIT_VIVA_MAGENTA,9,0,0)); create.setTextColor(Color.WHITE);
            create.setOnClickListener(v -> {
                if(selected[0]<0){Toast.makeText(this,"Seleziona prima il tempo duro",Toast.LENGTH_SHORT).show();return;}
                if(!ExposureRecipe.FILTER_MAGENTA.equals(filterType)){
                    Toast.makeText(this,"La fase dura richiede il filtro magenta",Toast.LENGTH_LONG).show();return;
                }
                splitHardChosenMs=snap(physical[selected[0]],500,36_000_000);
                splitHardChosenStrip=selected[0]+1;
                splitHardMagenta=filterValue;
                markTestResultHandled(testAt);
                persistSplitProvinoState();
                dialog.dismiss();
                createSplitPrintFromProvino();
            });
            panel.addView(create, margin(lp(-1,dp(52)),0,8,0,0));
            Button redo=compactButton("RIFAI IL DURO");
            redo.setOnClickListener(v->{dialog.dismiss();redoCurrentProvino(testAt,true);});
            panel.addView(redo, margin(lp(-1,dp(48)),0,7,0,0));
            Button soft=compactButton("RIVEDI IL MORBIDO");
            soft.setOnClickListener(v->{markTestResultHandled(testAt);dialog.dismiss();reviewSoftProvino();});
            panel.addView(soft, margin(lp(-1,dp(48)),0,7,0,0));
            Button cancel=compactButton("ANNULLA");
            cancel.setOnClickListener(v->{markTestResultHandled(testAt);dialog.dismiss();cancelSplitProvino();});
            panel.addView(cancel, margin(lp(-1,dp(47)),0,7,0,0));
        }

        dialog.setContentView(panel);
        dialog.setOnDismissListener(d->{testChooserOpen=false;refreshPendingTestStripChoiceUi();refreshSplitProvinoUi();});
        Window w=dialog.getWindow(); if(w!=null)w.setBackgroundDrawableResource(android.R.color.transparent);
        dialog.show(); if(w!=null)w.setLayout((int)(getResources().getDisplayMetrics().widthPixels*0.94f),(int)(getResources().getDisplayMetrics().heightPixels*0.88f));
    }

    private void createSplitPrintFromProvino() {
        if (splitSoftChosenMs <= 0 || splitHardChosenMs <= 0) return;
        SplitGradePlan plan=new SplitGradePlan();
        plan.enabled=true;
        plan.softYellow=ExposureRecipe.snap5(splitSoftYellow);
        plan.softMs=snap(splitSoftChosenMs,500,36_000_000);
        plan.hardMagenta=ExposureRecipe.snap5(splitHardMagenta);
        plan.hardMs=snap(splitHardChosenMs,500,36_000_000);
        plan.sanitize();
        PrintSequence next=new PrintSequence();
        next.split=plan;
        // New experimentally determined base: do not silently inherit old Dodge/Burn.
        printSequence=next;
        getSharedPreferences("ui",MODE_PRIVATE).edit().putString("printSequence",printSequence.encode()).apply();
        persistPrintSequence();

        int softMs=plan.softMs, hardMs=plan.hardMs, sy=plan.softYellow, hm=plan.hardMagenta;
        provinoFlow=PROVINO_SINGLE;
        testBaseFilterType=ExposureRecipe.normalizeFilter(splitReturnFilterType);
        testBaseFilterValue=ExposureRecipe.snap5(splitReturnFilterValue);
        testWidthMs=snap(splitReturnTestWidthMs,500,30_000);
        persistSplitProvinoState();
        refreshTestBaseFilterUi();
        setMode(MODE_PRINT);
        updatePrintSequenceUi();
        setStatusPresentation("SPLIT GRADE DAL PROVINO",
                "MORBIDO · "+sy+"Y / 0M · "+formatTime(softMs)+"  +  DURO · 0Y / "+hm+"M · "+formatTime(hardMs)+". Due esposizioni consecutive, tempi indipendenti.", GREEN);
    }

'''
wr(main, s[:a] + new_block + s[b:])
print('v0.2.5 OK result chooser/state transfer', flush=True)

# Pending chooser button label follows the current phase.
rep(main,
'''        testPendingChoiceButton.setVisibility(pending ? View.VISIBLE : View.GONE);\n        testPendingChoiceButton.setEnabled(pending && !armed);\n''',
'''        testPendingChoiceButton.setVisibility(pending ? View.VISIBLE : View.GONE);\n        if (pending) testPendingChoiceButton.setText(provinoFlow == PROVINO_SPLIT_SOFT ? "SCEGLI IL TEMPO MORBIDO" : (provinoFlow == PROVINO_SPLIT_HARD ? "SCEGLI IL TEMPO DURO" : "SCEGLI STRISCIA DEL PROVINO"));\n        testPendingChoiceButton.setEnabled(pending && !armed);\n''','phase-aware pending chooser button')

# -----------------------------------------------------------------------------
# SONOFF test engine: preliminary whole-strip soft exposure before hard steps.
# It stays one service cycle, keeping safelight OFF and requiring a new physical
# button press after the explicit filter-change instruction.
# -----------------------------------------------------------------------------
rep(service,
'''    public static final String EXTRA_TEST_FILTER_TYPE = "test_filter_type";\n    public static final String EXTRA_TEST_FILTER_VALUE = "test_filter_value";\n''',
'''    public static final String EXTRA_TEST_FILTER_TYPE = "test_filter_type";\n    public static final String EXTRA_TEST_FILTER_VALUE = "test_filter_value";\n    public static final String EXTRA_TEST_PRE_EXPOSURE_MS = "test_pre_exposure_ms";\n    public static final String EXTRA_TEST_PRE_EXPOSURE_FILTER_TYPE = "test_pre_exposure_filter_type";\n    public static final String EXTRA_TEST_PRE_EXPOSURE_FILTER_VALUE = "test_pre_exposure_filter_value";\n''','service pre-exposure extras')

rep(service,
'''    private volatile String testBaseFilterType = ExposureRecipe.FILTER_NONE;\n    private volatile int testBaseFilterValue = 0;\n    private volatile boolean printBaseDone = false;\n''',
'''    private volatile String testBaseFilterType = ExposureRecipe.FILTER_NONE;\n    private volatile int testBaseFilterValue = 0;\n    private volatile int testPreExposureMs = 0;\n    private volatile String testPreExposureFilterType = ExposureRecipe.FILTER_NONE;\n    private volatile int testPreExposureFilterValue = 0;\n    private volatile boolean testPreExposureDone = true;\n    private volatile boolean printBaseDone = false;\n''','service pre-exposure state')

rep(service,
'''            testBaseFilterType = mode == MODE_TEST ? ExposureRecipe.normalizeFilter(intent.getStringExtra(EXTRA_TEST_FILTER_TYPE)) : ExposureRecipe.FILTER_NONE;\n            testBaseFilterValue = mode == MODE_TEST ? ExposureRecipe.snap5(intent.getIntExtra(EXTRA_TEST_FILTER_VALUE, 0)) : 0;\n            printBaseDone = false;\n''',
'''            testBaseFilterType = mode == MODE_TEST ? ExposureRecipe.normalizeFilter(intent.getStringExtra(EXTRA_TEST_FILTER_TYPE)) : ExposureRecipe.FILTER_NONE;\n            testBaseFilterValue = mode == MODE_TEST ? ExposureRecipe.snap5(intent.getIntExtra(EXTRA_TEST_FILTER_VALUE, 0)) : 0;\n            int requestedPre = mode == MODE_TEST ? intent.getIntExtra(EXTRA_TEST_PRE_EXPOSURE_MS, 0) : 0;\n            testPreExposureMs = requestedPre > 0 ? sanitizeWidth(requestedPre) : 0;\n            testPreExposureFilterType = mode == MODE_TEST ? ExposureRecipe.normalizeFilter(intent.getStringExtra(EXTRA_TEST_PRE_EXPOSURE_FILTER_TYPE)) : ExposureRecipe.FILTER_NONE;\n            testPreExposureFilterValue = mode == MODE_TEST ? ExposureRecipe.snap5(intent.getIntExtra(EXTRA_TEST_PRE_EXPOSURE_FILTER_VALUE, 0)) : 0;\n            testPreExposureDone = testPreExposureMs <= 0;\n            printBaseDone = false;\n''','load pre-exposure state')

rep(service,
'''                testPulsesMs = TimingMath.testStripPulses(testTargetsMs, testStripMethod);\n                currentPulseWidthMs = testPulsesMs.length > 0 ? testPulsesMs[0] : widthMs;\n''',
'''                testPulsesMs = TimingMath.testStripPulses(testTargetsMs, testStripMethod);\n                currentPulseWidthMs = testPreExposureMs > 0 ? testPreExposureMs : (testPulsesMs.length > 0 ? testPulsesMs[0] : widthMs);\n''','arm preliminary soft time first')

rep(service,
'''            if (mode == MODE_TEST) { String tf=ExposureRecipe.filterLabel(testBaseFilterType,testBaseFilterValue); TechnicalLog.add(this, techSessionId, "FILTRO BASE PROVINO • " + ("NESSUNO".equals(tf)?"nessuno":tf)); TechnicalLog.add(this, techSessionId, "METODO PROVINATURA • " + testStripMethod); }\n''',
'''            if (mode == MODE_TEST) {\n                String tf=ExposureRecipe.filterLabel(testBaseFilterType,testBaseFilterValue);\n                TechnicalLog.add(this, techSessionId, "FILTRO BASE PROVINO • " + ("NESSUNO".equals(tf)?"nessuno":tf));\n                TechnicalLog.add(this, techSessionId, "METODO PROVINATURA • " + testStripMethod);\n                if(testPreExposureMs>0){\n                    String pf=ExposureRecipe.filterLabel(testPreExposureFilterType,testPreExposureFilterValue);\n                    TechnicalLog.add(this,techSessionId,"SPLIT PROVINO • BASE MORBIDA TUTTA STRISCIA • "+pf+" • "+seconds(testPreExposureMs));\n                }\n            }\n''','technical log Split pre-exposure')

rep(service,
'''            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) {\n                msg = "SPLIT GRADE ARMATO — GIALLO " + printSequence.split.softYellow + " · " + seconds(printSequence.split.softMs) + dodgeStatusSuffix(PrintCorrection.PHASE_SOFT) + " — premi il pulsante fisico";\n            } else {\n                msg = mode == MODE_PRINT ? "ARMATO — premi il pulsante fisico" : "PROVINO ARMATO — premi il pulsante fisico una volta";\n            }\n            broadcast(STATE_ARMED, msg);\n            updateNotification(msg);\n            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) scheduleVoiceInstruction(splitPhasePrompt(PrintCorrection.PHASE_SOFT));\n''',
'''            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) {\n                msg = "SPLIT GRADE ARMATO — GIALLO " + printSequence.split.softYellow + " · " + seconds(printSequence.split.softMs) + dodgeStatusSuffix(PrintCorrection.PHASE_SOFT) + " — premi il pulsante fisico";\n            } else if (mode == MODE_TEST && testPreExposureMs > 0) {\n                msg = "SPLIT GRADE · BASE MORBIDA ARMATA — " + testPreExposureFilterValue + "Y / 0M · " + seconds(testPreExposureMs) + " — premi il pulsante fisico";\n            } else {\n                msg = mode == MODE_PRINT ? "ARMATO — premi il pulsante fisico" : "PROVINO ARMATO — premi il pulsante fisico una volta";\n            }\n            broadcast(STATE_ARMED, msg);\n            updateNotification(msg);\n            if (mode == MODE_PRINT && printSequence != null && printSequence.hasSplit()) scheduleVoiceInstruction(splitPhasePrompt(PrintCorrection.PHASE_SOFT));\n            else if (mode == MODE_TEST && testPreExposureMs > 0) scheduleVoiceInstruction(testPreExposurePrompt());\n''','arm prompt for whole-strip soft exposure')

rep(service,
'''                    String msg = mode == MODE_PRINT\n                            ? printExposureMessage()\n                            : (TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — fascia finale " + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod)) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs));\n''',
'''                    String msg = mode == MODE_PRINT\n                            ? printExposureMessage()\n                            : (!testPreExposureDone ? "ESPOSIZIONE MORBIDA SU TUTTA LA STRISCIA — " + seconds(testPreExposureMs)\n                            : (TimingMath.isFStop(timingMethod) ? "PROVINO DURO " + current + "/" + count + " — fascia finale " + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod)) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs)));\n''','exposure message distinguishes preliminary soft')

service_helpers = r'''    private String testPreExposurePrompt() {
        return "Esposizione morbida su tutta la nuova striscia. Imposta giallo " + testPreExposureFilterValue
                + ". Azzera il magenta. Mantieni il cyan a zero. Tempo morbido: " + seconds(testPreExposureMs) + ".";
    }

    private String testHardTransitionPrompt() {
        return "Esposizione morbida completata. Azzera il giallo. Imposta magenta " + testBaseFilterValue
                + ". Mantieni il cyan a zero. Premi il pulsante fisico per iniziare il provino duro.";
    }

'''
rep(service,
'''    private void onExposureFinished() {\n''',
service_helpers + '''    private void onExposureFinished() {\n''','Split test voice helpers')

rep(service,
'''    private void onExposureFinished() {\n        if (completing.get()) return;\n        seenOn.set(false);\n\n        if (mode == MODE_PRINT && printSequence != null && !printSequence.isEmpty()) {\n''',
'''    private void onExposureFinished() {\n        if (completing.get()) return;\n        seenOn.set(false);\n\n        if (mode == MODE_TEST && testPreExposureMs > 0 && !testPreExposureDone) {\n            testPreExposureDone = true;\n            cancelPoll();\n            try {\n                currentPulseWidthMs = testPulsesMs.length > 0 ? testPulsesMs[0] : widthMs;\n                configurePulseVerified(currentPulseWidthMs);\n                TechnicalLog.add(this, techSessionId, "SPLIT PROVINO • base morbida completata • attesa cambio filtro • prossimo impulso duro " + seconds(currentPulseWidthMs));\n                String transition = testHardTransitionPrompt();\n                broadcast(STATE_WAITING_SPLIT, transition);\n                updateNotification(transition);\n                scheduleVoiceInstruction(transition);\n                startPolling(180);\n            } catch (Exception e) {\n                fail("Base morbida completata, ma preparazione del provino duro fallita: " + readable(e));\n            }\n            return;\n        }\n\n        if (mode == MODE_PRINT && printSequence != null && !printSequence.isEmpty()) {\n''','transition from whole-strip soft to hard test')

# -----------------------------------------------------------------------------
# Static acceptance guards.
# -----------------------------------------------------------------------------
mt=rd(main); sv=rd(service)
required_main=[
    'PROVINO_SPLIT_SOFT','PROVINO_SPLIT_HARD','SINGOLO','SPLIT GRADE',
    'FASE 1 DI 2 — TROVA IL MORBIDO','FASE 2 DI 2 — TROVA IL DURO',
    'NESSUNA MI CONVINCE — REIMPOSTA PROVINO','CONTINUA AL DURO',
    'CREA STAMPA SPLIT GRADE','RIFAI IL DURO','RIVEDI IL MORBIDO',
    'createSplitPrintFromProvino()','splitSoftChosenMs','splitHardChosenMs',
    'next.split=plan','plan.softYellow','plan.softMs','plan.hardMagenta','plan.hardMs',
    'Nessuna conversione automatica','Non esiste alcun vincolo rispetto al vecchio tempo singolo',
    'EXTRA_TEST_PRE_EXPOSURE_MS','private static final String APP_VERSION = "0.13.8";'
]
for needle in required_main:
    if needle not in mt: raise SystemExit('v0.2.5 Main guard missing: '+needle)
required_service=[
    'EXTRA_TEST_PRE_EXPOSURE_MS','testPreExposureDone','ESPOSIZIONE MORBIDA SU TUTTA LA STRISCIA',
    'Azzera il giallo. Imposta magenta','Mantieni il cyan a zero',
    'STATE_WAITING_SPLIT','configurePulseVerified(currentPulseWidthMs)'
]
for needle in required_service:
    if needle not in sv: raise SystemExit('v0.2.5 Service guard missing: '+needle)
for forbidden in [
    'morbida + dura non possono superare la base',
]:
    if forbidden in mt: raise SystemExit('v0.2.5 forbidden legacy Split constraint remains: '+forbidden)
# Keep the historical number of strips and core timing method; do not introduce Color 3.
if 'private int testCount = 7;' not in mt: raise SystemExit('v0.2.5 test strip count default changed')
if 'Color 3' in mt or 'COLOR3' in mt or 'color3' in mt: raise SystemExit('v0.2.5 unexpected Color 3 compensation')
if 'TimingMath.testStripPulses(testTargetsMs, testStripMethod)' not in sv: raise SystemExit('v0.2.5 existing test pulse engine lost')
print('v0.2.5 TRANSFORM OK — guided Split Grade provino engine, single provino preserved', flush=True)
