#!/usr/bin/env python3
from pathlib import Path
import sys

work=Path(sys.argv[1]); project=work/'project'; app=project/'app'; main_dir=app/'src/main'; java=main_dir/'java/it/darkroom/timer'
manifest=main_dir/'AndroidManifest.xml'; gradle=app/'build.gradle'; build=work/'build_darkroom.py'
main=java/'MainActivity.java'; timing=java/'TimingMath.java'; service=java/'SonoffArmService.java'; logentry=java/'LogEntry.java'; logstore=java/'LogStore.java'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s,encoding='utf-8')
def rep(p,old,new,label,count=1):
    s=rd(p); n=s.count(old)
    if n<count: raise SystemExit(f'v0.13.2 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count)); print('v0.13.2 OK',label,flush=True)

for p,needle in [(manifest,'android:versionName="0.13.1"'),(manifest,'android:versionCode="62"'),(main,'private static final String APP_VERSION = "0.13.1";')]:
    if needle not in rd(p): raise SystemExit('v0.13.2 BASE v0.13.1 non riconosciuta: '+needle)
if (java/'assistant').exists() or (java/'home').exists(): raise SystemExit('v0.13.2 base non Timer-only')

# Version bump only after the exact v0.13.1 transform.
s=rd(build)
if 'VERSION_NAME = "0.13.1"' not in s or 'VERSION_CODE = "62"' not in s: raise SystemExit('v0.13.2 builder base non riconosciuta')
s=s.replace('VERSION_NAME = "0.13.1"','VERSION_NAME = "0.13.2"').replace('VERSION_CODE = "62"','VERSION_CODE = "63"')
s=s.replace('[Darkroom v0.13.1]','[Darkroom v0.13.2]').replace('versionCode 62','versionCode 63').replace(r'versionCode\s+62\b',r'versionCode\s+63\b').replace('0.13.1','0.13.2')
wr(build,s)
rep(gradle,"versionCode 62\n        versionName '0.13.1'","versionCode 63\n        versionName '0.13.2'",'Gradle version')
rep(manifest,'android:versionCode="62"\n    android:versionName="0.13.1"','android:versionCode="63"\n    android:versionName="0.13.2"','manifest version')
rep(main,'private static final String APP_VERSION = "0.13.1";','private static final String APP_VERSION = "0.13.2";','Timer footer version')

# ---------------------------------------------------------------------------
# 1) One explicit physical masking model shared by SECONDS and F-STOP.
# ---------------------------------------------------------------------------
rep(timing,
'''    public static final String STEP_SECONDS = "0,5 s";\n    public static final String STEP_FSTOP = "¼ stop";\n''',
'''    public static final String STEP_SECONDS = "0,5 s";\n    public static final String STEP_FSTOP = "¼ stop";\n    public static final String MASK_REVEAL = "SCOPRIRE";\n    public static final String MASK_COVER = "COPRIRE";\n''','masking constants')

anchor='''    public static int[] subtractivePulses(int[] ascendingTargets) {\n        int[] forward = incrementalPulses(ascendingTargets);\n        int n = forward.length;\n        int[] out = new int[n];\n        for (int i = 0; i < n; i++) out[i] = forward[n - 1 - i];\n        return out;\n    }\n'''
addition=anchor+'''\n    public static String normalizeMaskingMethod(String method) {\n        return MASK_COVER.equalsIgnoreCase(method == null ? "" : method.trim()) ? MASK_COVER : MASK_REVEAL;\n    }\n\n    /** Chronological relay pulses for the selected physical test-strip gesture. */\n    public static int[] testStripPulses(int[] ascendingTargets, String maskingMethod) {\n        return MASK_REVEAL.equals(normalizeMaskingMethod(maskingMethod))\n                ? subtractivePulses(ascendingTargets)\n                : incrementalPulses(ascendingTargets);\n    }\n\n    /** Final exposure times in physical strip order (1st strip, 2nd strip, ...). */\n    public static int[] physicalTargets(int[] ascendingTargets, String maskingMethod) {\n        if (ascendingTargets == null) return new int[0];\n        int n = ascendingTargets.length;\n        int[] out = new int[n];\n        boolean reveal = MASK_REVEAL.equals(normalizeMaskingMethod(maskingMethod));\n        for (int i = 0; i < n; i++) out[i] = ascendingTargets[reveal ? n - 1 - i : i];\n        return out;\n    }\n\n    public static int physicalTargetAt(int[] ascendingTargets, int physicalIndex, String maskingMethod) {\n        int[] physical = physicalTargets(ascendingTargets, maskingMethod);\n        if (physicalIndex < 0 || physicalIndex >= physical.length) return 0;\n        return physical[physicalIndex];\n    }\n'''
rep(timing,anchor,addition,'shared SCOPRIRE/COPRIRE math')

# ---------------------------------------------------------------------------
# 2) Provino UI: selectable SCOPRIRE/COPRIRE, default SCOPRIRE.
# ---------------------------------------------------------------------------
rep(main,'    private Button testBaseFilterButton;\n    private TextView printSequenceSummary;','    private Button testBaseFilterButton;\n    private Button testStripMethodButton;\n    private TextView printSequenceSummary;','test method button field')
rep(main,'    private int testBaseFilterValue = 0;\n    private static final int ALLUNGA_COLOR','    private int testBaseFilterValue = 0;\n    private String testStripMethod = TimingMath.MASK_REVEAL;\n    private static final int ALLUNGA_COLOR','test method state field')
rep(main,'        testPauseMs = p.getInt("testPauseMs", 2000);\n','        testPauseMs = p.getInt("testPauseMs", 2000);\n        testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("testStripMethod", TimingMath.MASK_REVEAL));\n','load test method preference')

helper='''    private String testStripMethodButtonLabel() {\n        return "METODO PROVINO · " + TimingMath.normalizeMaskingMethod(testStripMethod);\n    }\n\n    private void refreshTestStripMethodUi() {\n        testStripMethod = TimingMath.normalizeMaskingMethod(testStripMethod);\n        if (testStripMethodButton != null) testStripMethodButton.setText(testStripMethodButtonLabel());\n        updateCumulativeTimes();\n    }\n\n    private void showTestStripMethodDialog() {\n        if (armed) return;\n        String[] choices = {\n                "SCOPRIRE — parti con 1 fascia e ne scopri una in più",\n                "COPRIRE — parti tutto scoperto e copri una fascia alla volta"\n        };\n        showAppChoiceDialog("METODO DI PROVINATURA", choices, which -> {\n            testStripMethod = which == 1 ? TimingMath.MASK_COVER : TimingMath.MASK_REVEAL;\n            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("testStripMethod", testStripMethod).apply();\n            refreshTestStripMethodUi();\n        }, "ANNULLA");\n    }\n\n'''
rep(main,'    private LinearLayout buildTestPanel() {\n',helper+'    private LinearLayout buildTestPanel() {\n','test method UI helpers')
rep(main,
'''        testBaseFilterButton = compactButton(testBaseFilterButtonLabel());\n        testBaseFilterButton.setOnClickListener(v -> showTestBaseFilterDialog());\n        exposure.addView(testBaseFilterButton, margin(lp(-1, dp(50)), 0, 10, 0, 0));\n        testFStopBadge = addFStopBadge(exposure, false);\n''',
'''        testBaseFilterButton = compactButton(testBaseFilterButtonLabel());\n        testBaseFilterButton.setOnClickListener(v -> showTestBaseFilterDialog());\n        exposure.addView(testBaseFilterButton, margin(lp(-1, dp(50)), 0, 10, 0, 0));\n        testStripMethodButton = compactButton(testStripMethodButtonLabel());\n        testStripMethodButton.setOnClickListener(v -> showTestStripMethodDialog());\n        exposure.addView(testStripMethodButton, margin(lp(-1, dp(50)), 0, 8, 0, 0));\n        testFStopBadge = addFStopBadge(exposure, false);\n''','test method selector button')
rep(main,
'''    private String cumulativeTimes() {\n        return "TEMPI CUMULATIVI  " + TimingMath.seriesLabel(currentTestStripTargets());\n    }\n''',
'''    private String cumulativeTimes() {\n        int[] physical = TimingMath.physicalTargets(currentTestStripTargets(), testStripMethod);\n        return "TEMPI STRISCE · " + TimingMath.normalizeMaskingMethod(testStripMethod) + "  " + TimingMath.seriesLabel(physical);\n    }\n''','physical strip time preview')

# Pass the selected method to the timing service.
rep(main,
'''            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);\n            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());\n''',
'''            i.putExtra(SonoffArmService.EXTRA_TIMING_METHOD, timingMethod);\n            i.putExtra(SonoffArmService.EXTRA_TEST_TARGETS, currentTestStripTargets());\n            i.putExtra(SonoffArmService.EXTRA_TEST_MASKING_METHOD, TimingMath.normalizeMaskingMethod(testStripMethod));\n''','pass masking method to service')

# ---------------------------------------------------------------------------
# 3) Preferred-strip chooser: physical order, robust reappearance, clean print state.
# ---------------------------------------------------------------------------
rep(main,
'''    private void maybeShowTestResultChooser() {\n        if (armed || mode != MODE_TEST || isFinishing() || !hasWindowFocus() || testChooserOpen) return;\n''',
'''    private void maybeShowTestResultChooser() {\n        if (armed || mode != MODE_TEST || isFinishing() || testChooserOpen) return;\n        if (!hasWindowFocus()) {\n            new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 450L);\n            return;\n        }\n''','robust chooser retry')
rep(main,
'''        final int[] strips = storedStrips.length == n ? storedStrips : TimingMath.cumulativeSeries(session.getString("lastTestMethod", TimingMath.METHOD_SECONDS), step, n);\n        String[] choices = new String[n];\n        final String chosenFilterType = ExposureRecipe.normalizeFilter(session.getString("lastTestBaseFilterType", ExposureRecipe.FILTER_NONE));\n        final int chosenFilterValue = ExposureRecipe.snap5(session.getInt("lastTestBaseFilterValue", 0));\n        final String chosenFilter = ExposureRecipe.filterLabel(chosenFilterType, chosenFilterValue);\n        for (int i = 0; i < n; i++) choices[i] = (i + 1) + "ª striscia   —   " + formatTime(strips[i]) + ("NESSUNO".equals(chosenFilter) ? "" : " · " + chosenFilter);\n''',
'''        final int[] strips = storedStrips.length == n ? storedStrips : TimingMath.cumulativeSeries(session.getString("lastTestMethod", TimingMath.METHOD_SECONDS), step, n);\n        final String chosenMaskingMethod = TimingMath.normalizeMaskingMethod(session.getString("lastTestStripMethod", testStripMethod));\n        final int[] physicalStrips = TimingMath.physicalTargets(strips, chosenMaskingMethod);\n        String[] choices = new String[n];\n        final String chosenFilterType = ExposureRecipe.normalizeFilter(session.getString("lastTestBaseFilterType", ExposureRecipe.FILTER_NONE));\n        final int chosenFilterValue = ExposureRecipe.snap5(session.getInt("lastTestBaseFilterValue", 0));\n        final String chosenFilter = ExposureRecipe.filterLabel(chosenFilterType, chosenFilterValue);\n        for (int i = 0; i < n; i++) choices[i] = (i + 1) + "ª striscia   —   " + formatTime(physicalStrips[i]) + ("NESSUNO".equals(chosenFilter) ? "" : " · " + chosenFilter);\n''','chooser uses physical strip order')
rep(main,'            int imported = strips[which];\n','            int imported = physicalStrips[which];\n','chooser imports physical strip time')
rep(main,
'''            exposureRecipe.globalQuarterStops = 0;\n            exposureRecipe.baseChosenAt = System.currentTimeMillis();\n            getSharedPreferences("ui", MODE_PRIVATE).edit().putString("exposureRecipe", exposureRecipe.encode()).apply();\n            setMode(MODE_PRINT);\n''',
'''            exposureRecipe.globalQuarterStops = 0;\n            exposureRecipe.baseChosenAt = System.currentTimeMillis();\n            // A new test-strip choice starts a new single-exposure print recipe. Never inherit\n            // stale SPLIT GRADE / DODGE / BURN state from an older print.\n            printSequence = new PrintSequence();\n            getSharedPreferences("ui", MODE_PRIVATE).edit()\n                    .putString("exposureRecipe", exposureRecipe.encode())\n                    .putString("printSequence", "")\n                    .apply();\n            updatePrintSequenceUi();\n            setMode(MODE_PRINT);\n''','clear stale print/split state when choosing strip')

# ---------------------------------------------------------------------------
# 4) Service executes the chosen gesture and persists it.
# ---------------------------------------------------------------------------
rep(service,'    public static final String EXTRA_TEST_TARGETS = "test_targets_ms";\n','    public static final String EXTRA_TEST_TARGETS = "test_targets_ms";\n    public static final String EXTRA_TEST_MASKING_METHOD = "test_masking_method";\n','service masking extra')
rep(service,'    private ScheduledFuture<?> interlockTask;\n','    private ScheduledFuture<?> interlockTask;\n    private ScheduledFuture<?> safelightRestoreTask;\n','safelight retry task field')
rep(service,'    private volatile String timingMethod = TimingMath.METHOD_SECONDS;\n','    private volatile String timingMethod = TimingMath.METHOD_SECONDS;\n    private volatile String testStripMethod = TimingMath.MASK_REVEAL;\n','service test method state')
rep(service,'            timingMethod = TimingMath.normalizeMethod(intent.getStringExtra(EXTRA_TIMING_METHOD));\n','            timingMethod = TimingMath.normalizeMethod(intent.getStringExtra(EXTRA_TIMING_METHOD));\n            testStripMethod = TimingMath.normalizeMaskingMethod(intent.getStringExtra(EXTRA_TEST_MASKING_METHOD));\n','service loads masking method')
rep(service,'                testPulsesMs = TimingMath.isFStop(timingMethod) ? TimingMath.subtractivePulses(testTargetsMs) : TimingMath.incrementalPulses(testTargetsMs);\n','                testPulsesMs = TimingMath.testStripPulses(testTargetsMs, testStripMethod);\n','service pulse plan by physical method')
rep(service,'            if (mode == MODE_TEST) { String tf=ExposureRecipe.filterLabel(testBaseFilterType,testBaseFilterValue); TechnicalLog.add(this, techSessionId, "FILTRO BASE PROVINO • " + ("NESSUNO".equals(tf)?"nessuno":tf)); }\n','            if (mode == MODE_TEST) { String tf=ExposureRecipe.filterLabel(testBaseFilterType,testBaseFilterValue); TechnicalLog.add(this, techSessionId, "FILTRO BASE PROVINO • " + ("NESSUNO".equals(tf)?"nessuno":tf)); TechnicalLog.add(this, techSessionId, "METODO PROVINATURA • " + testStripMethod); }\n','log masking method')
rep(service,'? "PROVINO " + current + "/" + count + " — fascia finale " + seconds(testTargetsMs[count - current]) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs));','? "PROVINO " + current + "/" + count + " — fascia finale " + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod)) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs));','first physical target label')
rep(service,'TechnicalLog.add(this, techSessionId, "COMANDO pulse=on aggiornato • esposizione " + (completed + 1) + "/" + count + " • impulso " + seconds(currentPulseWidthMs) + " • fascia finale " + seconds(testTargetsMs[count - completed - 1]));','TechnicalLog.add(this, techSessionId, "COMANDO pulse=on aggiornato • esposizione " + (completed + 1) + "/" + count + " • impulso " + seconds(currentPulseWidthMs) + " • fascia finale " + seconds(TimingMath.physicalTargetAt(testTargetsMs, completed, testStripMethod)));','subsequent physical target log')
rep(service,'String exposing = TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — fascia finale " + seconds(testTargetsMs[count - current]) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);','String exposing = TimingMath.isFStop(timingMethod) ? "PROVINO " + current + "/" + count + " — fascia finale " + seconds(TimingMath.physicalTargetAt(testTargetsMs, current - 1, testStripMethod)) + " · impulso " + seconds(currentPulseWidthMs) : "PROVINO " + current + "/" + count + " — esposizione " + seconds(widthMs);','subsequent physical target label')
rep(service,'            e.putString("lastTestStripTimes", TimingMath.toCsv(testTargetsMs.length == count ? testTargetsMs : TimingMath.cumulativeSeries(timingMethod, widthMs, count)));\n','            e.putString("lastTestStripTimes", TimingMath.toCsv(testTargetsMs.length == count ? testTargetsMs : TimingMath.cumulativeSeries(timingMethod, widthMs, count)));\n            e.putString("lastTestStripMethod", TimingMath.normalizeMaskingMethod(testStripMethod));\n','persist masking method')

# ---------------------------------------------------------------------------
# 5) Safelight restore must remain pending until ON is really confirmed.
# ---------------------------------------------------------------------------
old_restore='''    private void restoreSafelightBestEffort() {\n        boolean captured = cycleSafelightCaptured;\n        boolean restore = restoreSafelightAfterCycle;\n        cycleSafelightCaptured = false;\n        restoreSafelightAfterCycle = false;\n        if (!captured || !restore) {\n            if (captured) TechnicalLog.add(this, techSessionId, "SAFELIGHT era OFF prima del ciclo • stato lasciato OFF");\n            return;\n        }\n        try {\n            setSafelightConfirmed(true);\n            TechnicalLog.add(this, techSessionId, mode == MODE_TEST\n                    ? "PROVINO concluso — SAFELIGHT ripristinata ON"\n                    : "SAFELIGHT ripristinata ON perché era ON prima del ciclo");\n        } catch (Exception e) {\n            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: ripristino stato iniziale fallito — " + readable(e));\n        }\n    }\n'''
new_restore='''    private void restoreSafelightBestEffort() {\n        boolean captured = cycleSafelightCaptured;\n        boolean restore = restoreSafelightAfterCycle;\n        if (!captured || !restore) {\n            if (captured) TechnicalLog.add(this, techSessionId, "SAFELIGHT era OFF prima del ciclo • stato lasciato OFF");\n            cycleSafelightCaptured = false;\n            restoreSafelightAfterCycle = false;\n            cancelSafelightRestoreRetry();\n            return;\n        }\n        try {\n            setSafelightConfirmed(true);\n            cycleSafelightCaptured = false;\n            restoreSafelightAfterCycle = false;\n            cancelSafelightRestoreRetry();\n            TechnicalLog.add(this, techSessionId, mode == MODE_TEST\n                    ? "PROVINO concluso — SAFELIGHT ripristinata ON"\n                    : "SAFELIGHT ripristinata ON perché era ON prima del ciclo");\n        } catch (Exception e) {\n            // Do NOT forget the requested restore. Keep it pending and retry while the\n            // foreground interlock service remains alive.\n            TechnicalLog.add(this, techSessionId, "ATTENZIONE SAFELIGHT: ON non ancora confermato — nuovo tentativo automatico — " + readable(e));\n            updateNotification("Ripristino luce rossa in corso…");\n            scheduleSafelightRestoreRetry();\n        }\n    }\n\n    private void scheduleSafelightRestoreRetry() {\n        if (!cycleSafelightCaptured || !restoreSafelightAfterCycle) return;\n        if (safelightRestoreTask != null && !safelightRestoreTask.isDone()) return;\n        safelightRestoreTask = io.schedule(() -> {\n            safelightRestoreTask = null;\n            restoreSafelightBestEffort();\n        }, 1000L, TimeUnit.MILLISECONDS);\n    }\n\n    private void cancelSafelightRestoreRetry() {\n        if (safelightRestoreTask != null) {\n            safelightRestoreTask.cancel(false);\n            safelightRestoreTask = null;\n        }\n    }\n'''
rep(service,old_restore,new_restore,'persistent safelight restore watchdog')

# ---------------------------------------------------------------------------
# 6) Carry masking semantics into LOG/print card without breaking old rows.
# ---------------------------------------------------------------------------
rep(logentry,'    public String testStep = TimingMath.STEP_SECONDS;\n    public String testStripTimes = "";\n','    public String testStep = TimingMath.STEP_SECONDS;\n    public String testStripTimes = "";\n    public String testStripMethod = TimingMath.MASK_REVEAL;\n','LogEntry masking field')
rep(logstore,'                    e.recipeState = f.length >= 24 ? dec(f[23]) : "";\n','                    e.recipeState = f.length >= 24 ? dec(f[23]) : "";\n                    e.testStripMethod = f.length >= 25 ? TimingMath.normalizeMaskingMethod(dec(f[24])) : TimingMath.MASK_REVEAL;\n','parse masking field backwards-compatible')
rep(logstore,'                    e.recipeState = "";\n','                    e.recipeState = "";\n                    e.testStripMethod = TimingMath.MASK_REVEAL;\n','old row masking default')
rep(logstore,'                    .append(enc(e.recipeState));\n','                    .append(enc(e.recipeState)).append(\'\\t\')\n                    .append(enc(TimingMath.normalizeMaskingMethod(e.testStripMethod)));\n','serialize masking field')

# Both quick-save branches inherit the actual test-strip gesture.
rep(main,'                e.testStripTimes = p.getString("lastTestStripTimes", "");\n','                e.testStripTimes = p.getString("lastTestStripTimes", "");\n                e.testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("lastTestStripMethod", TimingMath.MASK_REVEAL));\n','save masking method with final print',1)
# There is a second quick-save occurrence later.
s=rd(main)
needle='            e.testStripTimes = p.getString("lastTestStripTimes", "");\n        }\n\n        // Defaults for every new print card'
if needle not in s: raise SystemExit('v0.13.2 quick-save masking anchor missing')
s=s.replace(needle,'            e.testStripTimes = p.getString("lastTestStripTimes", "");\n            e.testStripMethod = TimingMath.normalizeMaskingMethod(p.getString("lastTestStripMethod", TimingMath.MASK_REVEAL));\n        }\n\n        // Defaults for every new print card',1)
wr(main,s); print('v0.13.2 OK quick-save masking method',flush=True)

rep(main,'        String strips = entry.testMs > 0 ? TimingMath.seriesLabel(stripValues) : "—";\n','        String strips = entry.testMs > 0 ? TimingMath.seriesLabel(TimingMath.physicalTargets(stripValues, entry.testStripMethod)) : "—";\n','print card physical strip order')
rep(main,'        String testMethod = entry.testMs > 0 ? TimingMath.normalizeMethod(entry.testMethod) + " · " + (entry.testStep == null || entry.testStep.trim().isEmpty() ? TimingMath.stepLabel(entry.testMethod) : entry.testStep) : "—";\n','        String testMethod = entry.testMs > 0 ? TimingMath.normalizeMethod(entry.testMethod) + " · " + (entry.testStep == null || entry.testStep.trim().isEmpty() ? TimingMath.stepLabel(entry.testMethod) : entry.testStep) + " · " + TimingMath.normalizeMaskingMethod(entry.testStripMethod) : "—";\n','print card masking label')
rep(main,'            String provino = "Provino · " + TimingMath.normalizeMethod(e.testMethod) + " · " + (e.testStep == null || e.testStep.trim().isEmpty() ? TimingMath.stepLabel(e.testMethod) : e.testStep) + "\\nStrisce: " + TimingMath.seriesLabel(strips);\n','            String provino = "Provino · " + TimingMath.normalizeMethod(e.testMethod) + " · " + (e.testStep == null || e.testStep.trim().isEmpty() ? TimingMath.stepLabel(e.testMethod) : e.testStep) + " · " + TimingMath.normalizeMaskingMethod(e.testStripMethod) + "\\nStrisce: " + TimingMath.seriesLabel(TimingMath.physicalTargets(strips, e.testStripMethod));\n','log card physical strip order')

# Hard release guards.
t=rd(timing); sv=rd(service); mt=rd(main); le=rd(logentry); ls=rd(logstore)
for needle in ['MASK_REVEAL = "SCOPRIRE"','MASK_COVER = "COPRIRE"','testStripPulses','physicalTargets','physicalTargetAt']:
    if needle not in t: raise SystemExit('v0.13.2 TimingMath guard missing: '+needle)
for needle in ['EXTRA_TEST_MASKING_METHOD','lastTestStripMethod','scheduleSafelightRestoreRetry','ON non ancora confermato']:
    if needle not in sv: raise SystemExit('v0.13.2 service guard missing: '+needle)
for needle in ['METODO PROVINO ·','physicalStrips','putString("printSequence", "")','postDelayed(this::maybeShowTestResultChooser, 450L)']:
    if needle not in mt: raise SystemExit('v0.13.2 MainActivity guard missing: '+needle)
if 'testStripMethod = TimingMath.MASK_REVEAL' not in le or 'normalizeMaskingMethod(e.testStripMethod)' not in ls: raise SystemExit('v0.13.2 LOG masking guards missing')
if 'assistant' in rd(manifest).lower() or (java/'assistant').exists() or (java/'home').exists(): raise SystemExit('v0.13.2 Assistant residue')
if 'testFromPrint' in mt or 'NUOVO PROVINO DA QUESTA STAMPA' in mt: raise SystemExit('v0.13.2 regressione STAMPA->PROVINO')
print('v0.13.2 TRANSFORM OK — masking selectable, chooser restored, F-STOP physical mapping fixed, safelight watchdog, stale split cleared',flush=True)
