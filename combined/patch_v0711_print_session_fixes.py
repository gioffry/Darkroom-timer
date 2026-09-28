#!/usr/bin/env python3
"""Darkroom 0.7.11: session fixes from 2026-09-28 print test.

Changes:
1) VOL- focus can be toggled with the screen off while the Timer was the active
   screen before display sleep. The bridge is short-lived, screen-off only and
   stops itself as soon as the display becomes interactive again.
2) New seconds test-strip pattern BASE + PASSO, e.g. base 7 s and step 1 s ->
   final strips 7, 8, 9, 10, 11, 12 s. It deliberately uses COPRIRE so the base
   exposure is physically made first over the whole strip, then equal increments.
3) Log density is LPL-specific: FILTRO DENSITÀ is ATTIVO / NON ATTIVO, not a
   numeric legacy density value. Exact old payload structure remains readable.

No change to MINIR2 local-Inching ownership or 0.7.10 VOL+ screen-off logic.
"""

from pathlib import Path

ROOT = Path("combined/src/main/java/it/darkroom/timer")
MAIN = ROOT / "MainActivity.java"
SERVICE = ROOT / "SonoffArmService.java"
MATH = ROOT / "TimingMath.java"
JPEG = ROOT / "JpegCardRenderer.java"

main = MAIN.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
math = MATH.read_text(encoding="utf-8")
jpeg = JPEG.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# TimingMath: exact linear final exposure targets for BASE + PASSO.
# ---------------------------------------------------------------------------
anchor = """    public static int[] cumulativeFStopSeries(int firstStripMs, int count) {"""
method = r'''    public static int[] baseStepSecondsSeries(int baseMs, int stepMs, int count) {
        int n = Math.max(0, count);
        int[] out = new int[n];
        int base = snap500(baseMs, 500, 36_000_000);
        int step = snap500(stepMs, 500, 36_000_000);
        for (int i = 0; i < n; i++) {
            long target = (long) base + (long) step * i;
            out[i] = snap500((int)Math.min(36_000_000L, target), 500, 36_000_000);
        }
        return out;
    }

'''
if anchor not in math:
    raise SystemExit("v0.7.11: TimingMath insertion anchor not found")
math = math.replace(anchor, method + anchor, 1)

# ---------------------------------------------------------------------------
# MainActivity: BASE + PASSO state and UI.
# ---------------------------------------------------------------------------
old = """    private static final int PROVINO_SINGLE = 0;
    private static final int PROVINO_SPLIT_SOFT = 1;
    private static final int PROVINO_SPLIT_HARD = 2;"""
new = """    private static final int PROVINO_SINGLE = 0;
    private static final int PROVINO_SPLIT_SOFT = 1;
    private static final int PROVINO_SPLIT_HARD = 2;
    private static final String TEST_SECONDS_CUMULATIVE = "CUMULATIVO";
    private static final String TEST_SECONDS_BASE_STEP = "BASE_PASSO";"""
if old not in main:
    raise SystemExit("v0.7.11: provino constants anchor not found")
main = main.replace(old, new, 1)

old = """    private Button testBaseFilterButton;
    private Button testStripMethodButton;
    private Button testPendingChoiceButton;"""
new = """    private Button testBaseFilterButton;
    private Button testStripMethodButton;
    private Button testSecondsPatternButton;
    private LinearLayout testBaseTimeRow;
    private TextView testBaseTimeText;
    private Button testPendingChoiceButton;"""
if old not in main:
    raise SystemExit("v0.7.11: test UI fields anchor not found")
main = main.replace(old, new, 1)

old = """    private String testStripMethod = TimingMath.MASK_REVEAL;
    private int provinoFlow = PROVINO_SINGLE;"""
new = """    private String testStripMethod = TimingMath.MASK_REVEAL;
    private String testSecondsPattern = TEST_SECONDS_CUMULATIVE;
    private int testBaseMs = 7000;
    private boolean screenOffFocusBridgeRequested = false;
    private int provinoFlow = PROVINO_SINGLE;"""
if old not in main:
    raise SystemExit("v0.7.11: test state fields anchor not found")
main = main.replace(old, new, 1)

old = """        testPauseMs = p.getInt("testPauseMs", 2000);
        testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("testStripMethod", TimingMath.MASK_REVEAL));
        provinoFlow = Math.max(PROVINO_SINGLE, Math.min(PROVINO_SPLIT_HARD, p.getInt("provinoFlow", PROVINO_SINGLE)));"""
new = """        testPauseMs = p.getInt("testPauseMs", 2000);
        testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("testStripMethod", TimingMath.MASK_REVEAL));
        testSecondsPattern = normalizeTestSecondsPattern(p.getString("testSecondsPattern", TEST_SECONDS_CUMULATIVE));
        testBaseMs = snap(p.getInt("testBaseMs", 7000), 500, 30_000);
        provinoFlow = Math.max(PROVINO_SINGLE, Math.min(PROVINO_SPLIT_HARD, p.getInt("provinoFlow", PROVINO_SINGLE)));"""
if old not in main:
    raise SystemExit("v0.7.11: prefs load anchor not found")
main = main.replace(old, new, 1)

# Stop the temporary screen-off focus bridge when this Activity comes back.
old = """    @Override protected void onStart() {
        super.onStart();
        activityStarted = true;
        IntentFilter f = new IntentFilter(SonoffArmService.BROADCAST_STATE);"""
new = """    @Override protected void onStart() {
        super.onStart();
        activityStarted = true;
        if (screenOffFocusBridgeRequested) {
            screenOffFocusBridgeRequested = false;
            Intent stopFocusKeys = new Intent(this, SonoffArmService.class)
                    .setAction(SonoffArmService.ACTION_DISABLE_SCREEN_OFF_FOCUS);
            startServiceCompat(stopFocusKeys);
        }
        IntentFilter f = new IntentFilter(SonoffArmService.BROADCAST_STATE);"""
if old not in main:
    raise SystemExit("v0.7.11: MainActivity onStart anchor not found")
