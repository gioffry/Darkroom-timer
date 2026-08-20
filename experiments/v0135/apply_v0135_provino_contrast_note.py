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
    if n < count: raise SystemExit(f'v0.13.5 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count)); print('v0.13.5 OK',label,flush=True)

for p,needle in [
    (manifest,'android:versionName="0.13.4"'),
    (manifest,'android:versionCode="65"'),
    (main,'private static final String APP_VERSION = "0.13.4";')]:
    if needle not in rd(p): raise SystemExit('v0.13.5 BASE v0.13.4 non riconosciuta: '+needle)

s=rd(build)
if 'VERSION_NAME = "0.13.4"' not in s or 'VERSION_CODE = "65"' not in s:
    raise SystemExit('v0.13.5 builder base non riconosciuta')
s=s.replace('VERSION_NAME = "0.13.4"','VERSION_NAME = "0.13.5"').replace('VERSION_CODE = "65"','VERSION_CODE = "66"')
s=s.replace('[Darkroom v0.13.4]','[Darkroom v0.13.5]').replace('versionCode 65','versionCode 66').replace(r'versionCode\s+65\b',r'versionCode\s+66\b').replace('0.13.4','0.13.5')
wr(build,s)
rep(gradle,"versionCode 65\n        versionName '0.13.4'","versionCode 66\n        versionName '0.13.5'",'Gradle version')
rep(manifest,'android:versionCode="65"\n    android:versionName="0.13.4"','android:versionCode="66"\n    android:versionName="0.13.5"','manifest version')
rep(main,'private static final String APP_VERSION = "0.13.4";','private static final String APP_VERSION = "0.13.5";','Timer footer version')

anchor='''        testFStopBadge = addFStopBadge(exposure, false);\n'''
insert='''        testFStopBadge = addFStopBadge(exposure, false);\n        TextView contrastGuide = text("Leggi il provino dal CHIARO allo SCURO: se trovi prima i BIANCHI giusti → AUMENTA il contrasto; se trovi prima i NERI giusti → DIMINUISCI il contrasto. Se bianchi e neri sono giusti nello stesso gradino → CONTRASTO GIUSTO.", 12, darkroomMode ? RED : TEXT_PRIMARY, false);\n        contrastGuide.setPadding(dp(12), dp(10), dp(12), dp(10));\n        contrastGuide.setBackground(roundRect(darkroomMode ? Color.rgb(28,0,0) : Color.rgb(35,40,44), 9, 1, darkroomMode ? RED : BORDER));\n        exposure.addView(contrastGuide, margin(lp(-1,-2), 0, 8, 0, 0));\n'''
rep(main,anchor,insert,'provino contrast reading note')

mt=rd(main)
for needle in [
    'Leggi il provino dal CHIARO allo SCURO:',
    'BIANCHI giusti → AUMENTA il contrasto',
    'NERI giusti → DIMINUISCI il contrasto',
    'CONTRASTO GIUSTO']:
    if needle not in mt: raise SystemExit('v0.13.5 note guard missing: '+needle)
if 'assistant' in rd(manifest).lower() or (java/'assistant').exists() or (java/'home').exists():
    raise SystemExit('v0.13.5 Assistant residue')
print('v0.13.5 TRANSFORM OK — nota lettura contrasto integrata nel pannello PROVINO; timing untouched',flush=True)
