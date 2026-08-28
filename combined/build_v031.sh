#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.1 — full offline Massive Dev Chart catalog.
# Base verified: Darkroom v0.3.0 / versionCode 21.
# Preserve camera manuals/FAQ, Timer, Split Grade and SONOFF behavior.

python3 -m py_compile combined/patch_v029_full_offline_catalog.py combined/validate_v029_catalog.py

# Inject the catalog patch into the Assistant reconstruction immediately after v0.3.8.
python3 - <<'PY'
from pathlib import Path
p=Path('combined/build_v011.sh')
s=p.read_text(encoding='utf-8')
needle='python3 assistant/patch_v038_edit_persistence_simplify.py\n'
insert=needle+'python3 combined/patch_v029_full_offline_catalog.py\n'
if needle not in s:
    raise SystemExit('v0.3.1: Assistant v0.3.8 insertion marker missing')
if 'patch_v029_full_offline_catalog.py' not in s:
    s=s.replace(needle,insert,1)
p.write_text(s,encoding='utf-8')
PY

# Reuse the verified v0.3.0 reconstruction, only advancing app version/code.
python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v030.sh').read_text(encoding='utf-8')
for marker in ['Darkroom v0.3.0','Darkroom-v0.3.0','versionCode="21"',"s=s.replace('0.2.8','0.3.0')"]:
    if marker not in s:
        raise SystemExit('v0.3.1 source build marker missing: '+marker)
# Critical nested target: build_v030 itself transforms build_v028 0.2.8 -> 0.3.0.
# Advance that target too, otherwise the inner reconstruction still emits 0.3.0.
s=s.replace("s=s.replace('0.2.8','0.3.0')", "s=s.replace('0.2.8','0.3.1')", 1)
s=s.replace('Darkroom v0.3.0','Darkroom v0.3.1')
s=s.replace('Darkroom-v0.3.0','Darkroom-v0.3.1')
s=s.replace('versionName="0.3.0"','versionName="0.3.1"')
s=s.replace("versionName='0.3.0'","versionName='0.3.1'")
s=s.replace("versionName '0.3.0'","versionName '0.3.1'")
s=s.replace('versionName=0.3.0','versionName=0.3.1')
s=s.replace('versionCode="21"','versionCode="22"')
s=s.replace("versionCode='21'","versionCode='22'")
s=s.replace('versionCode 21','versionCode 22')
s=s.replace('versionCode=21','versionCode=22')
s=s.replace('apk-listing-v030.txt','apk-listing-v031.txt')
Path('/tmp/build_v031_generated.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v031_generated.sh

# Full catalog validation against the actual SQLite generated in this run.
python3 combined/validate_v029_catalog.py
cp validation-v029-catalog.txt validation-v031-catalog.txt
cat >> validation-v031-catalog.txt <<'EOF'
versionName=0.3.1
versionCode=22
base_version=0.3.0
base_camera_manuals_preserved=PASS
catalog_release=FULL_OFFLINE_MDC
personal_data_migration=NO_DESTRUCTIVE_RESET
EOF

test -f Darkroom-v0.3.1.apk
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$AAPT" dump badging Darkroom-v0.3.1.apk > apk-badging-v031.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v031.txt
grep -Fq "versionCode='22'" apk-badging-v031.txt
grep -Fq "versionName='0.3.1'" apk-badging-v031.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v031.txt
unzip -Z1 Darkroom-v0.3.1.apk > apk-listing-v031.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v031.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
STORE=combined/src/main/java/it/darkroom/assistant/FullCatalogStore.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
CHEM=combined/src/main/java/it/darkroom/assistant/ChemistrySpecEngine.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java

grep -q 'ROLE_WETTING = 16' "$ASSIST"
grep -q 'ROLE_WASHING = 32' "$ASSIST"
grep -q 'FullCatalogStore.searchChemicalNames' "$ASSIST"
grep -q 'Unified OFFLINE catalog' "$STORE"
grep -q 'Kodak D-76' "$STORE"
grep -q 'Kodak XTOL' "$STORE"
grep -q 'Ilford ID-11' "$STORE"
grep -q 'Ilford DD-X' "$STORE"
grep -q 'Adox Rodinal' "$STORE"
grep -q 'mdc_offline_darkroom_v029.sqlite' "$MDC"
grep -q 'private static final int DB_VERSION = 3;' "$MDC"
grep -q 'catalogo completamente offline' "$CHEM"

# v0.3.0 content must still be present.
grep -Fq 'NIKON L35AF' "$MAINT"
grep -Fq 'NIKON D100' "$MAINT"
grep -Fq 'NIKON ZOOM 100 AF' "$MAINT"
grep -Fq 'ROLLEIFLEX 3.5 AUTOMAT MX' "$MAINT"
grep -Fq 'ROLLEIFLEX 2.8 E2' "$MAINT"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"

grep -q 'fomatol_lqn=PASS' validation-v031-catalog.txt
grep -q 'catalog_validation=PASS' validation-v031-catalog.txt

grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt
sha256sum Darkroom-v0.3.1.apk | tee Darkroom-v0.3.1.sha256