main = main.replace(old, new, 1)

# Insert helper immediately before onStop (0.7.9 placed dispatchKeyEvent here).
marker = """    @Override protected void onStop() {"""
focus_bridge = r'''    // SCREEN_OFF_FOCUS_0711
    // Only arm the background VOL- bridge when Android is actually turning the
    // display off. Leaving the Timer for another app does not activate it.
    private void maybeStartScreenOffFocusBridge() {
        if (armed || mode == MODE_LOG) return;
        DeviceConfig d = (device != null && device.isValid()) ? device : DeviceConfig.load(this);
        if (d == null || !d.isValid()) return;
        try {
            android.os.PowerManager pm = (android.os.PowerManager) getSystemService(POWER_SERVICE);
            if (pm == null || pm.isInteractive()) return;
            screenOffFocusBridgeRequested = true;
            Intent focusKeys = new Intent(this, SonoffArmService.class)
                    .setAction(SonoffArmService.ACTION_ENABLE_SCREEN_OFF_FOCUS);
            startServiceCompat(focusKeys);
        } catch (Exception ignored) {}
    }

'''
if marker not in main:
    raise SystemExit("v0.7.11: MainActivity onStop marker not found")
main = main.replace(marker, focus_bridge + marker, 1)

old = """    @Override protected void onStop() {
        activityStarted = false;
        reconnectHandler.removeCallbacks(reconnectRunnable);"""
new = """    @Override protected void onStop() {
        maybeStartScreenOffFocusBridge();
        activityStarted = false;
        reconnectHandler.removeCallbacks(reconnectRunnable);"""
if old not in main:
    raise SystemExit("v0.7.11: MainActivity onStop body anchor not found")
main = main.replace(old, new, 1)

# Seconds-pattern helpers before the existing test-strip method helpers.
marker = """    private String testStripMethodButtonLabel() {"""
pattern_helpers = r'''    private static String normalizeTestSecondsPattern(String value) {
        return TEST_SECONDS_BASE_STEP.equals(value) ? TEST_SECONDS_BASE_STEP : TEST_SECONDS_CUMULATIVE;
    }

    private boolean isBaseStepSeconds() {
        return provinoFlow == PROVINO_SINGLE
                && !TimingMath.isFStop(timingMethod)
                && TEST_SECONDS_BASE_STEP.equals(normalizeTestSecondsPattern(testSecondsPattern));
    }

    private String testSecondsPatternButtonLabel() {
        return "SERIE IN SECONDI · " + (isBaseStepSeconds() ? "BASE + PASSO" : "CUMULATIVA");
    }

    private String currentTestStepLabel() {
        if (isBaseStepSeconds()) {
            return "BASE " + formatTime(testBaseMs) + " + PASSO " + formatTime(testWidthMs);
        }
        return TimingMath.stepLabel(timingMethod);
    }

    private void refreshTestSecondsPatternUi() {
        boolean secondsSingle = provinoFlow == PROVINO_SINGLE && !TimingMath.isFStop(timingMethod);
        if (testSecondsPatternButton != null) {
            testSecondsPatternButton.setVisibility(secondsSingle ? View.VISIBLE : View.GONE);
            testSecondsPatternButton.setText(testSecondsPatternButtonLabel());
        }
        if (testBaseTimeRow != null) testBaseTimeRow.setVisibility(isBaseStepSeconds() ? View.VISIBLE : View.GONE);
        if (testBaseTimeText != null) testBaseTimeText.setText("BASE " + formatTime(testBaseMs));
    }

    private void showTestSecondsPatternDialog() {
        if (armed || provinoFlow != PROVINO_SINGLE || TimingMath.isFStop(timingMethod)) return;
        String[] choices = {
                "CUMULATIVA — es. passo 2 s → 2 · 4 · 6 · 8…",
                "BASE + PASSO — es. base 7 s + 1 s → 7 · 8 · 9 · 10…"
        };
        showAppChoiceDialog("SERIE DEL PROVINO IN SECONDI", choices, which -> {
            testSecondsPattern = which == 1 ? TEST_SECONDS_BASE_STEP : TEST_SECONDS_CUMULATIVE;
            if (TEST_SECONDS_BASE_STEP.equals(testSecondsPattern)) {
                // This mode is explicitly: base over the whole sheet FIRST, then
                // equal added exposures while progressively covering the strip.
                testStripMethod = TimingMath.MASK_COVER;
                if (testBaseMs <= 0) testBaseMs = 7000;
                if (testWidthMs > 5000) testWidthMs = 1000;
            }
            getSharedPreferences("ui", MODE_PRIVATE).edit()
                    .putString("testSecondsPattern", testSecondsPattern)
                    .putInt("testBaseMs", testBaseMs)
                    .putInt("testWidthMs", testWidthMs)
                    .putString("testStripMethod", testStripMethod)
                    .apply();
            if (testTimeText != null) testTimeText.setText(formatTime(testWidthMs));
            refreshTestStripMethodUi();
            refreshTestSecondsPatternUi();
            updateTimingUi();
        }, "ANNULLA");
    }

'''
if marker not in main:
    raise SystemExit("v0.7.11: seconds-pattern helper anchor not found")
main = main.replace(marker, pattern_helpers + marker, 1)

# BASE+PASSO must physically run with COPRIRE.
old = """    private void showTestStripMethodDialog() {
        if (armed) return;
        String[] choices = {"""
new = """    private void showTestStripMethodDialog() {
        if (armed) return;
        if (isBaseStepSeconds()) {
            testStripMethod = TimingMath.MASK_COVER;
            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("testStripMethod", testStripMethod).apply();
            refreshTestStripMethodUi();
            Toast.makeText(this, "BASE + PASSO usa COPRIRE: prima la base su tutta la carta, poi gli incrementi.", Toast.LENGTH_LONG).show();
            return;
        }
        String[] choices = {"""
if old not in main:
    raise SystemExit("v0.7.11: test-strip dialog anchor not found")
main = main.replace(old, new, 1)

