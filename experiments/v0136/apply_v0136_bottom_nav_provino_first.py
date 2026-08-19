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
    if n < count: raise SystemExit(f'v0.13.6 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count)); print('v0.13.6 OK',label,flush=True)

for p,needle in [
    (manifest,'android:versionName="0.13.5"'),
    (manifest,'android:versionCode="66"'),
    (main,'private static final String APP_VERSION = "0.13.5";')]:
    if needle not in rd(p): raise SystemExit('v0.13.6 BASE v0.13.5 non riconosciuta: '+needle)

s=rd(build)
if 'VERSION_NAME = "0.13.5"' not in s or 'VERSION_CODE = "66"' not in s:
    raise SystemExit('v0.13.6 builder base non riconosciuta')
s=s.replace('VERSION_NAME = "0.13.5"','VERSION_NAME = "0.13.6"').replace('VERSION_CODE = "66"','VERSION_CODE = "67"')
s=s.replace('[Darkroom v0.13.5]','[Darkroom v0.13.6]').replace('versionCode 66','versionCode 67').replace(r'versionCode\s+66\b',r'versionCode\s+67\b').replace('0.13.5','0.13.6')
wr(build,s)
rep(gradle,"versionCode 66\n        versionName '0.13.5'","versionCode 67\n        versionName '0.13.6'",'Gradle version')
rep(manifest,'android:versionCode="66"\n    android:versionName="0.13.5"','android:versionCode="67"\n    android:versionName="0.13.6"','manifest version')
rep(main,'private static final String APP_VERSION = "0.13.5";','private static final String APP_VERSION = "0.13.6";','Timer footer version')

# Always enter the real working flow from PROVINO on Activity creation.
rep(main,
'''        mode = p.getInt("mode", MODE_PRINT);\n''',
'''        mode = MODE_TEST;\n        p.edit().putInt("mode", MODE_TEST).apply();\n''','default mode PROVINO')

# Convert the page to a scrollable content area plus a fixed bottom navigation.
rep(main,
'''    private void buildUi() {\n        ScrollView scroll = new ScrollView(this);\n        scroll.setFillViewport(true);\n        scroll.setBackgroundColor(Color.BLACK);\n        LinearLayout root = new LinearLayout(this);\n        root.setOrientation(LinearLayout.VERTICAL);\n        root.setPadding(dp(16), dp(14), dp(16), dp(28));\n        scroll.addView(root, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));\n''',
'''    private void buildUi() {\n        LinearLayout page = new LinearLayout(this);\n        page.setOrientation(LinearLayout.VERTICAL);\n        page.setBackgroundColor(Color.BLACK);\n\n        ScrollView scroll = new ScrollView(this);\n        scroll.setFillViewport(true);\n        scroll.setBackgroundColor(Color.BLACK);\n        LinearLayout root = new LinearLayout(this);\n        root.setOrientation(LinearLayout.VERTICAL);\n        root.setPadding(dp(16), dp(14), dp(16), dp(18));\n        scroll.addView(root, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));\n        page.addView(scroll, lp(-1, 0, 1f));\n''','fixed-bottom page container')

rep(main,
'''        LinearLayout modeRow = new LinearLayout(this);\n        modeRow.setOrientation(LinearLayout.HORIZONTAL);\n        printModeButton = navButton("STAMPA", PrimaryNavButton.ICON_TIMER);\n        testModeButton = navButton("PROVINO", PrimaryNavButton.ICON_TEST);\n        logModeButton = navButton("LOG", PrimaryNavButton.ICON_LOG);\n        printModeButton.setOnClickListener(v -> setMode(MODE_PRINT));\n        testModeButton.setOnClickListener(v -> setMode(MODE_TEST));\n        logModeButton.setOnClickListener(v -> setMode(MODE_LOG));\n        modeRow.addView(printModeButton, margin(lp(0, dp(88), 1f), 0, 0, dp(5), 0));\n        modeRow.addView(testModeButton, margin(lp(0, dp(88), 1f), dp(5), 0, dp(5), 0));\n        modeRow.addView(logModeButton, margin(lp(0, dp(88), 1f), dp(5), 0, 0, 0));\n        root.addView(modeRow, margin(lp(-1, -2), 0, 0, 0, 14));\n''',
'''        LinearLayout modeRow = new LinearLayout(this);\n        modeRow.setOrientation(LinearLayout.HORIZONTAL);\n        modeRow.setGravity(Gravity.CENTER_VERTICAL);\n        modeRow.setPadding(dp(10), dp(6), dp(10), dp(8));\n        modeRow.setBackground(roundRect(darkroomMode ? Color.rgb(18,0,0) : Color.rgb(16,18,20), 0, 1, darkroomMode ? RED : BORDER));\n        testModeButton = navButton("PROVINO", PrimaryNavButton.ICON_TEST);\n        printModeButton = navButton("STAMPA", PrimaryNavButton.ICON_TIMER);\n        logModeButton = navButton("LOG", PrimaryNavButton.ICON_LOG);\n        testModeButton.setOnClickListener(v -> setMode(MODE_TEST));\n        printModeButton.setOnClickListener(v -> setMode(MODE_PRINT));\n        logModeButton.setOnClickListener(v -> setMode(MODE_LOG));\n        modeRow.addView(testModeButton, margin(lp(0, dp(74), 1f), 0, 0, dp(4), 0));\n        modeRow.addView(printModeButton, margin(lp(0, dp(74), 1f), dp(4), 0, dp(4), 0));\n        modeRow.addView(logModeButton, margin(lp(0, dp(74), 1f), dp(4), 0, 0, 0));\n''','bottom nav order PROVINO STAMPA LOG')

rep(main,
'''        TextView footer = text("Darkroom Timer di F.G. - v" + APP_VERSION, 12, darkroomMode ? Color.rgb(92, 18, 18) : Color.rgb(105, 112, 118), false);\n        footer.setGravity(Gravity.CENTER);\n        root.addView(footer, margin(lp(-1, dp(46)), 0, 10, 0, 0));\n\n        setContentView(scroll);\n        setControlsEnabled(false);\n''',
'''        TextView footer = text("Darkroom Timer di F.G. - v" + APP_VERSION, 12, darkroomMode ? Color.rgb(92, 18, 18) : Color.rgb(105, 112, 118), false);\n        footer.setGravity(Gravity.CENTER);\n        root.addView(footer, margin(lp(-1, dp(46)), 0, 10, 0, 6));\n\n        page.addView(modeRow, lp(-1, dp(88)));\n        setContentView(page);\n        setControlsEnabled(false);\n''','attach fixed bottom navigation')

mt=rd(main)
for needle in [
    'mode = MODE_TEST;',
    'page.addView(scroll, lp(-1, 0, 1f));',
    'page.addView(modeRow, lp(-1, dp(88)));',
    'testModeButton = navButton("PROVINO", PrimaryNavButton.ICON_TEST);',
    'modeRow.addView(testModeButton',
    'modeRow.addView(printModeButton',
    'modeRow.addView(logModeButton',
    'Leggi il provino dal CHIARO allo SCURO:']:
    if needle not in mt: raise SystemExit('v0.13.6 UI guard missing: '+needle)

# The old top placement must be gone.
if 'root.addView(modeRow' in mt:
    raise SystemExit('v0.13.6 old top navigation still present')
if 'setContentView(scroll);' in mt:
    raise SystemExit('v0.13.6 old scroll-only content view still present')
if 'assistant' in rd(manifest).lower() or (java/'assistant').exists() or (java/'home').exists():
    raise SystemExit('v0.13.6 Assistant residue')
print('v0.13.6 TRANSFORM OK — PROVINO default, bottom navigation PROVINO/STAMPA/LOG, contrast note preserved; timing untouched',flush=True)
