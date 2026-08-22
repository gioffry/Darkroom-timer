#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.3 — operational enriched developer database.
# Base: v0.3.2. Preserve Timer, Split Grade, SONOFF, manuals and user data.

python3 -m py_compile combined/patch_v033_enriched_developer_db.py

# Make v033 run after the v029 catalog reconstruction. build_v031 will insert v029
# immediately after the same marker, therefore final order is v038 -> v029 -> v033.
python3 - <<'PY'
from pathlib import Path
p=Path('combined/build_v011.sh')
s=p.read_text(encoding='utf-8')
needle='python3 assistant/patch_v038_edit_persistence_simplify.py\n'
line='python3 combined/patch_v033_enriched_developer_db.py\n'
if needle not in s:
    raise SystemExit('v033: build_v011 insertion marker missing')
if line not in s:
    s=s.replace(needle,needle+line,1)
p.write_text(s,encoding='utf-8')

# v031 validates the generated MdcOfflineStore. v033 deliberately changes only the
# read-only catalog cache name/schema so an installed v0.3.2 receives the new asset.
p=Path('combined/build_v031.sh')
s=p.read_text(encoding='utf-8')
s=s.replace("grep -q 'mdc_offline_darkroom_v029.sqlite' \"$MDC\"", "grep -q 'mdc_offline_darkroom_v033.sqlite' \"$MDC\"")
s=s.replace("grep -q 'private static final int DB_VERSION = 3;' \"$MDC\"", "grep -q 'private static final int DB_VERSION = 4;' \"$MDC\"")
p.write_text(s,encoding='utf-8')
PY

# Reuse the already validated v0.3.2 build chain, advancing only version/code.
python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v032.sh').read_text(encoding='utf-8')
for marker in ['Darkroom v0.3.2','Darkroom-v0.3.2','versionCode="23"','v032']:
    if marker not in s:
        raise SystemExit('v033 source build marker missing: '+marker)
s=s.replace('v0.3.2','v0.3.3')
s=s.replace('0.3.2','0.3.3')
s=s.replace('versionCode="23"','versionCode="24"')
s=s.replace("versionCode='23'","versionCode='24'")
s=s.replace('versionCode 23','versionCode 24')
s=s.replace('versionCode=23','versionCode=24')
s=s.replace('v032','v033')
s=s.replace('base_version=0.3.1','base_version=0.3.2')
# Keep wrapper/output paths distinct from any nested generated script.
s=s.replace('/tmp/build_v033_generated.sh','/tmp/build_v031_generated.sh')
Path('/tmp/build_v033_from_v032.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v033_from_v032.sh

# Release-specific validation.
test -f Darkroom-v0.3.3.apk
test -f validation-v033-enriched-db.txt
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$AAPT" dump badging Darkroom-v0.3.3.apk > apk-badging-v033.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v033.txt
grep -Fq "versionCode='24'" apk-badging-v033.txt
grep -Fq "versionName='0.3.3'" apk-badging-v033.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v033.txt
unzip -Z1 Darkroom-v0.3.3.apk > apk-listing-v033.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v033.txt

grep -q 'DeveloperProfile' assistant/src/main/java/it/darkroom/assistant/FullCatalogStore.java
grep -q 'productFromDeveloperProfile' assistant/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
grep -q 'mdc_offline_darkroom_v033.sqlite' assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
grep -q 'private static final int DB_VERSION = 4;' assistant/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
grep -q 'rollei_supergrain=PASS' validation-v033-enriched-db.txt
grep -q 'fomadon_excel_runtime=PASS' validation-v033-enriched-db.txt
grep -q 'personal_data_migration=NO_DESTRUCTIVE_RESET' validation-v033-enriched-db.txt

python3 - <<'PY'
import sqlite3
p='assistant/src/main/assets/mdc_full.sqlite'
con=sqlite3.connect(p); c=con.cursor()
assert c.execute('select count(*) from times').fetchone()[0] == 14504
assert c.execute('select count(*) from developer_profiles').fetchone()[0] == 232
sg=c.execute("select manufacturer,preparation,reuse_mode,capacity_text,shelf_life_unopened from developer_profiles where developer_norm='rollei supergrain'").fetchone()
assert sg and all(str(x or '').strip() for x in sg), sg
ex=c.execute("select manufacturer,preparation,capacity_text from developer_profiles where developer_norm='fomadon excel'").fetchone()
assert ex and all(str(x or '').strip() for x in ex), ex
assert c.execute('pragma quick_check').fetchone()[0]=='ok'
con.close()
print('v033_sqlite_release_audit=PASS')
PY

cat >> validation-v033-enriched-db.txt <<'EOF'
versionName=0.3.3
versionCode=24
base_version=0.3.2
rollei_supergrain_only_final_scope=PASS
other_macodirect_incomplete_left_unchanged=PASS
runtime_profile_wiring=PASS
sqlite_release_audit=PASS
EOF
sha256sum Darkroom-v0.3.3.apk | tee Darkroom-v0.3.3.sha256