# Add the seconds pattern selector after masking method selector.
old = """        testStripMethodButton = compactButton(testStripMethodButtonLabel());
        testStripMethodButton.setOnClickListener(v -> showTestStripMethodDialog());
        exposure.addView(testStripMethodButton, margin(lp(-1, dp(50)), 0, 8, 0, 0));
        testPendingChoiceButton = compactButton("SCEGLI STRISCIA DEL PROVINO");"""
new = """        testStripMethodButton = compactButton(testStripMethodButtonLabel());
        testStripMethodButton.setOnClickListener(v -> showTestStripMethodDialog());
        exposure.addView(testStripMethodButton, margin(lp(-1, dp(50)), 0, 8, 0, 0));
        testSecondsPatternButton = compactButton(testSecondsPatternButtonLabel());
        testSecondsPatternButton.setOnClickListener(v -> showTestSecondsPatternDialog());
        exposure.addView(testSecondsPatternButton, margin(lp(-1, dp(50)), 0, 8, 0, 0));
        testPendingChoiceButton = compactButton("SCEGLI STRISCIA DEL PROVINO");"""
if old not in main:
    raise SystemExit("v0.7.11: pattern button insertion anchor not found")
main = main.replace(old, new, 1)

# Add a base-time stepper. Existing main time stepper becomes PASSO in this mode.
import re
pattern = re.compile(r'''(\s*plus\.setOnClickListener\(v -> adjustTestTime\(\+1\)\);\n\s*exposure\.addView\(selector[^;]*\);\n)(\s*testCumulativeText = text\(cumulativeTimes\(\), 13, [A-Z_]+, true\);)''')
addition = r'''\1
        testBaseTimeRow = new LinearLayout(this);
        testBaseTimeRow.setOrientation(LinearLayout.HORIZONTAL);
        testBaseTimeRow.setGravity(Gravity.CENTER);
        Button baseMinus = smallButton("−");
        Button basePlus = smallButton("+");
        testBaseTimeText = text("BASE " + formatTime(testBaseMs), 24, BLUE, true);
        testBaseTimeText.setGravity(Gravity.CENTER);
        testBaseTimeRow.addView(baseMinus, lp(dp(62), dp(54)));
        testBaseTimeRow.addView(testBaseTimeText, lp(0, dp(58), 1f));
        testBaseTimeRow.addView(basePlus, lp(dp(62), dp(54)));
        baseMinus.setOnClickListener(v -> adjustTestBaseTime(-1));
        basePlus.setOnClickListener(v -> adjustTestBaseTime(+1));
        exposure.addView(testBaseTimeRow, margin(lp(-1, -2), 0, 5, 0, 0));

\2'''
main, n = pattern.subn(addition, main, count=1)
if n != 1:
    idx = main.find("adjustTestTime(+1)")
    snippet = main[max(0, idx - 300):idx + 500] if idx >= 0 else "adjustTestTime(+1) not present"
    raise SystemExit("v0.7.11: base-time row insertion anchor not found after prior patches:\n" + snippet)

old = """        outer.addView(note, lp(-1, -2));
        refreshSplitProvinoUi();
        return outer;"""
new = """        outer.addView(note, lp(-1, -2));
        refreshTestSecondsPatternUi();
        refreshSplitProvinoUi();
        return outer;"""
if old not in main:
    raise SystemExit("v0.7.11: buildTestPanel final anchor not found")
main = main.replace(old, new, 1)

# Keep pattern UI synced when entering/leaving Split Grade.
old = """        if (actionButton != null && mode == MODE_TEST && !armed) {
            if (provinoFlow == PROVINO_SPLIT_SOFT) actionButton.setText("ARMA FASE 1 · MORBIDO · " + testCount + " STRISCE");
            else if (provinoFlow == PROVINO_SPLIT_HARD) actionButton.setText("ARMA FASE 2 · BASE MORBIDA + DURO");
        }
        refreshTestBaseFilterUi();"""
new = """        if (actionButton != null && mode == MODE_TEST && !armed) {
            if (provinoFlow == PROVINO_SPLIT_SOFT) actionButton.setText("ARMA FASE 1 · MORBIDO · " + testCount + " STRISCE");
            else if (provinoFlow == PROVINO_SPLIT_HARD) actionButton.setText("ARMA FASE 2 · BASE MORBIDA + DURO");
        }
        refreshTestSecondsPatternUi();
        refreshTestBaseFilterUi();"""
if old not in main:
    raise SystemExit("v0.7.11: refreshSplitProvinoUi anchor not found")
main = main.replace(old, new, 1)

# Adjust/set the common BASE independently from the added PASSO.
old = """    private void setPrintTime(int ms) {"""
base_adjust = r'''    private void adjustTestBaseTime(int direction) {
        if (armed || !isBaseStepSeconds()) return;
        setTestBaseTime(testBaseMs + direction * 500);
    }

    private void setTestBaseTime(int ms) {
        if (armed) return;
        testBaseMs = snap(ms, 500, 30_000);
        getSharedPreferences("ui", MODE_PRIVATE).edit().putInt("testBaseMs", testBaseMs).apply();
        if (testBaseTimeText != null) testBaseTimeText.setText("BASE " + formatTime(testBaseMs));
        updateCumulativeTimes();
        applyModeUi();
    }

'''
if old not in main:
    raise SystemExit("v0.7.11: base adjust insertion anchor not found")
main = main.replace(old, base_adjust + old, 1)

# Exact target sequence, labels and UI descriptions.
old = """    private int[] currentTestStripTargets() {
        return TimingMath.cumulativeSeries(timingMethod, testWidthMs, testCount);
    }"""
new = """    private int[] currentTestStripTargets() {
        if (isBaseStepSeconds()) return TimingMath.baseStepSecondsSeries(testBaseMs, testWidthMs, testCount);
        return TimingMath.cumulativeSeries(timingMethod, testWidthMs, testCount);
    }"""
if old not in main:
    raise SystemExit("v0.7.11: currentTestStripTargets anchor not found")
main = main.replace(old, new, 1)

