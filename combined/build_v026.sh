#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.6 — Piece 3: STAMPA Split Grade + voice + revision LOG.
# Base: user-tested Darkroom v0.2.5.

git fetch --no-tags origin feature-darkroom-v012-vintage-home-r2
git checkout FETCH_HEAD -- combined/v012_assets/home_mockup
python3 - <<'PY'
from pathlib import Path
import base64
assets=Path('combined/v012_assets/home_mockup')
parts=sorted(assets.glob('*.part'))
if len(parts)!=9: raise SystemExit(f'v0.2.6: expected 9 compatibility Home parts, found {len(parts)}')
encoded=''.join(''.join(p.read_text(encoding='utf-8').split()) for p in parts)
raw=base64.b64decode(encoded + '=' * (-len(encoded)%4), validate=True)
if len(raw)<50000 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WEBP': raise SystemExit('v0.2.6: compatibility Home payload invalid')
for p in parts: p.unlink()
cut=(len(encoded)+1)//2
(assets/'00.part').write_text(encoded[:cut],encoding='utf-8')
(assets/'01.part').write_text(encoded[cut:],encoding='utf-8')
PY

sed -i 's/len(raw) < 150_000/len(raw) < 40_000/' combined/patch_v021_home_font_log_fix.py
python3 -m py_compile combined/patch_v025_split_grade_provino.py combined/patch_v026_log_voice.py combined/patch_v026_print_integration.py

python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v018.sh').read_text(encoding='utf-8')
required=['Darkroom-v0.1.8','versionCode="9"','versionName="0.1.8"','python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n']
for marker in required:
    if marker not in s: raise SystemExit('v0.2.6 build wrapper missing base marker: '+marker)
s=s.replace('Darkroom-v0.1.8','Darkroom-v0.2.6')
s=s.replace('versionCode="9"','versionCode="17"').replace('versionCode 9','versionCode 17').replace("versionCode='9'","versionCode='17'")
s=s.replace('versionName="0.1.8"','versionName="0.2.6"').replace("versionName '0.1.8'","versionName '0.2.6'").replace("versionName='0.1.8'","versionName='0.2.6'")
needle='python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n'
replacement=(needle
    + 'python3 combined/patch_v019_use_maintenance.py\\\\n'
    + 'python3 combined/patch_v020_enlargement_log_flow.py\\\\n'
    + 'python3 combined/patch_v020_enlargement_legacy_recipe.py\\\\n'
    + 'python3 combined/patch_v020_visual_coherence.py\\\\n'
    + 'python3 combined/patch_v021_home_font_log_fix.py\\\\n'
    + 'python3 combined/patch_v024_home_safe_buttons.py\\\\n'
    + 'python3 combined/patch_v025_split_grade_provino.py\\\\n'
    + 'python3 combined/patch_v026_log_voice.py\\\\n'
    + 'python3 combined/patch_v026_print_integration.py\\\\n')
if s.count(needle)!=1: raise SystemExit('v0.2.6 patch insertion ambiguous')
s=s.replace(needle,replacement,1)
Path('/tmp/build_v026_generated.sh').write_text(s,encoding='utf-8')
PY

bash /tmp/build_v026_generated.sh

python3 - <<'PY'
from pathlib import Path
p=Path('validation-v015.txt')
if not p.exists(): raise SystemExit('v0.2.6 validation file missing')
lines=[]
for line in p.read_text(encoding='utf-8').splitlines():
    if line.startswith('versionName='): line='versionName=0.2.6'
    elif line.startswith('versionCode='): line='versionCode=17'
    elif line.startswith('timer_version='): line='timer_version=0.13.9'
    elif line=='build=SUCCESS': continue
    elif line=='timer_runtime_logic_unchanged=PASS': continue
    if line.startswith('home_mockup_approved=') or line.startswith('home_asset_') or line.startswith('home_source_full_decode=') or line.startswith('home_packaged_full_decode=') or line.startswith('home_black_screen_fix=') or line.startswith('home_no_duplicate_maintenance_overlay='):
        continue
    lines.append(line)
extras=[
'home_mode=native_buttons',
'home_artwork_dependency=NONE',
'home_five_visible_buttons=PASS',
'provino_split_piece2_preserved=PASS',
'print_plan_single_split_one_popup=PASS',
'print_split_no_50_50_conversion=PASS',
'print_split_no_sum_constraint=PASS',
'print_split_guided_or_manual=PASS',
'print_retest_single=PASS',
'print_retest_split_hard_only=PASS',
'print_retest_split_both=PASS',
'print_revision_non_destructive_navigation=PASS',
'print_revision_previous_snapshot=PASS',
'log_split_four_fields=PASS',
'log_split_chosen_strips_origin=PASS',
'log_revision_backward_compatible=PASS',
'voice_split_exposure_one_two=PASS',
'voice_zero_previous_filter=PASS',
'voice_no_cyan=PASS',
'voice_seconds_word=PASS',
'dodge_burn_local_only=PASS',
'color3_frozen=PASS',
'sonoff_rounding_500ms=PASS',
'build=SUCCESS']
for x in extras:
    if x not in lines: lines.append(x)
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
PY

