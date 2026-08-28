#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.5 - Zone System field FAQ + Minolta Zone System FAQ + EV table.
# Exact base: verified v0.4.4. No changes to Timer, SONOFF, enlargement,
# chemistry, camera manuals, Rolleiflex accessories or prior technical content.

bash combined/build_v044.sh
python3 combined/patch_v045_zone_minolta_ev_faqs_r2.py | tee validation-v045-zone-minolta.txt

python3 - <<'PY'
from pathlib import Path
import re
p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="36"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.4.5"',s,count=1)
if n1!=1 or n2!=1: raise SystemExit('v0.4.5 manifest version update failed')
p.write_text(s,encoding='utf-8')
g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 36', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.5'", gs, count=1)
if n3!=1 or n4!=1: raise SystemExit('v0.4.5 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.5.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.5.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.5.apk > certificate-v045.txt
"$AAPT" dump badging Darkroom-v0.4.5.apk > apk-badging-v045.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v045.txt
grep -Fq "versionCode='36'" apk-badging-v045.txt
grep -Fq "versionName='0.4.5'" apk-badging-v045.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v045.txt
unzip -Z1 Darkroom-v0.4.5.apk > apk-listing-v045.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v045.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

# v0.4.5 acceptance.
grep -Fq 'Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?' "$MAINT"
grep -Fq '| 1/125 ★ | 9,9 | — | 11,0 | 11,9 | 13,0 | 13,9 | 15,0 | 15,9 |' "$MAINT"
grep -Fq '★ = Rolleiflex 2.8 E2' "$MAINT"
grep -Fq '● = Rolleiflex 3.5 Tessar MX' "$MAINT"
grep -Fq 'Gli EV dipendono esclusivamente dalla coppia tempo/diaframma e non dagli ISO.' "$MAINT"
grep -Fq 'HorizontalScrollView' "$MAINT"
grep -Fq 'Typeface.MONOSPACE' "$MAINT"
grep -Fq 'Come posso usare il Sistema Zonale con il Minolta Auto Meter III F?' "$MAINT"
grep -Fq 'Passa alla visualizzazione FNo..' "$MAINT"
grep -Fq 'togli sempre 2 stop rispetto alla lettura fornita dal Minolta.' "$MAINT"
grep -Fq 'Come utilizzo rapidamente il Sistema Zonale sul campo?' "$MAINT"
grep -Fq 'EV misurato + 2 = EV di esposizione' "$MAINT"
grep -Fq 'Zona III + 5 = Zona VIII' "$MAINT"
grep -Fq 'Misura l’ombra con dettaglio → togli 2 stop → scatta.' "$MAINT"
grep -Fq 'EV luce − EV ombra → ti dice quanto è contrastata la scena.' "$MAINT"

python3 - <<'PY' | tee validation-v045-faq-guard.txt
from pathlib import Path
import re
s=Path('combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
def block(a,b):
    x=s.index('private static final String[] '+a)
    y=s.index('private static final String[] '+b,x)
    return s[x:y]
def nstrings(x): return len(re.findall(r'"(?:\\.|[^"\\])*"',x))
qm=block('Q_MINOLTA','A_MINOLTA')
am=block('A_MINOLTA','Q_PROCESS_WASH')
qz=block('Q_ZONE','A_ZONE')
az=block('A_ZONE','Q_PRINT')
assert nstrings(qm)==12, nstrings(qm)
assert nstrings(am)==12, nstrings(am)
assert nstrings(qz)==11, nstrings(qz)
assert nstrings(az)==11, nstrings(az)
q1='Quali sono gli EV delle coppie tempo/diaframma delle mie Rolleiflex?'
q2='Come posso usare il Sistema Zonale con il Minolta Auto Meter III F?'
assert qm.index(q1) < qm.index(q2)
assert qz.index('Come utilizzo rapidamente il Sistema Zonale sul campo?') < qz.index('Cos’è il Sistema Zonale e a cosa serve?')
assert 'addFaqMatches(hits,"MINOLTA AUTO METER IIIF",Q_MINOLTA,A_MINOLTA,q);' in s
assert 'addFaqMatches(hits,"SISTEMA ZONALE",Q_ZONE,A_ZONE,q);' in s
print('minolta_faq_count=12')
print('minolta_ev_table_first=PASS')
print('minolta_zone_faq_second=PASS')
print('ev_table_horizontal_scroll=PASS')
print('zone_system_faq_count=11')
print('zone_field_faq_first=PASS')
print('global_search_new_faqs=PASS')
PY

# Prior validated areas must survive unchanged.
grep -Fq 'NIKON F100' "$MAINT"
grep -Fq 'NIKON L35AF2' "$MAINT"
grep -Fq 'FILTRI E ACCESSORI ROLLEIFLEX' "$MAINT"
grep -Fq 'Heidosmat-Rolleinar 1' "$MAINT"
grep -Fq 'Come si sostituisce correttamente la lampada della Meopta Color 3?' "$MAINT"
grep -Fq 'PROCESSO E LAVAGGIO' "$MAINT"
grep -Fq 'Cerca nelle FAQ…' "$MAINT"
grep -Fq 'ALTEZZA PIANO CARTA (spessore marginatore)' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$MAIN"
grep -Fq 'enlargementPaperPlaneHeightMm' "$ENL"
grep -Fq 'Math.pow((c.beta+1)/(b1+1),2)' "$ENL"
grep -Fq 'Math.round(ms/500.0)*500' "$ENL"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"

python3 - <<'PY' | tee validation-v045-bundled-db.txt
from pathlib import Path
import sqlite3
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0]=='ok'
assert cur.execute('select count(*) from times').fetchone()[0]==14504
assert cur.execute('select count(*) from films').fetchone()[0]==347
assert cur.execute('select count(*) from developers').fetchone()[0]==232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0]==776
print('release=Darkroom-v0.4.5')
print('versionName=0.4.5')
print('versionCode=36')
print('base_version=0.4.4')
print('change_scope=ZONE_SYSTEM_PLUS_MINOLTA_EV_FAQS')
print('minolta_faq_count=12')
print('zone_system_faq_count=11')
print('nikon_f100_unchanged=PASS')
print('nikon_l35af2_unchanged=PASS')
print('rolleiflex_accessories_unchanged=PASS')
print('color3_lamp_faq_unchanged=PASS')
print('process_wash_faq_unchanged=PASS')
print('global_faq_search_preserved=PASS')
print('paper_plane_logic_unchanged=PASS')
print('enlargement_exposure_formula_unchanged=PASS')
print('sonoff_final_step_seconds=0.5')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
con.close()
PY

cat validation-v044.txt validation-v045-zone-minolta.txt validation-v045-faq-guard.txt validation-v045-bundled-db.txt > validation-v045.txt
sha256sum Darkroom-v0.4.5.apk | tee Darkroom-v0.4.5.sha256
