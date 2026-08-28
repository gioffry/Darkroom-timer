#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.8 — configurable paper-plane height for portable easels.
# Exact base: verified Darkroom v0.3.7 (versionCode 28).
# Existing Opemus 6 calibration, enlargement exposure formula and SONOFF 0.5 s
# final timing quantization remain unchanged.

bash combined/build_v037.sh

python3 combined/patch_v038_paper_plane_height.py | tee validation-v038-paper-plane.txt

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="29"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.3.8"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.3.8 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 29', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.3.8'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.3.8 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.8.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.8.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.3.8.apk > certificate-v038.txt
"$AAPT" dump badging Darkroom-v0.3.8.apk > apk-badging-v038.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v038.txt
grep -Fq "versionCode='29'" apk-badging-v038.txt
grep -Fq "versionName='0.3.8'" apk-badging-v038.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v038.txt
unzip -Z1 Darkroom-v0.3.8.apk > apk-listing-v038.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v038.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

grep -Fq 'ALTEZZA PIANO CARTA (spessore marginatore)' "$MAIN"
grep -Fq 'ALTEZZA PIANO CARTA (spessore marginatore)' "$ENL"
grep -Fq 'enlargementPaperPlaneHeightMm' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$ENL"
grep -Fq 'paperPlaneMm=%.1f' "$ENL"
grep -Fq 'effectiveCol=%.8f' "$ENL"
grep -Fq 'physicalCol(c.col,plane)' "$ENL"
grep -Fq 'metaPlaneMm(old)' "$ENL"
grep -Fq '0–50 mm' "$ENL"
grep -Fq '− 0,5 mm' "$ENL"
grep -Fq '+ 0,5 mm' "$ENL"

grep -Fq 'static final double[][] C80={{1,6},{1.5,7},{2,10},{2.5,13},{3,17},{3.5,20},{4,24},{5,32},{6,40},{7,48},{7.6,53}};' "$ENL"
grep -Fq 'static final double[][] C50={{2.5,1},{3,2},{3.5,4},{4,6},{5,11},{6,16},{7,21},{7.6,24},{9,32},{10,37},{11,42},{13,52}};' "$ENL"
grep -Fq 'Math.pow((c.beta+1)/(b1+1),2)' "$ENL"
grep -Fq 'Math.round(ms/500.0)*500' "$ENL"
grep -Fq 'if(n.hasSplit()){n.split.softMs=snap(n.split.softMs*factor);n.split.hardMs=snap(n.split.hardMs*factor);n.split.sanitize();}' "$ENL"

grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"

python3 - <<'PY' | tee validation-v038-bundled-db.txt
from pathlib import Path
import sqlite3
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776
print('release=Darkroom-v0.3.8')
print('versionName=0.3.8')
print('versionCode=29')
print('base_version=0.3.7')
print('paper_plane_default_mm=0')
print('paper_plane_range_mm=0..50')
print('paper_plane_precision_mm=0.5_or_better')
print('legacy_recipe_missing_paperPlaneMm=0')
print('opemus6_calibration_unchanged=PASS')
print('enlargement_exposure_formula_unchanged=PASS')
print('sonoff_final_step_seconds=0.5')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
con.close()
PY

cat validation-v037.txt validation-v038-paper-plane.txt validation-v038-bundled-db.txt > validation-v038.txt
sha256sum Darkroom-v0.3.8.apk | tee Darkroom-v0.3.8.sha256
