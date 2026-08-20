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
    if n<count: raise SystemExit(f'v0.13.4 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count)); print('v0.13.4 OK',label,flush=True)

for p,needle in [
    (manifest,'android:versionName="0.13.3"'),
    (manifest,'android:versionCode="64"'),
    (main,'private static final String APP_VERSION = "0.13.3";')]:
    if needle not in rd(p): raise SystemExit('v0.13.4 BASE v0.13.3 non riconosciuta: '+needle)

s=rd(build)
if 'VERSION_NAME = "0.13.3"' not in s or 'VERSION_CODE = "64"' not in s:
    raise SystemExit('v0.13.4 builder base non riconosciuta')
s=s.replace('VERSION_NAME = "0.13.3"','VERSION_NAME = "0.13.4"').replace('VERSION_CODE = "64"','VERSION_CODE = "65"')
s=s.replace('[Darkroom v0.13.3]','[Darkroom v0.13.4]').replace('versionCode 64','versionCode 65').replace(r'versionCode\s+64\b',r'versionCode\s+65\b').replace('0.13.3','0.13.4')
wr(build,s)
rep(gradle,"versionCode 64\n        versionName '0.13.3'","versionCode 65\n        versionName '0.13.4'",'Gradle version')
rep(manifest,'android:versionCode="64"\n    android:versionName="0.13.3"','android:versionCode="65"\n    android:versionName="0.13.4"','manifest version')
rep(main,'private static final String APP_VERSION = "0.13.3";','private static final String APP_VERSION = "0.13.4";','Timer footer version')

# Manual button must not share the stale testChooserOpen guard used by automatic popup attempts.
rep(main,
'''        testPendingChoiceButton.setOnClickListener(v -> maybeShowTestResultChooser());\n''',
'''        testPendingChoiceButton.setOnClickListener(v -> maybeShowTestResultChooser(true));\n''','manual chooser uses forced path')

rep(main,
'''    private void maybeShowTestResultChooser() {\n        if (armed || mode != MODE_TEST || isFinishing() || testChooserOpen) return;\n        if (!hasWindowFocus()) {\n            new Handler(Looper.getMainLooper()).postDelayed(this::maybeShowTestResultChooser, 450L);\n            return;\n        }\n''',
'''    private void maybeShowTestResultChooser() {\n        maybeShowTestResultChooser(false);\n    }\n\n    private void maybeShowTestResultChooser(boolean forceManual) {\n        if (armed || mode != MODE_TEST || isFinishing()) return;\n        if (forceManual) {\n            // Manual recovery entry point: a stale guard must never make the visible button inert.\n            testChooserOpen = false;\n        } else if (testChooserOpen) {\n            return;\n        }\n        if (!hasWindowFocus()) {\n            new Handler(Looper.getMainLooper()).postDelayed(() -> maybeShowTestResultChooser(forceManual), 450L);\n            return;\n        }\n''','separate manual/automatic chooser guards')

mt=rd(main)
for needle in [
    'testPendingChoiceButton.setOnClickListener(v -> maybeShowTestResultChooser(true));',
    'private void maybeShowTestResultChooser(boolean forceManual)',
    'testChooserOpen = false;',
    'postDelayed(() -> maybeShowTestResultChooser(forceManual), 450L)']:
    if needle not in mt: raise SystemExit('v0.13.4 chooser guard missing: '+needle)
if 'SCEGLI STRISCIA DEL PROVINO' not in mt or 'hasPendingTestStripChoice()' not in mt:
    raise SystemExit('v0.13.4 pending chooser regression')
if 'assistant' in rd(manifest).lower() or (java/'assistant').exists() or (java/'home').exists():
    raise SystemExit('v0.13.4 Assistant residue')
print('v0.13.4 TRANSFORM OK — manual pending-strip button bypasses stale dialog guard; timing untouched',flush=True)
