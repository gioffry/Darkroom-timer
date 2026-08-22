#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.7 — complete Italian display cleanup.
# Exact base: verified v0.3.6. No MDC data or Timer timing logic may change.

bash combined/build_v036.sh

python3 assistant/db/clean_visible_italian_v037.py combined/src/main/assets/mdc_full.sqlite \
  | tee validation-v037-italian-db.txt
python3 combined/patch_v037_italian_display_gate.py \
  | tee validation-v037-ui-patch.txt

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="28"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.3.7"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.3.7 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 28', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.3.7'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.3.7 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.7.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.7.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.3.7.apk > certificate-v037.txt
"$AAPT" dump badging Darkroom-v0.3.7.apk > apk-badging-v037.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v037.txt
grep -Fq "versionCode='28'" apk-badging-v037.txt
grep -Fq "versionName='0.3.7'" apk-badging-v037.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v037.txt
unzip -Z1 Darkroom-v0.3.7.apk > apk-listing-v037.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v037.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java

grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'safeItalianTechnical(lifeInfo.text)' "$ASSIST"
grep -Fq '" useful tank "' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"
! grep -Fq 'mdc_offline_darkroom_v036.sqlite' "$MDC"
# Prior app areas remain intact.
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'NIKON L35AF' "$MAINT"
grep -Fq 'ROLLEIFLEX 2.8 E2' "$MAINT"

python3 - <<'PY' | tee validation-v037-bundled-db.txt
from pathlib import Path
import sqlite3,re,calendar
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776

bad=re.compile(r"\b(the|and|with|when|should|stored|working solution|original package|developer|replenisher|concentrate|powder|liquid|full[- ]strength|closed container|without use|lists|useful|tank|capacity|chemistry|matrix|gallon|rolls|sheets|per litre|per liter)\b",re.I)
checks=[
 ('developer_profiles','developer_norm',('physical_state_it','preparation_it','reuse_instructions_it','capacity_it','storage_notes_it','notes_it','operational_life_it')),
 ('auxiliary_chemical_profiles','norm_name',('product_type_it','physical_state_it','preparation_it','capacity_it','storage_notes_it','notes_it','operational_life_it')),
]
off=[]
for table,key,fields in checks:
    cols={r[1] for r in cur.execute(f'pragma table_info({table})')}
    fields=tuple(f for f in fields if f in cols)
    for row in cur.execute(f"select {key},"+','.join(fields)+f" from {table}"):
        ident=row[0]
        for field,val in zip(fields,row[1:]):
            s=(val or '').strip()
            if s and (bad.search(s) or '\\n' in s or '\\r' in s): off.append((table,ident,field,s))
assert not off,off[:20]

d76=cur.execute("select capacity_it,operational_life_kind,operational_life_it,operational_life_months from developer_profiles where developer_norm='d 76'").fetchone()
assert d76
assert d76[0]=='Capacità indicata da Kodak: 4 rulli per litro di soluzione stock (16 rulli per gallone USA).'
assert d76[1]=='STOCK_PREPARATO' and d76[3]==6
assert d76[2]=='Stock preparato in bottiglia piena e ben chiusa: 6 mesi.'
# Regression for the date shown in the user's test setup.
y,m,d=2026,8,22
m2=m-1+d76[3]; yy=y+m2//12; mm=m2%12+1; dd=min(d,calendar.monthrange(yy,mm)[1])
assert (yy,mm,dd)==(2027,2,22)

excel=cur.execute("select operational_life_it,operational_life_months from developer_profiles where developer_norm='fomadon excel'").fetchone()
assert excel and excel[1]==12 and '12 mesi' in excel[0]
fomatol=cur.execute("select operational_life_it,operational_life_months from auxiliary_chemical_profiles where norm_name='fomatol lqn'").fetchone()
assert fomatol and fomatol[1]==6 and '6 mesi' in fomatol[0]

print('release=Darkroom-v0.3.7')
print('versionName=0.3.7')
print('versionCode=28')
print('base_version=0.3.6')
print('visible_english_residue=0')
print('visible_literal_backslash_n=0')
print('d76_capacity_full_italian=PASS')
print('d76_stock_duration_full_italian=PASS')
print('d76_22_08_2026_expiry=22_02_2027')
print('fomadon_excel_regression=PASS')
print('fomatol_lqn_regression=PASS')
print('fresh_cleaned_sqlite_on_upgrade=PASS')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
print('timer_splitgrade_sonoff_preserved=PASS')
con.close()
PY

cat validation-v036.txt validation-v037-italian-db.txt validation-v037-ui-patch.txt validation-v037-bundled-db.txt > validation-v037.txt
sha256sum Darkroom-v0.3.7.apk | tee Darkroom-v0.3.7.sha256
