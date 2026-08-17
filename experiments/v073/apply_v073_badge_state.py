#!/usr/bin/env python3
from pathlib import Path
import sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
build = work / 'build_darkroom.py'


def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label):
    p=Path(p); s=rd(p)
    if old not in s: raise SystemExit(f'v0.7.3: pattern mancante: {label}')
    wr(p, s.replace(old,new,1)); print('v0.7.3 OK', label, flush=True)

# Versione
rep(build, 'VERSION_NAME = "0.7.2"\nVERSION_CODE = "35"', 'VERSION_NAME = "0.7.3"\nVERSION_CODE = "36"', 'version build')
rep(build, '[Darkroom v0.7.2]', '[Darkroom v0.7.3]', 'tag build')
rep(build, 'versionCode\\s+35\\b', 'versionCode\\s+36\\b', 'preflight code')
rep(build, '0\\.7\\.2', '0\\.7\\.3', 'preflight name')
rep(build, 'versionCode 35 / versionName 0.7.2', 'versionCode 36 / versionName 0.7.3', 'preflight msg')
rep(build, 'Preflight v0.7.2 OK', 'Preflight v0.7.3 OK', 'preflight log')
rep(project/'app/build.gradle', "versionCode 35\n        versionName '0.7.2'", "versionCode 36\n        versionName '0.7.3'", 'gradle')
rep(project/'app/src/main/AndroidManifest.xml', 'android:versionCode="35"\n    android:versionName="0.7.2"', 'android:versionCode="36"\n    android:versionName="0.7.3"', 'manifest')
rep(main, 'private static final String APP_VERSION = "0.7.2";', 'private static final String APP_VERSION = "0.7.3";', 'app version')

# I badge devono esistere sempre come View e cambiare visibilità assieme al metodo.
rep(main,
'''    private TextView testPromptText;\n    private TextView testStepText;\n    private Button actionButton;''',
'''    private TextView testPromptText;\n    private TextView testStepText;\n    private TextView printFStopBadge;\n    private TextView testFStopBadge;\n    private Button actionButton;''',
'campi badge')

old_helper='''    private void addFStopBadge(LinearLayout parent, boolean compact) {\n        if (parent == null || !TimingMath.isFStop(timingMethod)) return;\n        TextView badge = fStopBadge(compact);\n        parent.addView(badge, margin(lp(compact ? -2 : -1, dp(compact ? 26 : 32)), compact ? 0 : dp(36), dp(6), compact ? 0 : dp(36), dp(6)));\n    }'''
new_helper='''    private TextView addFStopBadge(LinearLayout parent, boolean compact) {\n        if (parent == null) return null;\n        TextView badge = fStopBadge(compact);\n        badge.setVisibility(TimingMath.isFStop(timingMethod) ? View.VISIBLE : View.GONE);\n        parent.addView(badge, margin(lp(compact ? -2 : -1, dp(compact ? 26 : 32)), compact ? 0 : dp(36), dp(6), compact ? 0 : dp(36), dp(6)));\n        return badge;\n    }'''
rep(main, old_helper, new_helper, 'helper badge dinamico')
rep(main, '        addFStopBadge(box, false);', '        printFStopBadge = addFStopBadge(box, false);', 'badge stampa reference')
rep(main, '        addFStopBadge(exposure, false);', '        testFStopBadge = addFStopBadge(exposure, false);', 'badge provino reference')

old_update='''    private void updateTimingUi() {\n        if (printStepText != null) printStepText.setText(printStepDescription());\n        if (testPromptText != null) testPromptText.setText(testPromptDescription());\n        if (testStepText != null) testStepText.setText(testStepDescription());\n        updateCumulativeTimes();\n        applyModeUi();\n    }'''
new_update='''    private void updateTimingUi() {\n        boolean fstop = TimingMath.isFStop(timingMethod);\n        if (printStepText != null) printStepText.setText(printStepDescription());\n        if (testPromptText != null) testPromptText.setText(testPromptDescription());\n        if (testStepText != null) testStepText.setText(testStepDescription());\n        if (printFStopBadge != null) printFStopBadge.setVisibility(fstop ? View.VISIBLE : View.GONE);\n        if (testFStopBadge != null) testFStopBadge.setVisibility(fstop ? View.VISIBLE : View.GONE);\n        updateCumulativeTimes();\n        applyModeUi();\n    }'''
rep(main, old_update, new_update, 'update badge su cambio metodo')

# Verifica che badge, testi, pulsante ARMA e matematica dipendano dallo stesso timingMethod.
s=rd(main)
for needle in [
    'printFStopBadge.setVisibility(fstop ? View.VISIBLE : View.GONE)',
    'testFStopBadge.setVisibility(fstop ? View.VISIBLE : View.GONE)',
    'TimingMath.cumulativeSeries(timingMethod, testWidthMs, testCount)',
    'TimingMath.isFStop(timingMethod) ? "Tempo prima striscia"',
    'TimingMath.isFStop(timingMethod)'
]:
    if needle not in s: raise SystemExit('v0.7.3 verifica fallita: '+needle)

# Il PNG esatto viene reinserito nell'APK finale dopo il build e poi rifirmato
# con la stessa chiave stabile. Qui il materializer non deve alterare la risorsa.
wr(work/'v064_icon.py', '''from pathlib import Path\n\ndef materialize_icon(project):\n    print("[Darkroom v0.7.3] Icona del build lasciata invariata per sostituzione finale verificata", flush=True)\n''')
print('v0.7.3 OK icon materializer neutro', flush=True)
print('v0.7.3 TUTTE LE VERIFICHE OK', flush=True)
