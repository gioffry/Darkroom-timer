#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.4 - replace Nikon D100 manual/FAQ with Nikon F100 in Italian.
# Exact base: verified v0.4.3. All Timer, SONOFF, enlargement, chemistry,
# Rolleiflex, Color 3, Nikon L35AF2 and Minolta functions remain unchanged.

# v0.4.3 needs the inherited v0.4.2 FAQ validator normalization before rebuilding.
python3 combined/patch_v043_prebuild_v042_validator.py
bash combined/build_v043.sh
python3 combined/patch_v044_nikon_f100_manual_faq.py | tee validation-v044-nikon-f100.txt

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="35"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.4.4"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.4.4 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 35', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.4'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.4.4 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.4.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.4.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.4.apk > certificate-v044.txt
"$AAPT" dump badging Darkroom-v0.4.4.apk > apk-badging-v044.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v044.txt
grep -Fq "versionCode='35'" apk-badging-v044.txt
grep -Fq "versionName='0.4.4'" apk-badging-v044.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v044.txt
unzip -Z1 Darkroom-v0.4.4.apk > apk-listing-v044.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v044.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

# v0.4.4 acceptance.
grep -Fq 'NIKON F100' "$MAINT"
grep -Fq 'Nikon F100 - Manuale IT' "$MAINT"
grep -Fq 'Reflex 35 mm autofocus · 10 FAQ' "$MAINT"
grep -Fq 'Quali batterie usa la Nikon F100?' "$MAINT"
grep -Fq 'quattro batterie AA da 1,5 V' "$MAINT"
grep -Fq 'ISO 25 a 5000' "$MAINT"
grep -Fq 'ISO 6-6400' "$MAINT"
grep -Fq '1/8000 s' "$MAINT"
grep -Fq '1/250 s' "$MAINT"
grep -Fq 'addFaqMatches(hits,"NIKON F100",Q_NIKON_F100,A_NIKON_F100,q);' "$MAINT"
! grep -Fq 'NIKON D100' "$MAINT"
! grep -Fq 'Q_NIKON_D100' "$MAINT"
! grep -Fq 'A_NIKON_D100' "$MAINT"

python3 - <<'PY' | tee validation-v044-faq-guard.txt
from pathlib import Path
s=Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
def count(a,b):
    x=s.index('private static final String[] '+a)
    y=s.index('private static final String[] '+b,x)
    return s[x:y].count('            "')
assert count('Q_NIKON_F100','A_NIKON_F100')==10
assert count('A_NIKON_F100','Q_NIKON_ZOOM100')==10
assert 'NIKON D100' not in s
assert 'NIKON F100' in s
assert 'NIKON_F100_URL = "https://drive.google.com/file/d/1-6_YrOo-hJwlLB4en3-vcBupuHxQm1l9/view?usp=drivesdk"' in s
print('nikon_f100_questions=10')
print('nikon_f100_answers=10')
print('nikon_f100_manual_drive_link=PASS')
print('nikon_d100_removed=PASS')
print('global_faq_search_f100=PASS')
print('battery_faq_4xAA=PASS')
PY

# Prior validated areas must survive unchanged.
grep -Fq 'NIKON L35AF2' "$MAINT"
grep -Fq 'DX automatico' "$MAINT"
grep -Fq 'Quale batteria usa il Minolta Auto Meter IIIF?' "$MAINT"
grep -Fq 'FILTRI E ACCESSORI ROLLEIFLEX' "$MAINT"
grep -Fq 'Heidosmat-Rolleinar 1' "$MAINT"
grep -Fq 'Come si sostituisce correttamente la lampada della Meopta Color 3?' "$MAINT"
grep -Fq 'PROCESSO E LAVAGGIO' "$MAINT"
grep -Fq 'Cerca nelle FAQ…' "$MAINT"
grep -Fq 'ALTEZZA PIANO CARTA (spessore marginatore)' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$ENL"
grep -Fq 'Math.round(ms/500.0)*500' "$ENL"
grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"

python3 - <<'PY' | tee validation-v044-bundled-db.txt
from pathlib import Path
import sqlite3
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776
print('release=Darkroom-v0.4.4')
print('versionName=0.4.4')
print('versionCode=35')
print('base_version=0.4.3')
print('change_scope=NIKON_D100_TO_F100_MANUAL_AND_FAQ')
print('nikon_f100_faq_count=10')
print('nikon_l35af2_unchanged=PASS')
print('minolta_unchanged=PASS')
print('rolleiflex_accessories_unchanged=PASS')
print('color3_lamp_faq_unchanged=PASS')
print('process_wash_faq_unchanged=PASS')
print('global_faq_search_preserved=PASS')
print('paper_plane_logic_unchanged=PASS')
print('sonoff_final_step_seconds=0.5')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
con.close()
PY

cat validation-v043.txt validation-v044-nikon-f100.txt validation-v044-faq-guard.txt validation-v044-bundled-db.txt > validation-v044.txt
sha256sum Darkroom-v0.4.4.apk | tee Darkroom-v0.4.4.sha256