old = """        if (testFStopBadge != null) testFStopBadge.setVisibility(fstop ? View.VISIBLE : View.GONE);
        updateCumulativeTimes();"""
new = """        if (testFStopBadge != null) testFStopBadge.setVisibility(fstop ? View.VISIBLE : View.GONE);
        refreshTestSecondsPatternUi();
        updateCumulativeTimes();"""
if old not in main:
    raise SystemExit("v0.7.11: updateTimingUi anchor not found")
main = main.replace(old, new, 1)

old = """    private String testPromptDescription() {
        return TimingMath.isFStop(timingMethod) ? "Tempo prima striscia" : "Incremento del provino";
    }

    private String testStepDescription() {
        return TimingMath.isFStop(timingMethod) ? "Progressione cumulativa • passo ¼ stop" : "Ogni esposizione ha lo stesso tempo";
    }"""
new = """    private String testPromptDescription() {
        if (TimingMath.isFStop(timingMethod)) return "Tempo prima striscia";
        return isBaseStepSeconds() ? "Passo dopo la base" : "Incremento del provino";
    }

    private String testStepDescription() {
        if (TimingMath.isFStop(timingMethod)) return "Progressione cumulativa • passo ¼ stop";
        return isBaseStepSeconds()
                ? "Base comune + progressione lineare in secondi • metodo COPRIRE"
                : "Ogni esposizione ha lo stesso tempo";
    }"""
if old not in main:
    raise SystemExit("v0.7.11: test descriptions anchor not found")
main = main.replace(old, new, 1)

# Arm button text for the new pattern.
old = """: (TimingMath.isFStop(timingMethod)
                        ? "ARMA PROVINO • " + testCount + " STRISCE • ¼ stop"
                        : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs)));"""
new = """: (TimingMath.isFStop(timingMethod)
                        ? "ARMA PROVINO • " + testCount + " STRISCE • ¼ stop"
                        : (isBaseStepSeconds()
                            ? "ARMA PROVINO • BASE " + formatTime(testBaseMs) + " + " + formatTime(testWidthMs)
                            : "ARMA PROVINO • " + testCount + " × " + formatTime(testWidthMs))));"""
if old not in main:
    raise SystemExit("v0.7.11: arm button text anchor not found")
main = main.replace(old, new, 1)

# Pass exact variable-pulse semantics and human-readable log label to Service.
old = """            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);
            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());
            i.putExtra(SonoffArmService.EXTRA_TEST_MASKING_METHOD, TimingMath.normalizeMaskingMethod(testStripMethod));"""
new = """            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);
            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());
            i.putExtra(SonoffArmService.EXTRA_TEST_VARIABLE_PULSES, isBaseStepSeconds());
            i.putExtra(SonoffArmService.EXTRA_TEST_STEP_LABEL, currentTestStepLabel());
            i.putExtra(SonoffArmService.EXTRA_TEST_MASKING_METHOD, TimingMath.normalizeMaskingMethod(testStripMethod));"""
if old not in main:
    raise SystemExit("v0.7.11: arm extras anchor not found")
main = main.replace(old, new, 1)

# ---------------------------------------------------------------------------
# MainActivity Log: LPL density is binary, not a numeric legacy field.
# ---------------------------------------------------------------------------
marker = """    private static String joinBits(List<String> bits) {"""
density_helpers = r'''    private static boolean logDensityActive(String raw) {
        String s = raw == null ? "" : raw.trim().toUpperCase(Locale.ITALY);
        if (s.isEmpty() || s.equals("0") || s.equals("D0") || s.contains("NON ATTIV") || s.equals("OFF") || s.equals("NO")) return false;
        if (s.contains("ATTIV") || s.equals("ON") || s.equals("SI") || s.equals("SÌ") || s.equals("YES")) return true;
        try {
            String numeric = s.startsWith("D") ? s.substring(1) : s;
            numeric = numeric.replace(',', '.');
            return Double.parseDouble(numeric) > 0.0;
        } catch (Exception ignored) {
            return false;
        }
    }

    private static String logDensityLabel(boolean active) {
        return active ? "ATTIVO" : "NON ATTIVO";
    }

'''
if marker not in main:
    raise SystemExit("v0.7.11: log density helper anchor not found")
main = main.replace(marker, density_helpers + marker, 1)

old = """        if (e.density != null && !e.density.trim().isEmpty()) filterBits.add("D " + e.density.trim());"""
new = """        if (e.density != null && !e.density.trim().isEmpty()) filterBits.add("FILTRO DENSITÀ " + logDensityLabel(logDensityActive(e.density)));"""
if old not in main:
    raise SystemExit("v0.7.11: log list density anchor not found")
main = main.replace(old, new, 1)

old = """        e.magenta = "0";
        e.yellow = "0";
        e.density = "0";"""
new = """        e.magenta = "0";
        e.yellow = "0";
        e.density = "NON ATTIVO";"""
if old not in main:
    raise SystemExit("v0.7.11: new log defaults anchor not found")
main = main.replace(old, new, 1)

old = """            if (ExposureRecipe.FILTER_MAGENTA.equals(autoRecipe.filterType)) e.magenta=String.valueOf(autoRecipe.filterValue);
            if (ExposureRecipe.FILTER_YELLOW.equals(autoRecipe.filterType)) e.yellow=String.valueOf(autoRecipe.filterValue);
            e.density=autoRecipe.densityLabel();
        }"""
new = """            if (ExposureRecipe.FILTER_MAGENTA.equals(autoRecipe.filterType)) e.magenta=String.valueOf(autoRecipe.filterValue);
            if (ExposureRecipe.FILTER_YELLOW.equals(autoRecipe.filterType)) e.yellow=String.valueOf(autoRecipe.filterValue);
            // The LPL 7451 density filter is a physical binary state in the Log.
            // Do not copy the separate "Allunga tempi" neutral-density calculation here.
        }"""
if old not in main:
    raise SystemExit("v0.7.11: auto recipe density anchor not found")
main = main.replace(old, new, 1)

