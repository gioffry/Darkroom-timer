#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.1 - correct Nikon L35AF2 / One Touch manual and FAQs.
# Exact base: verified v0.4.0. Timer, SONOFF, enlargement, paper-plane,
# Minolta manual/FAQ and chemical catalog must remain unchanged.

bash combined/build_v040.sh
python3 combined/patch_v041_nikon_l35af2_manual_faq.py | tee validation-v041-nikon-l35af2.txt

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="32"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.4.1"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.4.1 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 32', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.1'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.4.1 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.1.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.1.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.1.apk > certificate-v041.txt
"$AAPT" dump badging Darkroom-v0.4.1.apk > apk-badging-v041.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v041.txt
grep -Fq "versionCode='32'" apk-badging-v041.txt
grep -Fq "versionName='0.4.1'" apk-badging-v041.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v041.txt
unzip -Z1 Darkroom-v0.4.1.apk > apk-listing-v041.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v041.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

# Nikon L35AF2 acceptance.
grep -Fq 'https://drive.google.com/file/d/1jJn6XXhkkGJqSR9JKD377LqSL7hte14p/view?usp=drivesdk' "$MAINT"
grep -Fq 'NIKON L35AF2' "$MAINT"
grep -Fq 'DX automatico' "$MAINT"
grep -Fq 'ISO 50-1600' "$MAINT"
grep -Fq 'ISO 100' "$MAINT"
grep -Fq '2 batterie AA' "$MAINT"
grep -Fq '0,7-3,6 m' "$MAINT"
grep -Fq 'circa 10 secondi' "$MAINT"
grep -Fq 'circa 20 secondi' "$MAINT"
! grep -Fq 'La sensibilità non viene letta automaticamente: va impostata sulla ghiera ASA/ISO' "$MAINT"
! grep -Fq 'da 50 a 1000 ISO' "$MAINT"

python3 - <<'PY' | tee validation-v041-faq-guard.txt
from pathlib import Path
s=Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
q=s[s.index('private static final String[] Q_NIKON_L35AF'):s.index('private static final String[] A_NIKON_L35AF')]
a=s[s.index('private static final String[] A_NIKON_L35AF'):s.index('private static final String[] Q_NIKON_D100')]
assert q.count('            "')==10
assert a.count('            "')==10
for x in ('NIKON L35AF2','DX automatico','ISO 50-1600','ISO 100','2 batterie AA','0,7-3,6 m'):
    assert x in s,x
assert 'ghiera ASA/ISO, da 50 a 1000 ISO' not in s
print('nikon_l35af2_questions=10')
print('nikon_l35af2_answers=10')
print('dx_auto_iso_50_1600=PASS')
print('non_dx_iso_100=PASS')
print('old_l35af_iso_ring_faq_removed=PASS')
print('manual_link_correct_l35af2_it_pdf=PASS')
PY

# v0.4.0 Minolta and previous operational areas must survive unchanged.
grep -Fq 'Quale batteria usa il Minolta Auto Meter IIIF?' "$MAINT"
grep -Fq '4LR44' "$MAINT"
grep -Fq '2CR-1/3N' "$MAINT"
grep -Fq '4SR44' "$MAINT"
grep -Fq 'ALTEZZA PIANO CARTA (spessore marginatore)' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$ENL"
grep -Fq 'Math.pow((c.beta+1)/(b1+1),2)' "$ENL"
grep -Fq 'Math.round(ms/500.0)*500' "$ENL"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"

python3 - <<'PY' | tee validation-v041-bundled-db.txt
from pathlib import Path
import sqlite3
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776
print('release=Darkroom-v0.4.1')
print('versionName=0.4.1')
print('versionCode=32')
print('base_version=0.4.0')
print('change_scope=NIKON_L35AF2_MANUAL_AND_FAQ')
print('nikon_manual_model=L35AF2_ONE_TOUCH')
print('nikon_manual_language=IT')
print('nikon_faq_count=10')
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

cat validation-v040.txt validation-v041-nikon-l35af2.txt validation-v041-faq-guard.txt validation-v041-bundled-db.txt > validation-v041.txt
sha256sum Darkroom-v0.4.1.apk | tee Darkroom-v0.4.1.sha256
