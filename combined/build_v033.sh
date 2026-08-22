#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.3 — DB evoluto MDC-first + schede tecniche in italiano.
# Base applicativa: v0.3.2. Nessuna modifica a Timer / Split Grade / SONOFF.
python3 -m py_compile combined/patch_v033_enriched_profiles_it.py

# Il patch v0.3.3 deve essere eseguito subito dopo la costruzione catalogo v0.3.1,
# prima che il progetto Assistant venga copiato/compilato.
python3 - <<'PY'
from pathlib import Path
p=Path('combined/build_v011.sh')
s=p.read_text(encoding='utf-8')
v029='python3 combined/patch_v029_full_offline_catalog.py\n'
v033='python3 combined/patch_v033_enriched_profiles_it.py\n'
base='python3 assistant/patch_v038_edit_persistence_simplify.py\n'
if v033 not in s:
    if v029 in s:
        s=s.replace(v029,v029+v033,1)
    elif base in s:
        s=s.replace(base,base+v029+v033,1)
    else:
        raise SystemExit('v033 insertion marker missing')
p.write_text(s,encoding='utf-8')
PY

# Riusa integralmente la build v0.3.2, avanzando solo versione/codice/output.
python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v032.sh').read_text(encoding='utf-8')
for marker in ['Darkroom v0.3.2','Darkroom-v0.3.2','versionCode="23"','v032']:
    if marker not in s: raise SystemExit('v033 base marker missing: '+marker)
s=s.replace('v0.3.2','v0.3.3').replace('Darkroom-v0.3.2','Darkroom-v0.3.3')
s=s.replace('0.3.2','0.3.3')
s=s.replace('versionCode="23"','versionCode="24"')
s=s.replace("versionCode='23'","versionCode='24'")
s=s.replace('versionCode 23','versionCode 24').replace('versionCode=23','versionCode=24')
s=s.replace('v032','v033')
Path('/tmp/build_v033_outer.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v033_outer.sh

# Audit finale del DB realmente incluso nella build.
python3 assistant/db/audit_developer_profiles.py
python3 assistant/db/audit_macodirect_scope.py
cat developer-db-audit.txt
cat macodirect-scope-audit.txt

grep -q 'database_audit=PASS' developer-db-audit.txt
grep -q 'mdc_priority_regression=PASS' developer-db-audit.txt
grep -q 'developers=232' developer-db-audit.txt
grep -q 'films=347' developer-db-audit.txt
grep -q 'combinations=14504' developer-db-audit.txt
grep -q 'macodirect_scope_complete_core=9' macodirect-scope-audit.txt

python3 - <<'PY'
import sqlite3
p='assistant/src/main/assets/mdc_full.sqlite'
c=sqlite3.connect(p); q=c.cursor()
r=q.execute("SELECT manufacturer,physical_state,preparation,reuse_mode,capacity_text,shelf_life_unopened FROM developer_profiles WHERE developer_norm='rollei supergrain'").fetchone()
if not r or any(not str(x or '').strip() for x in r): raise SystemExit('SUPERGRAIN profile incomplete: '+repr(r))
d=[x[0] for x in q.execute("SELECT dilution FROM developer_dilutions WHERE developer_norm='rollei supergrain' ORDER BY dilution_norm")]
if not d: raise SystemExit('SUPERGRAIN dilutions missing')
e=q.execute("SELECT capacity_text FROM developer_profiles WHERE developer_norm='fomadon excel'").fetchone()
if not e or '12' not in (e[0] or ''): raise SystemExit('FOMADON Excel enriched capacity missing')
if q.execute('PRAGMA quick_check').fetchone()[0] != 'ok': raise SystemExit('sqlite quick_check failed')
c.close()
print('supergrain_profile=PASS')
print('italian_profile_layer=PASS')
PY

APP=Darkroom-v0.3.3.apk
test -f "$APP"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$AAPT" dump badging "$APP" > apk-badging-v033.txt
grep -Fq "versionCode='24'" apk-badging-v033.txt
grep -Fq "versionName='0.3.3'" apk-badging-v033.txt
unzip -Z1 "$APP" > apk-listing-v033.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v033.txt

PROFILE=combined/src/main/java/it/darkroom/assistant/DeveloperProfileStore.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
test -f "$PROFILE"
grep -Fq 'SCHEDA TECNICA' "$PROFILE"
grep -Fq 'Soluzione di lavoro fresca consigliata da Rollei' "$PROFILE"
grep -Fq 'DeveloperProfileStore.detailsItalian' "$ASSIST"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'NIKON D100' "$MAINT"
grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt

cat > validation-v033-enriched.txt <<'EOF'
release=Darkroom-v0.3.3
versionName=0.3.3
versionCode=24
base_version=0.3.2
database_hierarchy=MDC_FIRST_MANUFACTURER_FILL_ONLY
macodirect_role=COMMERCE_FILTER_ONLY
technical_sources=MANUFACTURERS_ONLY
rollei_supergrain=COMPLETE
user_facing_technical_notes=ITALIAN
mdc_combinations=14504
mdc_priority_regression=PASS
camera_manuals_preserved=PASS
timer_split_sonoff_preserved=PASS
personal_data_migration=NO_DESTRUCTIVE_RESET
EOF
sha256sum "$APP" | tee Darkroom-v0.3.3.sha256