# Replace free-text density editor with ATTIVO / NON ATTIVO buttons.
old = """        final EditText aperture = editField("Diaframma f/", entry.aperture);
        final EditText magenta = editField("Magenta", entry.magenta);
        final EditText yellow = editField("Yellow", entry.yellow);
        final EditText density = editField("Densità", entry.density);
        final EditText paper = editField("Carta", entry.paper == null || entry.paper.trim().isEmpty() ? "Fomaspeed Variant 311 RC lucida" : entry.paper);"""
new = """        final EditText aperture = editField("Diaframma f/", entry.aperture);
        final EditText magenta = editField("Magenta", entry.magenta);
        final EditText yellow = editField("Yellow", entry.yellow);
        final boolean[] densityActive = {logDensityActive(entry.density)};
        final EditText paper = editField("Carta", entry.paper == null || entry.paper.trim().isEmpty() ? "Fomaspeed Variant 311 RC lucida" : entry.paper);"""
if old not in main:
    raise SystemExit("v0.7.11: log editor fields anchor not found")
main = main.replace(old, new, 1)

old = """        panel.addView(magenta, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(yellow, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(density, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(paper, margin(lp(-1, dp(52)), 0, 0, 0, 8));"""
new = """        panel.addView(magenta, margin(lp(-1, dp(52)), 0, 0, 0, 8));
        panel.addView(yellow, margin(lp(-1, dp(52)), 0, 0, 0, 8));

        panel.addView(text("FILTRO DENSITÀ LPL", 12, MUTED, true), margin(lp(-1, -2), 0, 2, 0, 4));
        LinearLayout densityRow = new LinearLayout(this);
        densityRow.setOrientation(LinearLayout.HORIZONTAL);
        final Button densityOff = compactButton("NON ATTIVO");
        final Button densityOn = compactButton("ATTIVO");
        final Runnable densityStyle = () -> {
            densityOff.setBackground(roundRect(!densityActive[0] ? LOG_ACCENT : BUTTON, 8, 1, !densityActive[0] ? LOG_ACCENT : BORDER));
            densityOn.setBackground(roundRect(densityActive[0] ? LOG_ACCENT : BUTTON, 8, 1, densityActive[0] ? LOG_ACCENT : BORDER));
            densityOff.setTextColor(!densityActive[0] ? Color.WHITE : TEXT_PRIMARY);
            densityOn.setTextColor(densityActive[0] ? Color.WHITE : TEXT_PRIMARY);
        };
        densityOff.setOnClickListener(v -> { densityActive[0] = false; densityStyle.run(); });
        densityOn.setOnClickListener(v -> { densityActive[0] = true; densityStyle.run(); });
        densityRow.addView(densityOff, margin(lp(0, dp(48), 1f), 0, 0, dp(4), 0));
        densityRow.addView(densityOn, margin(lp(0, dp(48), 1f), dp(4), 0, 0, 0));
        densityStyle.run();
        panel.addView(densityRow, margin(lp(-1, -2), 0, 0, 0, 8));

        panel.addView(paper, margin(lp(-1, dp(52)), 0, 0, 0, 8));"""
if old not in main:
    raise SystemExit("v0.7.11: log density row anchor not found")
main = main.replace(old, new, 1)

count = main.count('entry.density = density.getText().toString().trim();')
if count != 3:
    raise SystemExit(f"v0.7.11: expected 3 density save assignments, found {count}")
main = main.replace('entry.density = density.getText().toString().trim();',
                    'entry.density = logDensityLabel(densityActive[0]);')

# ---------------------------------------------------------------------------
# Service: variable seconds pulses + screen-off VOL- focus bridge.
# ---------------------------------------------------------------------------
old = """    public static final String ACTION_START_INTERLOCK = "it.darkroom.timer.START_SAFELIGHT_INTERLOCK";
    public static final String ACTION_STOP_INTERLOCK = "it.darkroom.timer.STOP_SAFELIGHT_INTERLOCK";"""
new = """    public static final String ACTION_START_INTERLOCK = "it.darkroom.timer.START_SAFELIGHT_INTERLOCK";
    public static final String ACTION_STOP_INTERLOCK = "it.darkroom.timer.STOP_SAFELIGHT_INTERLOCK";
    public static final String ACTION_ENABLE_SCREEN_OFF_FOCUS = "it.darkroom.timer.ENABLE_SCREEN_OFF_FOCUS";
    public static final String ACTION_DISABLE_SCREEN_OFF_FOCUS = "it.darkroom.timer.DISABLE_SCREEN_OFF_FOCUS";"""
if old not in service:
    raise SystemExit("v0.7.11: service action constants anchor not found")
service = service.replace(old, new, 1)

old = """    public static final String EXTRA_TEST_TARGETS = "test_targets_ms";
    public static final String EXTRA_TEST_MASKING_METHOD = "test_masking_method";"""
new = """    public static final String EXTRA_TEST_TARGETS = "test_targets_ms";
    public static final String EXTRA_TEST_VARIABLE_PULSES = "test_variable_pulses";
    public static final String EXTRA_TEST_STEP_LABEL = "test_step_label";
    public static final String EXTRA_TEST_MASKING_METHOD = "test_masking_method";"""
if old not in service:
    raise SystemExit("v0.7.11: service test extras anchor not found")
service = service.replace(old, new, 1)

old = """    private volatile String timingMethod = TimingMath.METHOD_SECONDS;
    private volatile String testStripMethod = TimingMath.MASK_REVEAL;
    private volatile int[] testTargetsMs = new int[0];"""
new = """    private volatile String timingMethod = TimingMath.METHOD_SECONDS;
    private volatile String testStripMethod = TimingMath.MASK_REVEAL;
    private volatile boolean testVariablePulses = false;
    private volatile String testStepLabel = TimingMath.STEP_SECONDS;
    private volatile int[] testTargetsMs = new int[0];"""
if old not in service:
    raise SystemExit("v0.7.11: service test fields anchor not found")
service = service.replace(old, new, 1)

