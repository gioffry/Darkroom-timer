#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.5.8 - exact MDC match first, then an audited one-hop equivalent.
# All lookups remain inside the bundled SQLite snapshot.

bash combined/build_v057.sh
python3 combined/patch_v058_offline_equivalents.py \
  | tee validation-v058-equivalence-source.txt

python3 - <<'PY'
from pathlib import Path
import re

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="49"', text, count=1)
text, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.5.8"', text, count=1)
if n1 != 1 or n2 != 1: raise SystemExit('v0.5.8 manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle_file = Path('combined/build.gradle')
text = gradle_file.read_text(encoding='utf-8')
text, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 49', text, count=1)
text, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.5.8'", text, count=1)
if n3 != 1 or n4 != 1: raise SystemExit('v0.5.8 Gradle version update failed')
gradle_file.write_text(text, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.8.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.8.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.8.apk > certificate-v058.txt
"$AAPT" dump badging Darkroom-v0.5.8.apk > apk-badging-v058.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v058.txt
grep -Fq "versionCode='49'" apk-badging-v058.txt
grep -Fq "versionName='0.5.8'" apk-badging-v058.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v058.txt
unzip -Z1 Darkroom-v0.5.8.apk > apk-listing-v058.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v058.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
grep -Fq 'mdc_offline_darkroom_v058.sqlite' "$MDC"
grep -Fq 'if (exact != null) return exact;' "$MDC"
grep -Fq 'developer_time_equivalents' "$MDC"
grep -Fq 'EQUIVALENZA CONTROLLATA' "$ASSIST"
! grep -Fq 'MdcOfflineStore.syncAsync' "$ASSIST"

python3 - <<'PY' | tee validation-v058.txt
from pathlib import Path
import re
import sqlite3
import unicodedata


def norm(value):
    value = unicodedata.normalize('NFD', value or '').lower().replace('-', ' ')
    value = ''.join(c for c in value if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9+]+', ' ', value)).strip()


db = sqlite3.connect(Path('combined/src/main/assets/mdc_full.sqlite'))
db.row_factory = sqlite3.Row
assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert db.execute('SELECT COUNT(*) FROM developer_time_equivalents').fetchone()[0] == 39
assert db.execute(
    'SELECT COUNT(DISTINCT selected_developer_norm) FROM developer_time_equivalents'
).fetchone()[0] == 12
assert db.execute(
    "SELECT COUNT(*) FROM developer_time_equivalents WHERE evidence_kind<>'AUDITED_DIRECT_ONE_HOP'"
).fetchone()[0] == 0


def exact(film, developer, dilution, iso=100, temp=20):
    return db.execute(
        '''SELECT film,developer,dilution,iso,time35,time120,timesheet,temp,source_url
           FROM times WHERE film_norm=? AND developer_norm=? AND dilution_norm=?
             AND iso=? AND temp=? ORDER BY id''',
        (norm(film), norm(developer), norm(dilution), iso, temp),
    ).fetchall()


def resolve(film, developer, dilution, iso=100, temp=20):
    rows = exact(film, developer, dilution, iso, temp)
    if rows:
        return 'EXACT', rows
    mappings = db.execute(
        '''SELECT source_developer,source_dilution FROM developer_time_equivalents
           WHERE selected_developer_norm=? AND selected_dilution_norm=?''',
        (norm(developer), norm(dilution)),
    ).fetchall()
    if len(mappings) != 1:
        return 'NONE', []
    mapping = mappings[0]
    rows = exact(film, mapping['source_developer'], mapping['source_dilution'], iso, temp)
    return ('EQUIVALENT', rows) if rows else ('NONE', [])


# Reported missing-time regression: no Excel row exists, but the single approved
# Xtol fallback supplies the MDC 10-minute base time. The app applies JOBO 0.85.
kind, rows = resolve('Kentmere 100', 'Fomadon Excel', '1+1')
assert kind == 'EQUIVALENT' and len(rows) == 1, (kind, [dict(r) for r in rows])
assert rows[0]['developer'] == 'Xtol'
assert (rows[0]['time35'], rows[0]['time120']) == ('10', '10')
assert round(10 * 60 * 0.85 / 5) * 5 == 510

# Exact data always wins even when a fallback mapping exists.
kind, rows = resolve('Fomapan 100', 'Fomadon Excel', '1+1')
assert kind == 'EXACT', kind
assert rows[0]['developer'] == 'Fomadon Excel'
assert rows[0]['time35'] == '8-9'

# Deliberately excluded: no inferred family match and no unresolved dilution map.
for developer in ('Bellini B&W Ecofilm', 'Fomadon LQR'):
    assert db.execute(
        'SELECT COUNT(*) FROM developer_time_equivalents WHERE selected_developer_norm=?',
        (norm(developer),),
    ).fetchone()[0] == 0

# Every selectable target is a currently scoped Maco developer; sources may use
# the wider MDC pool. No target+dilution can point to more than one source.
assert db.execute(
    '''SELECT COUNT(*) FROM developer_time_equivalents e
       LEFT JOIN maco_developer_scope m
         ON m.developer_norm=e.selected_developer_norm
       WHERE m.developer_norm IS NULL'''
).fetchone()[0] == 0
assert db.execute(
    '''SELECT COUNT(*) FROM (
           SELECT selected_developer_norm,selected_dilution_norm,COUNT(*) n
           FROM developer_time_equivalents
           GROUP BY selected_developer_norm,selected_dilution_norm HAVING n<>1
       )'''
).fetchone()[0] == 0
assert db.execute('SELECT COUNT(*) FROM times').fetchone()[0] >= 14500
assert db.execute('SELECT COUNT(*) FROM maco_developer_scope').fetchone()[0] == 37
db.close()

print('release=Darkroom-v0.5.8')
print('versionName=0.5.8')
print('versionCode=49')
print('runtime_network_for_mdc=DISABLED')
print('selection_scope=MACO_DIRECT_37')
print('equivalence_source_pool=MDC_FULL_OFFLINE')
print('equivalence_rules=39')
print('equivalence_targets=12')
print('lookup_order=EXACT_THEN_ONE_HOP')
print('fuzzy_equivalence=DISABLED')
print('transitive_equivalence=DISABLED')
print('kentmere100_excel_1+1_source=XTOL_10MIN')
print('kentmere100_excel_1+1_jobo=8MIN30S')
print('fomapan100_excel_1+1_source=EXACT_8_TO_9MIN')
print('database_integrity=PASS')
PY

sha256sum Darkroom-v0.5.8.apk | tee Darkroom-v0.5.8.sha256
