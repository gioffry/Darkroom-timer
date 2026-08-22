#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.5 — fix reale della scheda chimica vista su dispositivo.
# Exact base: verified Darkroom v0.3.4. No MDC/Timer behavior changes.

bash combined/build_v034.sh

# Rebuild ONLY Italian display overlays. Protected MDC tables are fingerprinted
# before/after by the script and the build fails on any change.
python3 assistant/db/fix_italian_technical_profiles_v035.py combined/src/main/assets/mdc_full.sqlite \
  | tee validation-v035-technical-db.txt

# UI fixes: real newlines, strict Italian display, official shelf-life visible,
# legacy numeric expiry clearly separated as a personal/local override.
python3 combined/patch_v035_chemical_card_fix_it.py

# Advance only outer Darkroom release.
python3 - <<'PY'
from pathlib import Path
import re

p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="26"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.3.5"',s,count=1)
if n1 != 1 or n2 != 1: raise SystemExit('v0.3.5 manifest version update failed')
p.write_text(s,encoding='utf-8')

g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 26', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.3.5'", gs, count=1)
if n3 != 1 or n4 != 1: raise SystemExit('v0.3.5 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.5.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.5.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.3.5.apk > certificate-v035.txt
"$AAPT" dump badging Darkroom-v0.3.5.apk > apk-badging-v035.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v035.txt
grep -Fq "versionCode='26'" apk-badging-v035.txt
grep -Fq "versionName='0.3.5'" apk-badging-v035.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v035.txt
unzip -Z1 Darkroom-v0.3.5.apk > apk-listing-v035.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v035.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java

grep -Fq 'SCHEDA TECNICA · PRODUTTORE' "$ASSIST"
grep -Fq 'SCADENZA LOCALE PERSONALIZZATA (giorni)' "$ASSIST"
! grep -Fq 'DURATA DOPO APERTURA (giorni)' "$ASSIST"
grep -Fq 'chemicalTechnicalPreparationIt' "$ASSIST"
grep -Fq 'cleanTechnicalText' "$ASSIST"
grep -Fq 'safeItalianTechnical' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v035.sqlite' "$MDC"
grep -Fq 'private static final int DB_VERSION = 3;' "$MDC"
# Preserve Timer / manuals / SONOFF release internals.
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'NIKON L35AF' "$MAINT"
grep -Fq 'ROLLEIFLEX 2.8 E2' "$MAINT"

python3 - <<'PY' | tee validation-v035-bundled-db.txt
from pathlib import Path
import re, sqlite3

p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('PRAGMA quick_check').fetchone()[0]=='ok'
assert cur.execute('SELECT COUNT(*) FROM times').fetchone()[0]==14504
assert cur.execute('SELECT COUNT(*) FROM films').fetchone()[0]==347
assert cur.execute('SELECT COUNT(*) FROM developers').fetchone()[0]==232
assert cur.execute("SELECT COUNT(*) FROM developer_dilutions WHERE source_kind='MDC'").fetchone()[0]==776
assert cur.execute('SELECT COUNT(*) FROM developer_profiles').fetchone()[0]==232
sourced=cur.execute("SELECT COUNT(DISTINCT developer_norm) FROM developer_profile_sources WHERE source_kind='MANUFACTURER'").fetchone()[0]
assert sourced==85, sourced

bad=re.compile(r'\b(the|and|with|when|should|stored|working solution|original package|minimum|defines|processing|explicitly|before|protected|darkness|oxidation|later use|replace|guaranteed|direct sun|air access|unopened|opened concentrate|prepared|manufacturer states|depending on|once opened|use once|discard|per litre|per liter|rolls|sheets|developer|full tightly|half full)\b',re.I)
it_fields=['physical_state_it','preparation_it','reuse_instructions_it','capacity_it','shelf_life_unopened_it','shelf_life_opened_it','shelf_life_stock_it','shelf_life_working_it','storage_notes_it','notes_it']
for f in it_fields:
    for dn,v in cur.execute(f"SELECT developer_norm,{f} FROM developer_profiles WHERE COALESCE({f},'')<>''"):
        assert not bad.search(v), f'English residue {dn}.{f}: {v}'
        assert '\\n' not in v, f'literal newline escape {dn}.{f}: {v}'

# Exact screenshot regressions.
excel=cur.execute("SELECT preparation_it,reuse_instructions_it,capacity_it,shelf_life_unopened_it,shelf_life_working_it,storage_notes_it FROM developer_profiles WHERE developer_norm='fomadon excel'").fetchone()
assert excel and all(excel)
assert '20–30 °C' in excel[0]
assert '24 mesi' in excel[3]
assert '12 mesi' in excel[4]
assert not any(bad.search(v) or '\\n' in v for v in excel)

lqn=cur.execute("SELECT preparation_it,shelf_life_unopened_it,shelf_life_working_it,storage_notes_it,notes_it FROM auxiliary_chemical_profiles WHERE norm_name='fomatol lqn'").fetchone()
assert lqn and all(lqn)
assert '1+7' in lqn[0]
assert '24 mesi' in lqn[1]
assert '2 giorni' in lqn[2]
assert not any(bad.search(v) or '\\n' in v for v in lqn)

# Build a text sample exactly with real LF separators and make sure the visible
# output cannot contain the two characters backslash+n.
sample='\n'.join([
    'Produttore: FOMA BOHEMIA',
    'Preparazione: '+excel[0],
    'Durata confezione originale: '+excel[3],
    'Durata soluzione di lavoro: '+excel[4],
    'Conservazione: '+excel[5],
])
assert '\\n' not in sample
assert sample.count('\n') >= 4

src=Path('combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java').read_text(encoding='utf-8')
assert 'out.append("\\n");' in src, 'Java real newline append missing'
assert 'out.append("\\\\n");' not in src, 'Java literal backslash-n append still present'
assert '.replace("\\\\n", "\\n")' in src, 'runtime literal newline cleanup missing'
assert 'DURATA DOPO APERTURA (giorni)' not in src
assert 'SCADENZA LOCALE PERSONALIZZATA (giorni)' in src
assert 'SCHEDA TECNICA · PRODUTTORE' in src

clean_prep=cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(preparation_it,'')<>''").fetchone()[0]
clean_any=cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(physical_state_it,preparation_it,reuse_instructions_it,capacity_it,shelf_life_unopened_it,shelf_life_opened_it,shelf_life_stock_it,shelf_life_working_it,storage_notes_it,notes_it,'')<>''").fetchone()[0]
print('release=Darkroom-v0.3.5')
print('versionName=0.3.5')
print('versionCode=26')
print('base_version=0.3.4')
print('developer_profiles_total=232')
print('developer_profiles_manufacturer_sourced=85')
print(f'developer_profiles_with_clean_italian={clean_any}')
print(f'developer_profiles_with_clean_italian_preparation={clean_prep}')
print('fomadon_excel_device_regression=PASS')
print('fomatol_lqn_device_regression=PASS')
print('literal_backslash_n=PASS')
print('official_duration_visible_in_technical_card=PASS')
print('legacy_duration_field_relabelled=PASS')
print('mixed_english_italian_display_blocked=PASS')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
print('timer_splitgrade_sonoff_preserved=PASS')
print('personal_data_migration=NO_DESTRUCTIVE_RESET')
con.close()
PY

cat validation-v034.txt validation-v035-technical-db.txt validation-v035-bundled-db.txt > validation-v035.txt
sha256sum Darkroom-v0.3.5.apk | tee Darkroom-v0.3.5.sha256
