#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.6 - JOBO/LPL 7451, 35 mm / 6x6 / 4x5, LPL filter grades,
# Italian manual and one-time reset of print state tied to the previous enlarger.
# Exact base: verified v0.4.5, including Zone System and Minolta/Rolleiflex EV work.

bash combined/build_v045_r2.sh
python3 combined/patch_v046_lpl7451.py | tee validation-v046-lpl7451-patch.txt

python3 - <<'PY'
from pathlib import Path
import re

p = Path('combined/src/main/AndroidManifest.xml')
s = p.read_text(encoding='utf-8')
s, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="37"', s, count=1)
s, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.4.6"', s, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit('v0.4.6 manifest version update failed')
p.write_text(s, encoding='utf-8')

g = Path('combined/build.gradle')
gs = g.read_text(encoding='utf-8')
gs, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 37', gs, count=1)
gs, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.6'", gs, count=1)
if n3 != 1 or n4 != 1:
    raise SystemExit('v0.4.6 Gradle version update failed')
g.write_text(gs, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.6.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.6.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.6.apk > certificate-v046.txt
"$AAPT" dump badging Darkroom-v0.4.6.apk > apk-badging-v046.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v046.txt
grep -Fq "versionCode='37'" apk-badging-v046.txt
grep -Fq "versionName='0.4.6'" apk-badging-v046.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v046.txt
unzip -Z1 Darkroom-v0.4.6.apk > apk-listing-v046.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v046.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
MIGRATION=combined/src/main/java/it/darkroom/timer/Lpl7451Migration.java
SPLIT=combined/src/main/java/it/darkroom/timer/SplitGradePlan.java
JPEG=combined/src/main/java/it/darkroom/timer/JpegCardRenderer.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

# v0.4.6 acceptance: one enlarger, three formats and no invented column curve.
grep -Fq 'static final String LPL_MODEL = "LPL7451"' "$ENL"
grep -Fq '"35", "66", "45"' "$ENL"
grep -Fq '"35 mm · 24 × 36 mm · obiettivo 50 mm"' "$ENL"
grep -Fq '"6×6 · 56 × 56 mm · obiettivo 75 mm"' "$ENL"
grep -Fq '"4×5 · 101,6 × 127 mm · obiettivo 150 mm"' "$ENL"
grep -Fq 'carrier=35mm' "$ENL" || grep -Fq 'carrier=%s' "$ENL"
grep -Fq 'columnCalibration=PENDING' "$ENL"
grep -Fq 'Math.pow((c.beta+1)/(b1+1),2)' "$ENL"
grep -Fq 'Math.round(ms / 500.0) * 500' "$ENL"
if grep -Fq 'b2c(' "$ENL" || grep -Fq 'C50={{' "$ENL" || grep -Fq 'C80={{' "$ENL"; then
  echo 'Obsolete physical column calibration survived' >&2
  exit 1
fi
if grep -RFiq 'OPEMUS' combined/src/main/java/it/darkroom/timer; then
  echo 'Obsolete enlarger reference survived in app source' >&2
  exit 1
fi

# Automatic format/lens/carrier persistence and LOG support.
grep -Fq 'lensMm(format)' "$ENL"
grep -Fq 'carrierCode(format)' "$ENL"
grep -Fq 'd.negative = logNegative(x.negativeCode)' "$ENL"
grep -Fq 'setLogFilter("4x5")' "$MAIN"
grep -Fq 'logFilter45Button' "$MAIN"
grep -Fq 'compactButton("4×5")' "$MAIN"
grep -Fq 'if ("4x5".equalsIgnoreCase(v)) return "4×5"' "$JPEG"
grep -Fq '"Ingrandimento β"' "$JPEG"

# LPL contrast table and unchanged two-phase Split Grade structure.
grep -Fq '"Y60 / M0", "Y30 / M0", "Y0 / M10", "Y0 / M40", "Y0 / M90", "Y0 / M130"' "$MAIN"
grep -Fq '"GRADO 0 · Y60 / M0"' "$MAIN"
grep -Fq '"GRADO 5 · Y0 / M130"' "$MAIN"
grep -Fq 'public int hardMagenta = 130;' "$SPLIT"
grep -Fq 'Split Grade morbido' "$ENL"
grep -Fq 'Split Grade duro' "$ENL"

# Explicit, one-time reset of print recipes/logs tied to the previous enlarger.
grep -Fq 'lpl7451MigrationV046Done' "$MIGRATION"
grep -Fq 'LogStore.replaceAll(context, new ArrayList<LogEntry>())' "$MIGRATION"
grep -Fq '.remove("exposureRecipe")' "$MIGRATION"
grep -Fq '.remove("printSequence")' "$MIGRATION"
grep -Fq '.remove("enlargementMeta")' "$MIGRATION"
if grep -Fq 'enlargementPaperPlaneHeightMm' "$MAIN" || grep -Fq 'enlargementPaperPlaneHeightMm' "$ENL"; then
  echo 'Legacy physical column setting survived' >&2
  exit 1
fi

# Italian LPL manual and FAQ integration.
grep -Fq 'JOBO/LPL 7451' "$MAINT"
grep -Fq '1y67xUwISxjz8f4-QFmBUOquabVezXq4A' "$MAINT"
grep -Fq 'APRI MANUALE COMPLETO IT' "$MAINT"
grep -Fq 'Q_LPL7451' "$MAINT"
grep -Fq 'La ventola deve restare accesa durante l’uso?' "$MAINT"

# v0.4.5 EV/Zone work and the rest of the cumulative application survive.
grep -Fq 'Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?' "$MAINT"
grep -Fq '| 1/125 ★ | 9,9 | — | 11,0 | 11,9 | 13,0 | 13,9 | 15,0 | 15,9 |' "$MAINT"
grep -Fq 'Come posso usare il Sistema Zonale con il Minolta Auto Meter III F?' "$MAINT"
grep -Fq 'Come utilizzo rapidamente il Sistema Zonale sul campo?' "$MAINT"
grep -Fq 'NIKON F100' "$MAINT"
grep -Fq 'NIKON L35AF2' "$MAINT"
grep -Fq 'FILTRI E ACCESSORI ROLLEIFLEX' "$MAINT"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"

python3 - <<'PY' | tee validation-v046-source.txt
from pathlib import Path
import re
import sqlite3

root = Path('combined/src/main/java/it/darkroom/timer')
maint = (root / 'maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
main = (root / 'MainActivity.java').read_text(encoding='utf-8')
enl = (root / 'EnlargementActivity.java').read_text(encoding='utf-8')

def array_body(name):
    marker = 'private static final String[] ' + name + ' = {'
    start = maint.index(marker)
    body_start = maint.index('{', start) + 1
    end = maint.index('\n    };', body_start)
    return maint[body_start:end]

def count_strings(name):
    return len(re.findall(r'"(?:\\.|[^"\\])*"', array_body(name)))

assert count_strings('Q_LPL7451') == 10
assert count_strings('A_LPL7451') == 10
assert count_strings('Q_MINOLTA') == 12
assert count_strings('A_MINOLTA') == 12
assert count_strings('Q_ZONE') == 11
assert count_strings('A_ZONE') == 11
assert main.count('setLogFilter("4x5")') == 1
assert 'M180' not in main
assert 'b2c(' not in enl
assert 'paperPlane' not in enl

db = Path('combined/src/main/assets/mdc_full.sqlite')
con = sqlite3.connect(db)
cur = con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0] == 'ok'
assert cur.execute('select count(*) from times').fetchone()[0] == 14504
assert cur.execute('select count(*) from films').fetchone()[0] == 347
assert cur.execute('select count(*) from developers').fetchone()[0] == 232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0] == 776
con.close()

print('release=Darkroom-v0.4.6')
print('versionName=0.4.6')
print('versionCode=37')
print('base_version=0.4.5')
print('enlarger=JOBO/LPL_7451_ONLY')
print('negative_formats=35mm,6x6,4x5')
print('automatic_lenses=50mm,75mm,150mm')
print('physical_column_calibration=DEFERRED')
print('lpl_manual_it=PASS')
print('lpl_grade_table=PASS')
print('split_grade_structure_preserved=PASS')
print('legacy_print_state_reset_once=PASS')
print('ev_zone_work_preserved=PASS')
print('sonoff_final_step_seconds=0.5')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
PY

cat validation-v045.txt validation-v046-lpl7451-patch.txt validation-v046-source.txt > validation-v046.txt
sha256sum Darkroom-v0.4.6.apk | tee Darkroom-v0.4.6.sha256
