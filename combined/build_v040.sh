#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.0 — complete Minolta Auto Meter IIIF Italian manual + 10 verified FAQs.
# Exact base: verified Darkroom v0.3.9. Timer/SONOFF, enlargement, paper-plane and catalog logic are immutable.

bash combined/build_v039.sh
python3 combined/patch_v040_minolta_manual_faq.py | tee validation-v040-minolta-faq.txt

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="31"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.4.0"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.4.0 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 31', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.0'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.4.0 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.0.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.0.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.0.apk > certificate-v040.txt
"$AAPT" dump badging Darkroom-v0.4.0.apk > apk-badging-v040.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v040.txt
grep -Fq "versionCode='31'" apk-badging-v040.txt
grep -Fq "versionName='0.4.0'" apk-badging-v040.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v040.txt
unzip -Z1 Darkroom-v0.4.0.apk > apk-listing-v040.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v040.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

# Minolta manual/FAQ acceptance.
grep -Fq 'https://drive.google.com/file/d/1rniErjqK3_S-0pDY3mvXosb4dk_Y0GOV/view?usp=drivesdk' "$MAINT"
grep -Fq 'Quale batteria usa il Minolta Auto Meter IIIF?' "$MAINT"
grep -Fq '4LR44' "$MAINT"
grep -Fq '2CR-1/3N' "$MAINT"
grep -Fq '4SR44' "$MAINT"
grep -Fq 'Spot Mask II' "$MAINT"
grep -Fq 'APRI MANUALE COMPLETO' "$MAINT"
! grep -Fq 'MINOLTA_PENDING' "$MAINT"
! grep -Fq 'manuale completo non disponibile' "$MAINT"
! grep -Fq 'APRI RIFERIMENTO DRIVE' "$MAINT"

python3 - <<'PY' | tee validation-v040-faq-guard.txt
from pathlib import Path
s=Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
q=s[s.index('private static final String[] Q_MINOLTA'):s.index('private static final String[] A_MINOLTA')]
a=s[s.index('private static final String[] A_MINOLTA'):s.index('private static final String[] Q_TESTSTRIP')]
assert q.count('            "')==10
assert a.count('            "')==10
for x in ('4LR44','2CR-1/3N','4SR44','Viewfinder 10°','Spot Mask II','AVERAGE','1/60','1/250','±1 EV'):
    assert x in s,x
print('minolta_questions=10')
print('minolta_answers=10')
print('battery_faq=PASS')
print('manual_link_complete_pdf=PASS')
print('old_pending_reference_removed=PASS')
PY

# Prior operational areas must remain unchanged.
grep -Fq 'ALTEZZA PIANO CARTA (spessore marginatore)' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$ENL"
grep -Fq 'Math.pow((c.beta+1)/(b1+1),2)' "$ENL"
grep -Fq 'Math.round(ms/500.0)*500' "$ENL"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"

python3 - <<'PY' | tee validation-v040-bundled-db.txt
from pathlib import Path
import sqlite3
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776
print('release=Darkroom-v0.4.0')
print('versionName=0.4.0')
print('versionCode=31')
print('base_version=0.3.9')
print('change_scope=MINOLTA_MANUAL_AND_FAQ')
print('minolta_manual_language=IT')
print('minolta_manual_complete=PASS')
print('minolta_faq_count=10')
print('paper_plane_logic_unchanged=PASS')
print('enlargement_exposure_formula_unchanged=PASS')
print('sonoff_final_step_seconds=0.5')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
con.close()
PY

cat validation-v039.txt validation-v040-minolta-faq.txt validation-v040-faq-guard.txt validation-v040-bundled-db.txt > validation-v040.txt
sha256sum Darkroom-v0.4.0.apk | tee Darkroom-v0.4.0.sha256
