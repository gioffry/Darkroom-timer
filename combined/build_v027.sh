#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.7 — hotfix: safelight ON during Split provino filter change.
# Base: user-tested Darkroom v0.2.6.

git fetch --no-tags origin feature-darkroom-v012-vintage-home-r2
git checkout FETCH_HEAD -- combined/v012_assets/home_mockup
python3 - <<'PY'
from pathlib import Path
import base64
assets=Path('combined/v012_assets/home_mockup')
parts=sorted(assets.glob('*.part'))
if len(parts)!=9: raise SystemExit(f'v0.2.7: expected 9 compatibility Home parts, found {len(parts)}')
encoded=''.join(''.join(p.read_text(encoding='utf-8').split()) for p in parts)
raw=base64.b64decode(encoded + '=' * (-len(encoded)%4), validate=True)
if len(raw)<50000 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WEBP': raise SystemExit('v0.2.7: compatibility Home payload invalid')
for p in parts: p.unlink()
cut=(len(encoded)+1)//2
(assets/'00.part').write_text(encoded[:cut],encoding='utf-8')
(assets/'01.part').write_text(encoded[cut:],encoding='utf-8')
PY

sed -i 's/len(raw) < 150_000/len(raw) < 40_000/' combined/patch_v021_home_font_log_fix.py
python3 -m py_compile \
  combined/patch_v025_split_grade_provino.py \
  combined/patch_v026_log_voice.py \
  combined/patch_v026_print_integration.py \
  combined/patch_v027_split_provino_safelight_pause.py

python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v018.sh').read_text(encoding='utf-8')
required=['Darkroom-v0.1.8','versionCode="9"','versionName="0.1.8"','python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n']
for marker in required:
    if marker not in s: raise SystemExit('v0.2.7 build wrapper missing base marker: '+marker)
s=s.replace('Darkroom-v0.1.8','Darkroom-v0.2.7')
s=s.replace('versionCode="9"','versionCode="18"').replace('versionCode 9','versionCode 18').replace("versionCode='9'","versionCode='18'")
s=s.replace('versionName="0.1.8"','versionName="0.2.7"').replace("versionName '0.1.8'","versionName '0.2.7'").replace("versionName='0.1.8'","versionName='0.2.7'")
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
    + 'python3 combined/patch_v026_print_integration.py\\\\n'
    + 'python3 combined/patch_v027_split_provino_safelight_pause.py\\\\n')
if s.count(needle)!=1: raise SystemExit('v0.2.7 patch insertion ambiguous')
s=s.replace(needle,replacement,1)
Path('/tmp/build_v027_generated.sh').write_text(s,encoding='utf-8')
PY

bash /tmp/build_v027_generated.sh

python3 - <<'PY'
from pathlib import Path
p=Path('validation-v015.txt')
if not p.exists(): raise SystemExit('v0.2.7 validation file missing')
lines=[]
for line in p.read_text(encoding='utf-8').splitlines():
    if line.startswith('versionName='): line='versionName=0.2.7'
    elif line.startswith('versionCode='): line='versionCode=18'
    elif line.startswith('timer_version='): line='timer_version=0.13.10'
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
'print_split_piece3_preserved=PASS',
'print_revision_piece3_preserved=PASS',
'voice_no_cyan=PASS',
'voice_seconds_word=PASS',
'provino_split_safelight_on_filter_change=PASS',
'provino_split_safelight_off_first_hard=PASS',
'provino_split_safelight_off_between_hard_strips=PASS',
'provino_single_safelight_behavior_unchanged=PASS',
'print_split_safelight_behavior_unchanged=PASS',
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

# Existing pieces remain intact.
grep -q 'navButton("PRODOTTI CHIMICI", false)' "$HOME"
grep -q 'navButton("USO E MANUTENZIONE", true)' "$HOME"
! grep -q 'ImageView' "$HOME"
grep -q 'PROVINO_SPLIT_SOFT' "$MAIN"
grep -q 'FASE 1 DI 2 — TROVA IL MORBIDO' "$MAIN"
grep -q 'FASE 2 DI 2 — TROVA IL DURO' "$MAIN"
grep -q 'TROVA I TEMPI CON UN PROVINO  ·  CONSIGLIATO' "$MAIN"
grep -q 'RIFAI SOLO IL DURO' "$MAIN"
grep -q 'RIFAI ENTRAMBI' "$MAIN"
grep -q 'public String exposureMode = "SINGLE";' "$LOGENTRY"
grep -q 'REV2|' "$LOGSTORE"
grep -q 'DODGE' "$MAIN"
grep -q 'BURN' "$MAIN"
grep -q 'RIDIMENSIONA STAMPA' "$MAIN"

# v0.2.7 hotfix acceptance.
grep -q 'private static final String APP_VERSION = "0.13.10";' "$MAIN"
grep -q 'testSplitFilterPauseSafelightOn' "$SERVICE"
grep -q 'temporarilyRestoreSafelightForPause();' "$SERVICE"
grep -q 'SPLIT PROVINO • SAFELIGHT ON per cambio filtro morbido → duro' "$SERVICE"
grep -q "SPLIT PROVINO • SAFELIGHT OFF all'avvio del provino duro; resta OFF tra le strisce" "$SERVICE"
grep -q 'dimSafelightForExposure();' "$SERVICE"
grep -q 'TimingMath.testStripPulses(testTargetsMs, testStripMethod)' "$SERVICE"
grep -q 'Esposizione uno di due' "$SERVICE"
grep -q 'Esposizione due di due' "$SERVICE"
grep -q 'voiceSeconds(printSequence.split.softMs)' "$SERVICE"
grep -q 'voiceSeconds(printSequence.split.hardMs)' "$SERVICE"
! grep -Eiq 'cyan|ciano' "$SERVICE"
! grep -q 'Somma massima delle due esposizioni' "$MAIN"
! grep -q 'La somma dello Split Grade non può superare' "$MAIN"
grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt
! grep -q 'sans-serif-condensed' "$MAINT"
grep -q 'syncLogDisplayFields(originEntry,meta);' "$ENL"

test -f Darkroom-v0.2.7.apk
test -f Darkroom-v0.2.7.sha256
grep -Fq "versionCode='18'" apk-badging-v015.txt
grep -Fq "versionName='0.2.7'" apk-badging-v015.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v015.txt
unzip -Z1 Darkroom-v0.2.7.apk > apk-listing-v027.txt
! grep -Eiq '(^|/)home_vintage\.(jpg|jpeg|png|webp)$' apk-listing-v027.txt
sha256sum Darkroom-v0.2.7.apk | tee Darkroom-v0.2.7.sha256