# v0.7.10 added the screen-off VOL+ fields immediately before wakeLock.
old = """    private PowerManager.WakeLock wakeLock;"""
focus_fields = r'''    // SCREEN_OFF_FOCUS_0711
    private volatile MediaSession screenOffFocusSession;
    private volatile MediaPlayer screenOffFocusPlayer;
    private volatile AudioManager screenOffFocusAudioManager;
    private final AudioManager.OnAudioFocusChangeListener screenOffFocusFocusListener = focusChange -> { };
    private final Handler screenOffFocusHandler = new Handler(Looper.getMainLooper());
    private final AtomicBoolean screenOffFocusActive = new AtomicBoolean(false);
    private final AtomicBoolean screenOffFocusCommandInFlight = new AtomicBoolean(false);
    private volatile int screenOffFocusBaselineVolume = -1;
    private volatile int screenOffFocusRestoreVolume = -1;
    private final Runnable screenOffFocusProbe = new Runnable() {
        @Override public void run() {
            if (!screenOffFocusActive.get()) return;
            try {
                PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
                if (pm != null && pm.isInteractive()) {
                    disableScreenOffFocusKeys(true);
                    return;
                }
                AudioManager am = screenOffFocusAudioManager;
                if (am != null) {
                    int now = am.getStreamVolume(AudioManager.STREAM_MUSIC);
                    int before = screenOffFocusBaselineVolume;
                    if (before >= 0 && now < before) {
                        try { am.setStreamVolume(AudioManager.STREAM_MUSIC, before, 0); } catch (Exception ignored) {}
                        TechnicalLog.add(SonoffArmService.this, techSessionId,
                                "FOCUS VOL- FALLBACK screen-off • STREAM_MUSIC " + before + "→" + now);
                        requestScreenOffFocusToggle();
                    }
                }
            } catch (Exception ignored) {}
            if (screenOffFocusActive.get()) screenOffFocusHandler.postDelayed(this, 80L);
        }
    };

'''
if old not in service:
    raise SystemExit("v0.7.11: service wakeLock anchor not found")
service = service.replace(old, focus_fields + old, 1)

# Add screen-off focus actions before the normal ARM branch and tear bridge down on ARM.
old = """        String action = intent.getAction();
        if (ACTION_ARM_PRINT.equals(action) || ACTION_ARM_TEST.equals(action)) {
            interlockActive = false;"""
new = """        String action = intent.getAction();
        if (ACTION_ENABLE_SCREEN_OFF_FOCUS.equals(action)) {
            enableScreenOffFocusKeys();
            return START_NOT_STICKY;
        } else if (ACTION_DISABLE_SCREEN_OFF_FOCUS.equals(action)) {
            disableScreenOffFocusKeys(true);
            return START_NOT_STICKY;
        } else if (ACTION_ARM_PRINT.equals(action) || ACTION_ARM_TEST.equals(action)) {
            disableScreenOffFocusKeys(false);
            interlockActive = false;"""
if old not in service:
    raise SystemExit("v0.7.11: service onStart action anchor not found")
service = service.replace(old, new, 1)

old = """            timingMethod = TimingMath.normalizeMethod(intent.getStringExtra(EXTRA_TIMING_METHOD));
            testStripMethod = TimingMath.normalizeMaskingMethod(intent.getStringExtra(EXTRA_TEST_MASKING_METHOD));
            if (mode == MODE_TEST) {"""
new = """            timingMethod = TimingMath.normalizeMethod(intent.getStringExtra(EXTRA_TIMING_METHOD));
            testStripMethod = TimingMath.normalizeMaskingMethod(intent.getStringExtra(EXTRA_TEST_MASKING_METHOD));
            testVariablePulses = mode == MODE_TEST && intent.getBooleanExtra(EXTRA_TEST_VARIABLE_PULSES, false);
            String requestedStepLabel = mode == MODE_TEST ? intent.getStringExtra(EXTRA_TEST_STEP_LABEL) : null;
            testStepLabel = requestedStepLabel == null || requestedStepLabel.trim().isEmpty()
                    ? TimingMath.stepLabel(timingMethod) : requestedStepLabel.trim();
            if (mode == MODE_TEST) {"""
if old not in service:
    raise SystemExit("v0.7.11: service parse test settings anchor not found")
service = service.replace(old, new, 1)

# Technical log and preparation label describe exact final strip targets for variable seconds.
old = """: (TimingMath.isFStop(timingMethod) ? "PROVINO F-STOP · ¼ stop • strisce " + TimingMath.seriesLabel(testTargetsMs) + " • pausa " + seconds(pauseMs) : "PROVINO richiesto " + count + " × " + seconds(widthMs) + " • pausa " + seconds(pauseMs)));"""
new = """: ((TimingMath.isFStop(timingMethod) || testVariablePulses)
                        ? "PROVINO " + testStepLabel + " • strisce " + TimingMath.seriesLabel(testTargetsMs) + " • pausa " + seconds(pauseMs)
                        : "PROVINO richiesto " + count + " × " + seconds(widthMs) + " • pausa " + seconds(pauseMs)));"""
if old not in service:
    raise SystemExit("v0.7.11: service technical session label anchor not found")
service = service.replace(old, new, 1)

old = """: (TimingMath.isFStop(timingMethod) ? "Preparo provino: " + count + " strisce • ¼ stop" : "Preparo provino: " + count + " × " + seconds(widthMs)));"""
new = """: ((TimingMath.isFStop(timingMethod) || testVariablePulses)
                        ? "Preparo provino: " + count + " strisce • " + testStepLabel
                        : "Preparo provino: " + count + " × " + seconds(widthMs)));"""
if old not in service:
    raise SystemExit("v0.7.11: service preparation label anchor not found")
service = service.replace(old, new, 1)

# Every subsequent seconds BASE+PASSO pulse must use the exact pulse array, same
# as F-stop already does.
old = """                if (TimingMath.isFStop(timingMethod) && testPulsesMs.length == count) {
                    currentPulseWidthMs = testPulsesMs[completed];"""
