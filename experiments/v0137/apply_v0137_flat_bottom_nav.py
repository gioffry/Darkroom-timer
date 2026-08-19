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
nav = java / 'PrimaryNavButton.java'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s,encoding='utf-8')
def rep(p,old,new,label,count=1):
    s=rd(p); n=s.count(old)
    if n < count: raise SystemExit(f'v0.13.7 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count)); print('v0.13.7 OK',label,flush=True)

for p,needle in [
    (manifest,'android:versionName="0.13.6"'),
    (manifest,'android:versionCode="67"'),
    (main,'private static final String APP_VERSION = "0.13.6";')]:
    if needle not in rd(p): raise SystemExit('v0.13.7 BASE v0.13.6 non riconosciuta: '+needle)

s=rd(build)
if 'VERSION_NAME = "0.13.6"' not in s or 'VERSION_CODE = "67"' not in s:
    raise SystemExit('v0.13.7 builder base non riconosciuta')
s=s.replace('VERSION_NAME = "0.13.6"','VERSION_NAME = "0.13.7"').replace('VERSION_CODE = "67"','VERSION_CODE = "68"')
s=s.replace('[Darkroom v0.13.6]','[Darkroom v0.13.7]').replace('versionCode 67','versionCode 68').replace(r'versionCode\s+67\b',r'versionCode\s+68\b').replace('0.13.6','0.13.7')
wr(build,s)
rep(gradle,"versionCode 67\n        versionName '0.13.6'","versionCode 68\n        versionName '0.13.7'",'Gradle version')
rep(manifest,'android:versionCode="67"\n    android:versionName="0.13.6"','android:versionCode="68"\n    android:versionName="0.13.7"','manifest version')
rep(main,'private static final String APP_VERSION = "0.13.6";','private static final String APP_VERSION = "0.13.7";','Timer footer version')

# Bottom bar: remove the three card-like button surfaces and make the whole bar flat.
rep(main,
'''        modeRow.setPadding(dp(10), dp(6), dp(10), dp(8));\n        modeRow.setBackground(roundRect(darkroomMode ? Color.rgb(18,0,0) : Color.rgb(16,18,20), 0, 1, darkroomMode ? RED : BORDER));\n''',
'''        modeRow.setPadding(dp(8), dp(2), dp(8), dp(3));\n        modeRow.setBackgroundColor(Color.BLACK);\n''','flat bottom bar surface')

rep(main,
'''        modeRow.addView(testModeButton, margin(lp(0, dp(74), 1f), 0, 0, dp(4), 0));\n        modeRow.addView(printModeButton, margin(lp(0, dp(74), 1f), dp(4), 0, dp(4), 0));\n        modeRow.addView(logModeButton, margin(lp(0, dp(74), 1f), dp(4), 0, 0, 0));\n''',
'''        modeRow.addView(testModeButton, lp(0, dp(72), 1f));\n        modeRow.addView(printModeButton, lp(0, dp(72), 1f));\n        modeRow.addView(logModeButton, lp(0, dp(72), 1f));\n''','remove card gaps')

rep(main,
'''        root.addView(footer, margin(lp(-1, dp(46)), 0, 10, 0, 6));\n\n        page.addView(modeRow, lp(-1, dp(88)));\n''',
'''        root.addView(footer, margin(lp(-1, dp(46)), 0, 10, 0, 6));\n\n        View bottomNavDivider = new View(this);\n        bottomNavDivider.setBackgroundColor(darkroomMode ? BORDER : Color.rgb(42, 47, 50));\n        page.addView(bottomNavDivider, lp(-1, dp(1)));\n        page.addView(modeRow, lp(-1, dp(78)));\n''','thin divider above bottom nav')

rep(main,
'''    private void styleNavButton(Button button, boolean selected, int normalAccent) {\n        int foreground;\n        int background;\n        if (darkroomMode) {\n            foreground = selected ? Color.BLACK : RED;\n            background = selected ? RED : BUTTON;\n        } else {\n            foreground = selected ? Color.WHITE : MUTED;\n            background = selected ? normalAccent : BUTTON;\n        }\n        button.setTextColor(foreground);\n        button.setBackground(roundRect(background, 12, selected ? 0 : 1, BORDER));\n        if (button instanceof PrimaryNavButton) {\n            ((PrimaryNavButton) button).setIconColor(foreground);\n        }\n    }\n''',
'''    private void styleNavButton(Button button, boolean selected, int normalAccent) {\n        int foreground;\n        if (darkroomMode) {\n            foreground = selected ? RED : Color.rgb(125, 0, 0);\n        } else {\n            foreground = selected ? (normalAccent == LOG_ACCENT ? TEXT_PRIMARY : normalAccent) : MUTED;\n        }\n        button.setTextColor(foreground);\n        button.setTypeface(Typeface.DEFAULT, selected ? Typeface.BOLD : Typeface.NORMAL);\n        button.setBackgroundColor(Color.TRANSPARENT);\n        if (button instanceof PrimaryNavButton) {\n            PrimaryNavButton navButton = (PrimaryNavButton) button;\n            navButton.setIconColor(foreground);\n            navButton.setActiveIndicator(selected, foreground);\n        }\n    }\n''','flat nav selected state')

# PrimaryNavButton draws the small selected line above the icon, like the reference mockup.
rep(nav,
'''    private int iconColor = Color.WHITE;\n    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);\n''',
'''    private int iconColor = Color.WHITE;\n    private boolean activeIndicator = false;\n    private int activeColor = Color.WHITE;\n    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);\n''','nav active indicator state')

rep(nav,
'''        setTextSize(14);\n        setTypeface(Typeface.DEFAULT, Typeface.BOLD);\n        setAllCaps(false);\n        setGravity(Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);\n        setPadding(d(6), d(8), d(6), d(10));\n''',
'''        setTextSize(12);\n        setTypeface(Typeface.DEFAULT, Typeface.NORMAL);\n        setAllCaps(false);\n        setGravity(Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);\n        setPadding(d(4), d(6), d(4), d(7));\n''','lighter nav typography')

rep(nav,
'''    public void setIconColor(int color) {\n        iconColor = color;\n        invalidate();\n    }\n''',
'''    public void setIconColor(int color) {\n        iconColor = color;\n        invalidate();\n    }\n\n    public void setActiveIndicator(boolean active, int color) {\n        activeIndicator = active;\n        activeColor = color;\n        invalidate();\n    }\n''','nav indicator setter')

rep(nav,
'''    @Override protected void onDraw(Canvas canvas) {\n        super.onDraw(canvas);\n        float cx = getWidth() / 2f;\n''',
'''    @Override protected void onDraw(Canvas canvas) {\n        super.onDraw(canvas);\n        float cx = getWidth() / 2f;\n        if (activeIndicator) {\n            paint.setColor(activeColor);\n            paint.setStrokeWidth(d(3));\n            paint.setStrokeCap(Paint.Cap.ROUND);\n            paint.setStyle(Paint.Style.STROKE);\n            canvas.drawLine(cx - d(18), d(2), cx + d(18), d(2), paint);\n        }\n''','draw active line')

mt=rd(main); nt=rd(nav)
for needle in [
    'page.addView(bottomNavDivider, lp(-1, dp(1)));',
    'page.addView(modeRow, lp(-1, dp(78)));',
    'button.setBackgroundColor(Color.TRANSPARENT);',
    'navButton.setActiveIndicator(selected, foreground);',
    'mode = MODE_TEST;',
    'Leggi il provino dal CHIARO allo SCURO:',
    'maybeShowTestResultChooser(true)']:
    if needle not in mt: raise SystemExit('v0.13.7 MainActivity guard missing: '+needle)
for needle in ['activeIndicator', 'setActiveIndicator(boolean active, int color)', 'canvas.drawLine(cx - d(18), d(2), cx + d(18), d(2), paint);']:
    if needle not in nt: raise SystemExit('v0.13.7 PrimaryNavButton guard missing: '+needle)
if 'assistant' in rd(manifest).lower() or (java/'assistant').exists() or (java/'home').exists():
    raise SystemExit('v0.13.7 Assistant residue')
print('v0.13.7 TRANSFORM OK — flat mockup-style bottom nav; PROVINO default preserved; timing untouched',flush=True)
