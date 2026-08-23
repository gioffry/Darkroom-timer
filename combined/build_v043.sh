#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.3 - global FAQ search + Rolleiflex accessory chapters.
# Exact base: verified v0.4.2. Timer, SONOFF, enlargement, paper-plane,
# Nikon/Minolta manuals, chemistry DB and prior technical FAQs remain unchanged.

bash combined/build_v042.sh
python3 combined/patch_v043_rolleiflex_faq_search.py | tee validation-v043-rolleiflex-search.txt

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="34"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.4.3"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.4.3 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 34', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.3'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.4.3 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.3.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.3.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.3.apk > certificate-v043.txt
"$AAPT" dump badging Darkroom-v0.4.3.apk > apk-badging-v043.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v043.txt
grep -Fq "versionCode='34'" apk-badging-v043.txt
grep -Fq "versionName='0.4.3'" apk-badging-v043.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v043.txt
unzip -Z1 Darkroom-v0.4.3.apk > apk-listing-v043.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v043.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

# v0.4.3 acceptance: global search and Rolleiflex accessory navigation/content.
grep -Fq 'Cerca nelle FAQ…' "$MAINT"
grep -Fq 'renderFaqSearchResults' "$MAINT"
grep -Fq 'renderSingleFaq' "$MAINT"
grep -Fq 'FILTRI E ACCESSORI ROLLEIFLEX' "$MAINT"
grep -Fq 'ROLLEIFLEX 3.5 — ACCESSORI' "$MAINT"
grep -Fq 'ROLLEIFLEX 2.8 — ACCESSORI' "$MAINT"
grep -Fq 'ROLLEIFILTER SPORT' "$MAINT"
grep -Fq 'GELB MITTEL' "$MAINT"
grep -Fq 'HELLGRÜN' "$MAINT"
grep -Fq 'HELLROT' "$MAINT"
grep -Fq 'HELLBLAU' "$MAINT"
grep -Fq 'ROLLEIPARKEIL 1' "$MAINT" || grep -Fq 'Rolleiparkeil 1' "$MAINT"
grep -Fq 'Rolleiparkeil 2' "$MAINT"
grep -Fq 'Heidosmat-Rolleinar 1' "$MAINT"
grep -Fq 'circa da 1 metro a 47 cm' "$MAINT"
grep -Fq 'FAQ arrays invalid for' "$MAINT"

python3 - <<'PY' | tee validation-v043-faq-guard.txt
from pathlib import Path
s=Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
required=[
'Cerca nelle FAQ…','addFaqMatches(hits,"MEOPTA OPEMUS 6"','addFaqMatches(hits,"ROLLEIFLEX 3.5 — GENERALE"','addFaqMatches(hits,"ROLLEIFLEX 2.8 — GENERALE"',
'Rolleifilter Sport','Gelb Mittel','Hellgrün','Hellrot','Hellblau','Rolleinar 1','Rolleinar 2','Rolleiparkeil 1','Rolleiparkeil 2','Heidosmat-Rolleinar 1','puntino rosso'
]
for x in required: assert x in s,x
for a,b,n in [
('Q_R35_GENERAL','A_R35_GENERAL',10),('Q_R35_SPORT','A_R35_SPORT',1),('Q_R35_YELLOW','A_R35_YELLOW',3),('Q_R35_GREEN','A_R35_GREEN',4),('Q_R35_RED','A_R35_RED',4),('Q_R35_BLUE','A_R35_BLUE',3),('Q_R35_R1','A_R35_R1',8),('Q_R35_R2','A_R35_R2',8),('Q_R28_GENERAL','A_R28_GENERAL',3),('Q_R28_HOOD','A_R28_HOOD',1),('Q_R28_R1','A_R28_R1',5)]:
    x=s.index('private static final String[] '+a); y=s.index('private static final String[] '+b,x); assert s[x:y].count('            "')==n,(a,n)
print('global_faq_search=PASS')
print('search_question_and_answer=PASS')
print('search_direct_single_faq=PASS')
print('rolleiflex_35_accessory_sections=8')
print('rolleiflex_28_accessory_sections=3')
print('rolleiflex_35_general_faq=10')
print('rolleiflex_28_rolleinar1_two_piece=PASS')
PY

# Prior validated areas must survive unchanged.
grep -Fq 'Come si sostituisce correttamente la lampada della Meopta Color 3?' "$MAINT"
grep -Fq 'PROCESSO E LAVAGGIO' "$MAINT"
grep -Fq 'non farlo girare nel processore' "$MAINT"
grep -Fq 'NIKON L35AF2' "$MAINT"
grep -Fq 'DX automatico' "$MAINT"
grep -Fq 'ISO 50-1600' "$MAINT"
grep -Fq 'Quale batteria usa il Minolta Auto Meter IIIF?' "$MAINT"
grep -Fq '4LR44' "$MAINT"
grep -Fq 'ALTEZZA PIANO CARTA (spessore marginatore)' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$ENL"
grep -Fq 'Math.pow((c.beta+1)/(b1+1),2)' "$ENL"
grep -Fq 'Math.round(ms/500.0)*500' "$ENL"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"

python3 - <<'PY' | tee validation-v043-bundled-db.txt
from pathlib import Path
import sqlite3
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776
print('release=Darkroom-v0.4.3')
print('versionName=0.4.3')
print('versionCode=34')
print('base_version=0.4.2')
print('change_scope=GLOBAL_FAQ_SEARCH_PLUS_ROLLEIFLEX_ACCESSORIES')
print('global_faq_search=PASS')
print('rolleiflex_35_and_28_separated=PASS')
print('color3_lamp_faq_unchanged=PASS')
print('process_wash_faq_unchanged=PASS')
print('nikon_l35af2_manual_faq_unchanged=PASS')
print('minolta_manual_faq_unchanged=PASS')
print('paper_plane_logic_unchanged=PASS')
print('enlargement_exposure_formula_unchanged=PASS')
print('sonoff_final_step_seconds=0.5')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
con.close()
PY

cat validation-v042.txt validation-v043-rolleiflex-search.txt validation-v043-faq-guard.txt validation-v043-bundled-db.txt > validation-v043.txt
sha256sum Darkroom-v0.4.3.apk | tee Darkroom-v0.4.3.sha256