new = """                if ((TimingMath.isFStop(timingMethod) || testVariablePulses) && testPulsesMs.length == count) {
                    currentPulseWidthMs = testPulsesMs[completed];"""
count = service.count(old)
if count != 1:
    raise SystemExit(f"v0.7.11: expected one next-pulse branch, found {count}")
service = service.replace(old, new, 1)

# Status messages should show final strip target + actual pulse for variable seconds too.
service = service.replace(
    'TimingMath.isFStop(timingMethod) ? "PROVINO DURO " + current + "/" + count + " — fascia finale "',
    '(TimingMath.isFStop(timingMethod) || testVariablePulses) ? "PROVINO DURO " + current + "/" + count + " — fascia finale "',
    1
)
service = service.replace(
    'String exposing = TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — fascia finale "',
    'String exposing = (TimingMath.isFStop(timingMethod) || testVariablePulses) ? "PROVINO " + current + "/" + count + " — fascia finale "',
    1
)
# v0.7.9 generalized the VOL+ path with another F-stop ternary.
old = """                        : (TimingMath.isFStop(timingMethod)
                            ? "PROVINO DURO " + current + "/" + count + " — fascia finale " """
if old in service:
    service = service.replace(
        old,
        """                        : ((TimingMath.isFStop(timingMethod) || testVariablePulses)
                            ? "PROVINO DURO " + current + "/" + count + " — fascia finale " """,
        1
    )

old = """            e.putString("lastTestStep", TimingMath.stepLabel(timingMethod));"""
new = """            e.putString("lastTestStep", testStepLabel);"""
if old not in service:
    raise SystemExit("v0.7.11: service log step anchor not found")
service = service.replace(old, new, 1)

# Screen-off focus bridge methods before normal polling helpers.
marker = """    private void startPolling(long initialDelayMs) {"""
focus_methods = r'''    private void enableScreenOffFocusKeys() {
        disableScreenOffFocusKeys(false);
        try {
            PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
            if (pm == null || pm.isInteractive()) {
                stopSelf();
                return;
            }
            DeviceConfig d = DeviceConfig.load(this);
            if (d == null || !d.isValid()) {
                stopSelf();
                return;
            }
            device = d;
            startForeground(NOTIFICATION_ID, notification("FOCUS • VOL− attivo a schermo spento"));

            AudioManager am = (AudioManager) getSystemService(AUDIO_SERVICE);
            screenOffFocusAudioManager = am;
            if (am != null) {
                try {
                    am.requestAudioFocus(screenOffFocusFocusListener, AudioManager.STREAM_MUSIC,
                            AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK);
                } catch (Exception ignored) {}
                int max = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int current = am.getStreamVolume(AudioManager.STREAM_MUSIC);
                screenOffFocusRestoreVolume = current;
                // Leave one physical downward step available for the Samsung fallback.
                if (max > 0 && current <= 0) {
                    am.setStreamVolume(AudioManager.STREAM_MUSIC, 1, 0);
                    current = 1;
                }
                screenOffFocusBaselineVolume = current;
            }

            MediaSession session = new MediaSession(this, "DarkroomTimerScreenOffFocus");
            screenOffFocusSession = session;
            session.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS
                    | MediaSession.FLAG_HANDLES_TRANSPORT_CONTROLS);
            session.setCallback(new MediaSession.Callback() {}, new Handler(Looper.getMainLooper()));
            session.setPlaybackState(new PlaybackState.Builder()
                    .setActions(PlaybackState.ACTION_PLAY | PlaybackState.ACTION_PLAY_PAUSE)
                    .setState(PlaybackState.STATE_PLAYING, 0L, 1.0f)
                    .build());
            session.setPlaybackToRemote(new VolumeProvider(
                    VolumeProvider.VOLUME_CONTROL_ABSOLUTE, 100, 50) {
                @Override public void onAdjustVolume(int direction) {
                    int before = getCurrentVolume();
                    int after = Math.max(0, Math.min(getMaxVolume(), before + direction));
                    setCurrentVolume(after);
                    if (direction == AudioManager.ADJUST_LOWER || direction < 0) requestScreenOffFocusToggle();
                }
                @Override public void onSetVolumeTo(int volume) {
                    int before = getCurrentVolume();
                    int after = Math.max(0, Math.min(getMaxVolume(), volume));
                    setCurrentVolume(after);
                    if (after < before) requestScreenOffFocusToggle();
                }
            });
            session.setActive(true);

            MediaPlayer player = MediaPlayer.create(this, R.raw.darkroom_volume_keepalive);
            if (player != null) {
                player.setLooping(true);
                player.setVolume(0.0f, 0.0f);
                player.start();
                screenOffFocusPlayer = player;
            }

            screenOffFocusActive.set(true);
            screenOffFocusHandler.removeCallbacks(screenOffFocusProbe);
            screenOffFocusHandler.postDelayed(screenOffFocusProbe, 80L);
            TechnicalLog.add(this, techSessionId, "FOCUS VOL- SCREEN-OFF 0.7.11 ARMATO");
        } catch (Exception e) {
            disableScreenOffFocusKeys(true);
        }
    }

    private void requestScreenOffFocusToggle() {
        if (!screenOffFocusActive.get()) return;
        if (!screenOffFocusCommandInFlight.compareAndSet(false, true)) return;
        io.execute(() -> {
            try {
                DeviceConfig d = (device != null && device.isValid()) ? device : DeviceConfig.load(this);
                if (d == null || !d.isValid()) return;
                String before = SonoffHttp.infoQuick(d, 1800);
                boolean turnOn = !"on".equals(before);
                if (turnOn) {
                    SonoffHttp.pulseOff(d);
                    SonoffHttp.switchOn(d);
                } else {
                    SonoffHttp.switchOff(d);
                }
                TechnicalLog.add(this, techSessionId,
                        "FOCUS VOL- SCREEN-OFF • ingranditore " + (turnOn ? "ON" : "OFF"));
            } catch (Exception e) {
                TechnicalLog.add(this, techSessionId,
                        "ATTENZIONE FOCUS VOL- SCREEN-OFF • " + readable(e));
            } finally {
                screenOffFocusCommandInFlight.set(false);
            }
        });
    }

    private void disableScreenOffFocusKeys(boolean stopService) {
        screenOffFocusActive.set(false);
        screenOffFocusHandler.removeCallbacks(screenOffFocusProbe);

        MediaSession session = screenOffFocusSession;
        screenOffFocusSession = null;
        if (session != null) {
            try { session.setActive(false); } catch (Exception ignored) {}
            try { session.release(); } catch (Exception ignored) {}
        }

        MediaPlayer player = screenOffFocusPlayer;
        screenOffFocusPlayer = null;
        if (player != null) {
            try { player.stop(); } catch (Exception ignored) {}
            try { player.release(); } catch (Exception ignored) {}
        }

        AudioManager am = screenOffFocusAudioManager;
        screenOffFocusAudioManager = null;
        int restore = screenOffFocusRestoreVolume;
        screenOffFocusRestoreVolume = -1;
        screenOffFocusBaselineVolume = -1;
        if (am != null) {
            try {
                if (restore >= 0 && am.getStreamVolume(AudioManager.STREAM_MUSIC) != restore)
                    am.setStreamVolume(AudioManager.STREAM_MUSIC, restore, 0);
            } catch (Exception ignored) {}
            try { am.abandonAudioFocus(screenOffFocusFocusListener); } catch (Exception ignored) {}
        }

        if (stopService) {
            try { stopForeground(true); } catch (Exception ignored) {}
            stopSelf();
        }
    }

'''
if marker not in service:
    raise SystemExit("v0.7.11: service polling marker not found")
