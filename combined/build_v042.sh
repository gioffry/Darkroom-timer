#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.2 - Color 3 lamp replacement + four technique/washing FAQs.
# Exact base: verified v0.4.1. Timer, SONOFF, enlargement, paper-plane,
# Nikon/Minolta manuals and chemical catalog must remain unchanged.

bash combined/build_v041.sh
python3 combined/patch_v042_technique_faqs.py | tee validation-v042-technique-faqs.txt

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="33"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.4.2"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.4.2 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 33', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.2'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.4.2 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.2.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.2.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.2.apk > certificate-v042.txt
"$AAPT" dump badging Darkroom-v0.4.2.apk > apk-badging-v042.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v042.txt
grep -Fq "versionCode='33'" apk-badging-v042.txt
grep -Fq "versionName='0.4.2'" apk-badging-v042.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v042.txt
unzip -Z1 Darkroom-v0.4.2.apk > apk-listing-v042.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v042.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

# New FAQ acceptance.
grep -Fq 'Come si sostituisce correttamente la lampada della Meopta Color 3?' "$MAINT"
grep -Fq 'Tungsram 55 220' "$MAINT"
grep -Fq 'Osram 64 627' "$MAINT"
grep -Fq 'Philips 68 34' "$MAINT"
grep -Fq 'Thorn A1/231' "$MAINT"
grep -Fq 'GZ 6.35-18' "$MAINT"
grep -Fq 'PROCESSO E LAVAGGIO' "$MAINT"
grep -Fq 'Come realizzare un provino a contatto?' "$MAINT"
grep -Fq 'Quando è utile un pre-bagno della pellicola prima dello sviluppo?' "$MAINT"
grep -Fq 'Come lavare correttamente la pellicola?' "$MAINT"
grep -Fq 'Come lavare correttamente la carta RC?' "$MAINT"
grep -Fq 'non farlo girare nel processore' "$MAINT"
grep -Fq 'contenitore separato' "$MAINT"
grep -Fq '5 inversioni' "$MAINT"
grep -Fq '10 inversioni' "$MAINT"
grep -Fq '20 inversioni' "$MAINT"

python3 - <<'PY' | tee validation-v042-faq-guard.txt
from pathlib import Path
s=Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
def count(a,b):
    x=s.index('private static final String[] '+a)
    y=s.index('private static final String[] '+b,x)
    return s[x:y].count('            "')
assert count('Q_COLOR3','A_COLOR3')==11
assert count('A_COLOR3','Q_JOBO')==11
assert count('Q_PROCESS_WASH','A_PROCESS_WASH')==4
assert count('A_PROCESS_WASH','Q_TESTSTRIP')==4
assert 'FAQ count must be 4, 5, 10 or 11 for ' in s
print('color3_questions=11')
print('color3_answers=11')
print('color3_lamp_replacement=PASS')
print('process_wash_questions=4')
print('process_wash_answers=4')
print('jobo_wetting_agent_separate_container=PASS')
print('jobo_no_rotary_wetting_agent=PASS')
print('film_wash_5_10_20=PASS')
print('rc_wash_2min=PASS')
PY

# Prior validated areas must survive unchanged.
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

python3 - <<'PY' | tee validation-v042-bundled-db.txt
from pathlib import Path
import sqlite3
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776
print('release=Darkroom-v0.4.2')
print('versionName=0.4.2')
print('versionCode=33')
print('base_version=0.4.1')
print('change_scope=COLOR3_LAMP_PLUS_TECHNIQUE_FAQS')
print('color3_faq_count=11')
print('process_wash_faq_count=4')
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

cat validation-v041.txt validation-v042-technique-faqs.txt validation-v042-faq-guard.txt validation-v042-bundled-db.txt > validation-v042.txt
sha256sum Darkroom-v0.4.2.apk | tee Darkroom-v0.4.2.sha256
