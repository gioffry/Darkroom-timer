#!/usr/bin/env python3
from pathlib import Path
import sys

work = Path(sys.argv[1])
project = work / 'project'
java = project / 'app/src/main/java/it/darkroom/timer'
main = java / 'MainActivity.java'
jpg = java / 'JpegCardRenderer.java'
build = work / 'build_darkroom.py'

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).write_text(s, encoding='utf-8')
def rep(p, old, new, label):
    p = Path(p); s = rd(p)
    if old not in s:
        raise SystemExit(f'v0.7.4: pattern mancante: {label}')
    wr(p, s.replace(old, new, 1))
    print('v0.7.4 OK', label, flush=True)

# Versione
rep(build, 'VERSION_NAME = "0.7.3"\nVERSION_CODE = "36"', 'VERSION_NAME = "0.7.4"\nVERSION_CODE = "37"', 'version build')
rep(build, '[Darkroom v0.7.3]', '[Darkroom v0.7.4]', 'tag build')
rep(build, 'versionCode\\s+36\\b', 'versionCode\\s+37\\b', 'preflight code')
rep(build, '0\\.7\\.3', '0\\.7\\.4', 'preflight name')
rep(build, 'versionCode 36 / versionName 0.7.3', 'versionCode 37 / versionName 0.7.4', 'preflight msg')
rep(build, 'Preflight v0.7.3 OK', 'Preflight v0.7.4 OK', 'preflight log')
rep(project/'app/build.gradle', "versionCode 36\n        versionName '0.7.3'", "versionCode 37\n        versionName '0.7.4'", 'gradle')
rep(project/'app/src/main/AndroidManifest.xml', 'android:versionCode="36"\n    android:versionName="0.7.3"', 'android:versionCode="37"\n    android:versionName="0.7.4"', 'manifest')
rep(main, 'private static final String APP_VERSION = "0.7.3";', 'private static final String APP_VERSION = "0.7.4";', 'app version')

# F-STOP: colore semantico proprio. Normale = ocra/oro su fondo scuro con bordo.
# Darkroom Safety = solo rosso/nero.
old_badge = '''    private TextView fStopBadge(boolean compact) {\n        TextView badge = text(compact ? "F-STOP  ·  ¼" : "F-STOP  ·  ¼ stop", compact ? 10 : 12, Color.BLACK, true);\n        badge.setGravity(Gravity.CENTER);\n        badge.setPadding(dp(compact ? 8 : 12), dp(compact ? 3 : 5), dp(compact ? 8 : 12), dp(compact ? 3 : 5));\n        badge.setBackground(roundRect(darkroomMode ? RED : GREEN, compact ? 10 : 14, 0, 0));\n        badge.setContentDescription("Modalità F-STOP, passo un quarto di stop");\n        return badge;\n    }'''
new_badge = '''    private TextView fStopBadge(boolean compact) {\n        int accent = darkroomMode ? RED : Color.rgb(201, 157, 70);\n        int fill = darkroomMode ? Color.BLACK : Color.rgb(31, 29, 24);\n        TextView badge = text(compact ? "F-STOP  ·  ¼" : "F-STOP  ·  ¼ stop", compact ? 10 : 12, accent, true);\n        badge.setGravity(Gravity.CENTER);\n        badge.setPadding(dp(compact ? 8 : 12), dp(compact ? 3 : 4), dp(compact ? 8 : 12), dp(compact ? 3 : 4));\n        badge.setBackground(roundRect(fill, compact ? 10 : 13, 1, accent));\n        badge.setContentDescription("Modalità F-STOP, passo un quarto di stop");\n        return badge;\n    }'''
rep(main, old_badge, new_badge, 'badge ocra/oro')

# JPG: stesso codice colore F-STOP, distinto dal verde STAMPA.
rep(jpg, 'badgeFill.setColor(Color.rgb(80, 207, 70));', 'badgeFill.setColor(Color.rgb(201, 157, 70));', 'JPG badge oro')

# Verifiche
checks = {
    main: ['Color.rgb(201, 157, 70)', 'Color.rgb(31, 29, 24)', 'roundRect(fill, compact ? 10 : 13, 1, accent)', 'printFStopBadge.setVisibility', 'testFStopBadge.setVisibility'],
    jpg: ['badgeFill.setColor(Color.rgb(201, 157, 70));'],
    build: ['VERSION_NAME = "0.7.4"', 'VERSION_CODE = "37"'],
}
for path, needles in checks.items():
    text = rd(path)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'v0.7.4 verifica fallita: {needle} in {path}')
print('v0.7.4 TUTTE LE VERIFICHE OK', flush=True)