service = service.replace(marker, focus_methods + marker, 1)

# Always clean bridge on service destruction.
old = """    @Override public void onDestroy() {
        disableVolumeStartTrigger();"""
new = """    @Override public void onDestroy() {
        disableScreenOffFocusKeys(false);
        disableVolumeStartTrigger();"""
if old not in service:
    raise SystemExit("v0.7.11: service onDestroy anchor not found")
service = service.replace(old, new, 1)

# ---------------------------------------------------------------------------
# JPEG card: binary LPL density display.
# ---------------------------------------------------------------------------
old = '''                "Titolo", "Negativo", "Diaframma", "β / Scala LPL", "Magenta", "Yellow",
                "Densità", "Base operativa", "Metodo stampa", "Provino", "Metodo provino", "Carta"'''
new = '''                "Titolo", "Negativo", "Diaframma", "β / Scala LPL", "Magenta", "Yellow",
                "Filtro densità", "Base operativa", "Metodo stampa", "Provino", "Metodo provino", "Carta"'''
if old not in jpeg:
    raise SystemExit("v0.7.11: JPEG density label anchor not found")
jpeg = jpeg.replace(old, new, 1)

old = """    private static String autoDensity(LogEntry e) {
        ExposureRecipe r=ExposureRecipe.decode(e==null?"":e.recipeState); if(r.hasBase())return r.densityLabel(); return text(e==null?"":e.density,"D0");
    }"""
new = """    private static String autoDensity(LogEntry e) {
        String s = e == null || e.density == null ? "" : e.density.trim().toUpperCase(Locale.ITALY);
        if (s.isEmpty() || s.equals("0") || s.equals("D0") || s.contains("NON ATTIV") || s.equals("OFF") || s.equals("NO")) return "NON ATTIVO";
        if (s.contains("ATTIV") || s.equals("ON") || s.equals("SI") || s.equals("SÌ") || s.equals("YES")) return "ATTIVO";
        try {
            String numeric = s.startsWith("D") ? s.substring(1) : s;
            return Double.parseDouble(numeric.replace(',', '.')) > 0.0 ? "ATTIVO" : "NON ATTIVO";
        } catch (Exception ignored) {
            return "NON ATTIVO";
        }
    }"""
if old not in jpeg:
    raise SystemExit("v0.7.11: JPEG autoDensity anchor not found")
jpeg = jpeg.replace(old, new, 1)

# Internal Timer version.
if 'private static final String APP_VERSION = "0.13.23";' not in main:
    raise SystemExit("v0.7.11: expected Timer 0.13.23 base not found")
main = main.replace(
    'private static final String APP_VERSION = "0.13.23";',
    'private static final String APP_VERSION = "0.13.24";',
    1,
)

checks = [
    (main, "TEST_SECONDS_BASE_STEP"),
    (main, "BASE + PASSO"),
    (main, "EXTRA_TEST_VARIABLE_PULSES"),
    (main, "SCREEN_OFF_FOCUS_0711"),
    (main, "FILTRO DENSITÀ LPL"),
    (service, "ACTION_ENABLE_SCREEN_OFF_FOCUS"),
    (service, "FOCUS VOL- SCREEN-OFF 0.7.11 ARMATO"),
    (service, "testVariablePulses"),
    (service, "lastTestStep\", testStepLabel"),
    (math, "baseStepSecondsSeries"),
    (jpeg, "Filtro densità"),
]
for body, needle in checks:
    if needle not in body:
        raise SystemExit("v0.7.11: missing marker " + needle)

MAIN.write_text(main, encoding="utf-8")
SERVICE.write_text(service, encoding="utf-8")
MATH.write_text(math, encoding="utf-8")
JPEG.write_text(jpeg, encoding="utf-8")

print("session_fixes_0711=APPLIED")
print("vol_plus_screen_off=UNCHANGED_0710")
print("vol_minus_screen_off=FOCUS_BRIDGE_SCREEN_OFF_ONLY")
print("seconds_test_pattern=BASE_PLUS_STEP")
print("example_targets_7_plus_1=7_8_9_10_11_12")
print("base_plus_step_masking=FORCED_COVER")
print("log_density=LPL_BINARY_ACTIVE_INACTIVE")
print("legacy_log_payload=READABLE")
print("sonoff_inching_ownership=UNCHANGED")
print("timer_internal=0.13.24")
