#!/usr/bin/env python3
from pathlib import Path
import sys

work = Path(sys.argv[1])
project = work / 'project'
app = project / 'app'
main_dir = app / 'src/main'
java = main_dir / 'java/it/darkroom/timer'
manifest = main_dir / 'AndroidManifest.xml'
gradle = app / 'build.gradle'
build = work / 'build_darkroom.py'
main = java / 'MainActivity.java'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s,encoding='utf-8')
def rep(p,old,new,label,count=1):
    s=rd(p); n=s.count(old)
    if n<count: raise SystemExit(f'v0.13.3 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count)); print('v0.13.3 OK',label,flush=True)

# Exact base: v0.13.2, no timing changes in this release.
for p,needle in [
    (manifest,'android:versionName="0.13.2"'),
    (manifest,'android:versionCode="63"'),
    (main,'private static final String APP_VERSION = "0.13.2";')]:
    if needle not in rd(p): raise SystemExit('v0.13.3 BASE v0.13.2 non riconosciuta: '+needle)

s=rd(build)
if 'VERSION_NAME = "0.13.2"' not in s or 'VERSION_CODE = "63"' not in s:
    raise SystemExit('v0.13.3 builder base non riconosciuta')
s=s.replace('VERSION_NAME = "0.13.2"','VERSION_NAME = "0.13.3"').replace('VERSION_CODE = "63"','VERSION_CODE = "64"')
s=s.replace('[Darkroom v0.13.2]','[Darkroom v0.13.3]').replace('versionCode 63','versionCode 64').replace(r'versionCode\s+63\b',r'versionCode\s+64\b').replace('0.13.2','0.13.3')
wr(build,s)
rep(gradle,"versionCode 63\n        versionName '0.13.2'","versionCode 64\n        versionName '0.13.3'",'Gradle version')
rep(manifest,'android:versionCode="63"\n    android:versionName="0.13.2"','android:versionCode="64"\n    android:versionName="0.13.3"','manifest version')
rep(main,'private static final String APP_VERSION = "0.13.2";','private static final String APP_VERSION = "0.13.3";','Timer footer version')

# Persistent UI entry point for a provino whose strip choice is still pending.
rep(main,
'''    private Button testBaseFilterButton;\n    private Button testStripMethodButton;\n    private TextView printSequenceSummary;\n''',
'''    private Button testBaseFilterButton;\n    private Button testStripMethodButton;\n    private Button testPendingChoiceButton;\n    private TextView printSequenceSummary;\n''','pending chooser button field')

rep(main,
'''        testStripMethodButton = compactButton(testStripMethodButtonLabel());\n        testStripMethodButton.setOnClickListener(v -> showTestStripMethodDialog());\n        exposure.addView(testStripMethodButton, margin(lp(-1, dp(50)), 0, 8, 0, 0));\n        testFStopBadge = addFStopBadge(exposure, false);\n''',
'''        testStripMethodButton = compactButton(testStripMethodButtonLabel());\n        testStripMethodButton.setOnClickListener(v -> showTestStripMethodDialog());\n        exposure.addView(testStripMethodButton, margin(lp(-1, dp(50)), 0, 8, 0, 0));\n        testPendingChoiceButton = compactButton("SCEGLI STRISCIA DEL PROVINO");\n        testPendingChoiceButton.setTextColor(Color.WHITE);\n        testPendingChoiceButton.setBackground(roundRect(BLUE, 9, 0, 0));\n        testPendingChoiceButton.setOnClickListener(v -> maybeShowTestResultChooser());\n        exposure.addView(testPendingChoiceButton, margin(lp(-1, dp(52)), 0, 8, 0, 0));\n        refreshPendingTestStripChoiceUi();\n        testFStopBadge = addFStopBadge(exposure, false);\n''','persistent chooser button in provino panel')

helpers='''    private boolean hasPendingTestStripChoice() {\n        SharedPreferences session = getSharedPreferences("log_session", MODE_PRIVATE);\n        long testAt = session.getLong("lastTestAt", 0L);\n        if (testAt <= 0L) return false;\n        long chosenAt = getSharedPreferences("ui", MODE_PRIVATE).getLong("lastTestChooserShownAt", 0L);\n        return chosenAt < testAt;\n    }\n\n    private void refreshPendingTestStripChoiceUi() {\n        if (testPendingChoiceButton == null) return;\n        boolean pending = hasPendingTestStripChoice();\n        testPendingChoiceButton.setVisibility(pending ? View.VISIBLE : View.GONE);\n        testPendingChoiceButton.setEnabled(pending && !armed);\n        testPendingChoiceButton.setAlpha(testPendingChoiceButton.isEnabled() ? 1f : (darkroomMode ? 0.62f : 0.45f));\n    }\n\n'''
rep(main,
'''    private void maybeShowTestResultChooser() {\n        if (armed || mode != MODE_TEST || isFinishing() || testChooserOpen) return;\n''',
helpers+'''    private void maybeShowTestResultChooser() {\n        if (armed || mode != MODE_TEST || isFinishing() || testChooserOpen) return;\n''','pending chooser helpers')

# Rebuild the pending-button state when the activity becomes visible again.
rep(main,
'''        restoreRuntimeState();\n        new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 320L);\n''',
'''        restoreRuntimeState();\n        refreshPendingTestStripChoiceUi();\n        new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 320L);\n''','refresh pending chooser on resume')

# A real selection is the only action that clears the pending state.
rep(main,
'''            ui.edit().putLong("lastTestChooserShownAt", testAt).apply();\n            exposureRecipe = new ExposureRecipe();\n''',
'''            ui.edit().putLong("lastTestChooserShownAt", testAt).apply();\n            refreshPendingTestStripChoiceUi();\n            exposureRecipe = new ExposureRecipe();\n''','clear pending only after strip choice')

# NON ORA just dismisses the dialog: immediately expose the persistent button.
rep(main,
'''        dialog.setOnDismissListener(d -> {\n            if (title != null && title.startsWith("PROVINO COMPLETATO")) testChooserOpen = false;\n        });\n''',
'''        dialog.setOnDismissListener(d -> {\n            if (title != null && title.startsWith("PROVINO COMPLETATO")) {\n                testChooserOpen = false;\n                refreshPendingTestStripChoiceUi();\n            }\n        });\n''','NON ORA keeps pending choice visible')

# Hard guards. This release must not touch timing/service math.
mt=rd(main)
for needle in [
    'SCEGLI STRISCIA DEL PROVINO',
    'hasPendingTestStripChoice()',
    'refreshPendingTestStripChoiceUi()',
    'chosenAt < testAt',
    'refreshPendingTestStripChoiceUi();\n            exposureRecipe = new ExposureRecipe();']:
    if needle not in mt: raise SystemExit('v0.13.3 chooser guard missing: '+needle)
if 'lastTestChooserShownAt' not in mt or 'lastTestAt' not in mt:
    raise SystemExit('v0.13.3 pending-state timestamps missing')
if 'assistant' in rd(manifest).lower() or (java/'assistant').exists() or (java/'home').exists():
    raise SystemExit('v0.13.3 Assistant residue')
print('v0.13.3 TRANSFORM OK — preferred-strip choice remains pending after NON ORA; no timing changes',flush=True)
