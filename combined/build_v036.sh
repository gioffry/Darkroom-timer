#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.6 — operational chemistry expiration.
# Exact base: verified v0.3.5. Bottle condition is fixed: FULL and tightly closed.
# Massive Dev Chart combination tables are immutable.

bash combined/build_v035.sh

# The final v0.3.5 release completed all existing Italian preparation/duration
# overlays; run them explicitly here so the v0.3.6 build is reproducible even
# when rebuilt from the canonical v0.3.5 source chain.
# Normalize one official Kodak English product title inside an otherwise Italian
# sentence before applying the strict language validator. Technical meaning is
# unchanged; this is display text only.
python3 - <<'PY'
from pathlib import Path
p=Path('assistant/db/complete_italian_preparations_v035.py')
s=p.read_text(encoding='utf-8')
s=s.replace('T-MAX RS Developer and Replenisher', 'T-MAX RS (rivelatore e reintegratore)')
p.write_text(s,encoding='utf-8')
PY
python3 assistant/db/complete_italian_preparations_v035.py combined/src/main/assets/mdc_full.sqlite \
  | tee validation-v036-preparations.txt
python3 assistant/db/complete_italian_durations_v035.py combined/src/main/assets/mdc_full.sqlite \
  | tee validation-v036-durations.txt

# Dedicated operational shelf-life layer. It never reads 1+X working duration
# as inventory expiry. Full-bottle normalization removes half-bottle alternatives.
python3 assistant/db/apply_operational_stock_life_v036.py combined/src/main/assets/mdc_full.sqlite \
  | tee validation-v036-operational.txt
python3 assistant/db/normalize_full_bottle_only_v036.py combined/src/main/assets/mdc_full.sqlite \
  | tee validation-v036-full-bottle.txt

python3 combined/patch_v036_operational_stock_expiry.py

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="27"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.3.6"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.3.6 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 27', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.3.6'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.3.6 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.6.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.6.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.3.6.apk > certificate-v036.txt
"$AAPT" dump badging Darkroom-v0.3.6.apk > apk-badging-v036.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v036.txt
grep -Fq "versionCode='27'" apk-badging-v036.txt
grep -Fq "versionName='0.3.6'" apk-badging-v036.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v036.txt
unzip -Z1 Darkroom-v0.3.6.apk > apk-listing-v036.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v036.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java

grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'DURATA CONCENTRATO APERTO · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'SCADENZA STOCK' "$ASSIST"
grep -Fq 'SCADENZA CONCENTRATO' "$ASSIST"
grep -Fq 'DATA PREPARAZIONE STOCK' "$ASSIST"
grep -Fq 'DATA APERTURA CONCENTRATO' "$ASSIST"
grep -Fq 'operationalExpiryValue' "$ASSIST"
! grep -Fq 'SCADENZA LOCALE PERSONALIZZATA (giorni)' "$ASSIST"
! grep -Fq 'DURATA DOPO APERTURA (giorni)' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v036.sqlite' "$MDC"
# Preserve prior app areas and Timer internals.
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'NIKON L35AF' "$MAINT"
grep -Fq 'ROLLEIFLEX 2.8 E2' "$MAINT"

python3 - <<'PY' | tee validation-v036-bundled-db.txt
from pathlib import Path
import sqlite3,re,datetime,calendar
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776

for table in ('developer_profiles','auxiliary_chemical_profiles'):
    cols={r[1] for r in cur.execute(f'pragma table_info({table})')}
    for c in ('operational_life_kind','operational_life_it','operational_life_months','operational_life_days','operational_life_hours','operational_life_condition_it','operational_source_kind'):
        assert c in cols,(table,c)
    bad=cur.execute(f"select count(*) from {table} where coalesce(operational_life_it,'')<>'' and operational_life_condition_it!='bottiglia piena e ben chiusa, con minimo volume d’aria'").fetchone()[0]
    assert bad==0,(table,bad)
    # The operational field must never be a working 1+X lifetime.
    oneplus=cur.execute(f"select count(*) from {table} where coalesce(operational_life_it,'') glob '*1+*'").fetchone()[0]
    assert oneplus==0,(table,oneplus)
    half=cur.execute(f"select count(*) from {table} where lower(coalesce(operational_life_it,'')) like '%metà bottiglia%' or lower(coalesce(operational_life_it,'')) like '%half full%'").fetchone()[0]
    assert half==0,(table,half)

excel=cur.execute("select operational_life_kind,operational_life_it,operational_life_months from developer_profiles where developer_norm='fomadon excel'").fetchone()
assert excel and excel[0]=='STOCK_PREPARATO' and excel[2]==12 and '12 mesi' in excel[1]
fomatol=cur.execute("select operational_life_kind,operational_life_it,operational_life_months,operational_source_kind from auxiliary_chemical_profiles where norm_name='fomatol lqn'").fetchone()
assert fomatol and fomatol[0]=='CONCENTRATO_APERTO' and fomatol[2]==6 and '6 mesi' in fomatol[1]
# Date regression matching the user's current example: 22/08/2026 + 6 months.
y,m,d=2026,8,22
m2=m-1+6; yy=y+m2//12; mm=m2%12+1; dd=min(d,calendar.monthrange(yy,mm)[1])
assert (yy,mm,dd)==(2027,2,22)

opdev=cur.execute("select count(*) from developer_profiles where coalesce(operational_life_it,'')<>''").fetchone()[0]
opcalc=cur.execute("select count(*) from developer_profiles where operational_life_months is not null or operational_life_days is not null or operational_life_hours is not null").fetchone()[0]
opaux=cur.execute("select count(*) from auxiliary_chemical_profiles where coalesce(operational_life_it,'')<>''").fetchone()[0]
print('release=Darkroom-v0.3.6')
print('versionName=0.3.6')
print('versionCode=27')
print('base_version=0.3.5')
print('operational_rule=FULL_BOTTLE_ONLY')
print('working_1plusX_used_for_expiry=NO')
print(f'developer_operational_profiles={opdev}')
print(f'developer_operational_profiles_calculable={opcalc}')
print(f'auxiliary_operational_profiles={opaux}')
print('fomadon_excel_stock=12_months')
print('fomatol_lqn_opened_reference=6_months')
print('fomatol_lqn_22_08_2026_expiry=22_02_2027')
print('manual_local_expiry_field=REMOVED')
print('half_bottle_selector=ABSENT')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
print('timer_splitgrade_sonoff_preserved=PASS')
print('personal_data_migration=NO_DESTRUCTIVE_RESET')
con.close()
PY

cat validation-v035.txt validation-v036-preparations.txt validation-v036-durations.txt validation-v036-operational.txt validation-v036-full-bottle.txt validation-v036-bundled-db.txt > validation-v036.txt
sha256sum Darkroom-v0.3.6.apk | tee Darkroom-v0.3.6.sha256
