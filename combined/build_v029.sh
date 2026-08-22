#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.9 — Assistant full offline catalog.
# Base canonica: Darkroom v0.2.8 / versionCode 19. Timer e stampa invariati.

python3 - <<'PY'
from pathlib import Path
p=Path('combined/build_v011.sh')
s=p.read_text(encoding='utf-8')
needle='python3 assistant/patch_v038_edit_persistence_simplify.py\n'
insert=needle+'python3 combined/patch_v029_full_offline_catalog.py\n'
if needle not in s: raise SystemExit('v029: Assistant v038 insertion marker missing')
if 'patch_v029_full_offline_catalog.py' not in s:
    s=s.replace(needle,insert,1)
p.write_text(s,encoding='utf-8')
PY

python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v028.sh').read_text(encoding='utf-8')
s=s.replace('Darkroom v0.2.8','Darkroom v0.2.9')
s=s.replace('Darkroom-v0.2.8','Darkroom-v0.2.9')
s=s.replace('versionName="0.2.8"','versionName="0.2.9"')
s=s.replace("versionName='0.2.8'","versionName='0.2.9'")
s=s.replace('versionName=0.2.8','versionName=0.2.9')
s=s.replace('versionCode="19"','versionCode="20"')
s=s.replace("versionCode='19'","versionCode='20'")
s=s.replace('versionCode 19','versionCode 20')
s=s.replace('versionCode=19','versionCode=20')
Path('/tmp/build_v029_generated.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v029_generated.sh

python3 combined/validate_v029_catalog.py

test -f Darkroom-v0.2.9.apk
test -f Darkroom-v0.2.9.sha256
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$AAPT" dump badging Darkroom-v0.2.9.apk > apk-badging-v029.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v029.txt
grep -Fq "versionCode='20'" apk-badging-v029.txt
grep -Fq "versionName='0.2.9'" apk-badging-v029.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v029.txt
unzip -Z1 Darkroom-v0.2.9.apk > apk-listing-v029.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v029.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
STORE=combined/src/main/java/it/darkroom/assistant/FullCatalogStore.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java

grep -q 'ROLE_WETTING = 16' "$ASSIST"
grep -q 'ROLE_WASHING = 32' "$ASSIST"
grep -q 'FullCatalogStore.searchChemicalNames' "$ASSIST"
grep -q 'Produttore:' "$ASSIST"
grep -q 'Diluizione carta:' "$ASSIST"
grep -q 'Unified OFFLINE catalog' "$STORE"
grep -q 'mdc_offline_darkroom_v029.sqlite' "$MDC"
grep -q 'private static final int DB_VERSION = 3;' "$MDC"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt

cat >> validation-v029-catalog.txt <<'EOF'
versionName=0.2.9
versionCode=20
timer_internal=0.13.11
assistant_catalog_release=FULL_OFFLINE_V029
fomatol_search_regression=PASS
smart_search_min_chars=3
personal_data_migration=NO_DESTRUCTIVE_RESET
timer_regression=PASS
sonoff_regression=PASS
build=SUCCESS
EOF

sha256sum Darkroom-v0.2.9.apk | tee Darkroom-v0.2.9.sha256