HOME=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
SERVICE=combined/src/main/java/it/darkroom/timer/SonoffArmService.java
LOGENTRY=combined/src/main/java/it/darkroom/timer/LogEntry.java
LOGSTORE=combined/src/main/java/it/darkroom/timer/LogStore.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java

# Piece 1 and Piece 2 remain intact.
grep -q 'navButton("PRODOTTI CHIMICI", false)' "$HOME"
grep -q 'navButton("USO E MANUTENZIONE", true)' "$HOME"
! grep -q 'ImageView' "$HOME"
grep -q 'PROVINO_SPLIT_SOFT' "$MAIN"
grep -q 'FASE 1 DI 2 — TROVA IL MORBIDO' "$MAIN"
grep -q 'FASE 2 DI 2 — TROVA IL DURO' "$MAIN"
grep -q 'CREA STAMPA SPLIT GRADE' "$MAIN"
grep -q 'EXTRA_TEST_PRE_EXPOSURE_MS' "$SERVICE"

# Piece 3 — PIANO STAMPA and navigation.
grep -q 'private static final String APP_VERSION = "0.13.9";' "$MAIN"
grep -q 'TROVA I TEMPI CON UN PROVINO  ·  CONSIGLIATO' "$MAIN"
grep -q 'INSERISCI TEMPI GIÀ NOTI' "$MAIN"
grep -q 'RIFAI PROVINO SINGOLO' "$MAIN"
grep -q 'RIFAI SOLO IL DURO' "$MAIN"
grep -q 'RIFAI ENTRAMBI' "$MAIN"
grep -q 'CORREZIONI LOCALI' "$MAIN"
grep -q 'Morbido e duro sono due esposizioni consecutive. Non impostare Y e M contemporaneamente.' "$MAIN"
! grep -q 'PASSA A SPLIT GRADE' "$MAIN"
! grep -q 'Somma massima delle due esposizioni' "$MAIN"
! grep -q 'La somma dello Split Grade non può superare' "$MAIN"
! grep -q 'int softUnits =' "$MAIN"
! grep -Eiq 'color[ _-]?3' "$MAIN"

# Voice exactness: current filter is stated, previous one is zeroed, no cyan, full word secondi.
grep -q 'Esposizione uno di due' "$SERVICE"
grep -q 'Esposizione due di due' "$SERVICE"
grep -q 'Azzera il magenta' "$SERVICE"
grep -q 'Azzera il giallo' "$SERVICE"
grep -q 'voiceSeconds(printSequence.split.softMs)' "$SERVICE"
grep -q 'voiceSeconds(printSequence.split.hardMs)' "$SERVICE"
! grep -Eiq 'cyan|ciano' "$SERVICE"

# Revision/log explicit fields and old-log compatible tagged extension.
grep -q 'public String exposureMode = "SINGLE";' "$LOGENTRY"
grep -q 'public int splitSoftMs = 0;' "$LOGENTRY"
grep -q 'public int splitHardMs = 0;' "$LOGENTRY"
grep -q 'public long previousRevisionId = 0L;' "$LOGENTRY"
grep -q 'REV2|' "$LOGSTORE"
grep -q 'lastSplitSoftYellow' "$SERVICE"
grep -q 'lastSplitHardMs' "$SERVICE"
grep -q 'MOSTRA REVISIONE PRECEDENTE' "$MAIN"
grep -q 'commitPrintRevisionMetadata("PROVINO")' "$MAIN"
grep -q 'commitPrintRevisionMetadata("MANUALE")' "$MAIN"

# Existing unrelated approved functions remain present.
grep -q 'DODGE' "$MAIN"
grep -q 'BURN' "$MAIN"
grep -q 'ALLUNGA TEMPI' "$MAIN"
grep -q 'CORREZIONE GLOBALE' "$MAIN"
grep -q 'RIDIMENSIONA STAMPA' "$MAIN"
! grep -q 'sans-serif-condensed' "$MAINT"
grep -q 'syncLogDisplayFields(originEntry,meta);' "$ENL"
grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt

test -f Darkroom-v0.2.6.apk
test -f Darkroom-v0.2.6.sha256
grep -Fq "versionCode='17'" apk-badging-v015.txt
grep -Fq "versionName='0.2.6'" apk-badging-v015.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v015.txt
unzip -Z1 Darkroom-v0.2.6.apk > apk-listing-v026.txt
! grep -Eiq '(^|/)home_vintage\.(jpg|jpeg|png|webp)$' apk-listing-v026.txt
sha256sum Darkroom-v0.2.6.apk | tee Darkroom-v0.2.6.sha256
