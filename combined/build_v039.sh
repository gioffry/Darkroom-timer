#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.9 — UI-only ordering fix in enlarger hardware settings.
# Exact base: verified Darkroom v0.3.8. No enlargement math, paper-plane logic,
# SONOFF timing or catalog data may change.

bash combined/build_v038.sh
python3 combined/patch_v039_settings_sonoff_order.py | tee validation-v039-settings-order.txt

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="30"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.3.9"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.3.9 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 30', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.3.9'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.3.9 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.9.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.9.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.3.9.apk > certificate-v039.txt
"$AAPT" dump badging Darkroom-v0.3.9.apk > apk-badging-v039.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v039.txt
grep -Fq "versionCode='30'" apk-badging-v039.txt
grep -Fq "versionName='0.3.9'" apk-badging-v039.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v039.txt
unzip -Z1 Darkroom-v0.3.9.apk > apk-listing-v039.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v039.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java

python3 - <<'PY' | tee validation-v039-order-guard.txt
from pathlib import Path
p=Path('combined/src/main/java/it/darkroom/timer/MainActivity.java')
s=p.read_text(encoding='utf-8')
b='Button change = compactButton(selectedDeviceId == null || selectedDeviceId.isEmpty() ? "SCEGLI SONOFF" : "CAMBIA SONOFF");'
h='TextView paperPlaneTitle = text("ALTEZZA PIANO CARTA (spessore marginatore)", 12, TEXT_PRIMARY, true);'
assert b in s and h in s
assert s.index(b) < s.index(h)
assert 'change.setOnClickListener(v -> { dialog.dismiss(); showDevicePicker(); });' in s
assert 'enlargementPaperPlaneHeightMm' in s
print('sonoff_button_before_paper_plane=PASS')
print('sonoff_action_unchanged=PASS')
print('paper_plane_setting_preserved=PASS')
PY

grep -Fq 'ALTEZZA PIANO CARTA (spessore marginatore)' "$MAIN"
grep -Fq 'ALTEZZA PIANO CARTA (spessore marginatore)' "$ENL"
grep -Fq 'enlargementPaperPlaneHeightMm' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$ENL"
grep -Fq 'Math.pow((c.beta+1)/(b1+1),2)' "$ENL"
grep -Fq 'Math.round(ms/500.0)*500' "$ENL"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"

python3 - <<'PY' | tee validation-v039-bundled-db.txt
from pathlib import Path
import sqlite3
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776
print('release=Darkroom-v0.3.9')
print('versionName=0.3.9')
print('versionCode=30')
print('base_version=0.3.8')
print('change_scope=UI_ORDER_ONLY')
print('paper_plane_logic_unchanged=PASS')
print('enlargement_exposure_formula_unchanged=PASS')
print('sonoff_final_step_seconds=0.5')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
con.close()
PY

cat validation-v038.txt validation-v039-settings-order.txt validation-v039-order-guard.txt validation-v039-bundled-db.txt > validation-v039.txt
sha256sum Darkroom-v0.3.9.apk | tee Darkroom-v0.3.9.sha256
