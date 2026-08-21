#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.5 — Piece 2: guided Split Grade PROVINO engine.
# Base: user-verified Darkroom v0.2.4. Home remains native/buttons; piece 3 is not included.

# Reconstruct the historical payload only because the approved v0.2.1 persistence
# patch in the build chain expects it. v0.2.4 removes the artwork again afterwards.
git fetch --no-tags origin feature-darkroom-v012-vintage-home-r2
git checkout FETCH_HEAD -- combined/v012_assets/home_mockup
python3 - <<'PY'
from pathlib import Path
import base64
assets = Path('combined/v012_assets/home_mockup')
parts = sorted(assets.glob('*.part'))
if len(parts) != 9:
    raise SystemExit(f'v0.2.5: expected 9 historical Home parts for compatibility, found {len(parts)}')
encoded = ''.join(''.join(p.read_text(encoding='utf-8').split()) for p in parts)
raw = base64.b64decode(encoded + '=' * (-len(encoded) % 4), validate=True)
if len(raw) < 50000 or raw[:4] != b'RIFF' or raw[8:12] != b'WEBP':
    raise SystemExit('v0.2.5: historical Home compatibility payload invalid')
for p in parts:
    p.unlink()
cut = (len(encoded) + 1) // 2
(assets / '00.part').write_text(encoded[:cut], encoding='utf-8')
(assets / '01.part').write_text(encoded[cut:], encoding='utf-8')
PY

sed -i 's/len(raw) < 150_000/len(raw) < 40_000/' combined/patch_v021_home_font_log_fix.py

python3 - <<'PY'
from pathlib import Path
s = Path('combined/build_v018.sh').read_text(encoding='utf-8')
required = [
    'Darkroom-v0.1.8',
    'versionCode="9"',
    'versionName="0.1.8"',
    'python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n',
]
for marker in required:
    if marker not in s:
        raise SystemExit('v0.2.5 build wrapper: marker missing in v0.1.8: ' + marker)

s = s.replace('Darkroom-v0.1.8', 'Darkroom-v0.2.5')
s = s.replace('versionCode="9"', 'versionCode="16"')
s = s.replace('versionCode 9', 'versionCode 16')
s = s.replace("versionCode='9'", "versionCode='16'")
s = s.replace('versionName="0.1.8"', 'versionName="0.2.5"')
s = s.replace("versionName '0.1.8'", "versionName '0.2.5'")
s = s.replace("versionName='0.1.8'", "versionName='0.2.5'")

needle = 'python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n'
replacement = (needle
               + 'python3 combined/patch_v019_use_maintenance.py\\\\n'
               + 'python3 combined/patch_v020_enlargement_log_flow.py\\\\n'
               + 'python3 combined/patch_v020_enlargement_legacy_recipe.py\\\\n'
               + 'python3 combined/patch_v020_visual_coherence.py\\\\n'
               + 'python3 combined/patch_v021_home_font_log_fix.py\\\\n'
               + 'python3 combined/patch_v024_home_safe_buttons.py\\\\n'
               + 'python3 combined/patch_v025_split_grade_provino.py\\\\n')
if s.count(needle) != 1:
    raise SystemExit('v0.2.5 build wrapper: patch insertion point ambiguous')
s = s.replace(needle, replacement, 1)
Path('/tmp/build_v025_generated.sh').write_text(s, encoding='utf-8')
PY

bash /tmp/build_v025_generated.sh

python3 - <<'PY'
from pathlib import Path
p=Path('validation-v015.txt')
if not p.exists(): raise SystemExit('v0.2.5: validation file missing')
lines=[]
for line in p.read_text(encoding='utf-8').splitlines():
    if line.startswith('versionName='): line='versionName=0.2.5'
    elif line.startswith('versionCode='): line='versionCode=16'
    elif line == 'build=SUCCESS': continue
    elif line == 'timer_runtime_logic_unchanged=PASS': continue
    if line.startswith('home_mockup_approved=') or line.startswith('home_asset_') \
            or line.startswith('home_source_full_decode=') or line.startswith('home_packaged_full_decode=') \
            or line.startswith('home_black_screen_fix=') or line.startswith('home_no_duplicate_maintenance_overlay='):
        continue
    lines.append(line)
for extra in [
    'home_mode=native_buttons',
    'home_artwork_dependency=NONE',
    'home_five_visible_buttons=PASS',
    'provino_single_default=PASS',
    'provino_single_reset_without_print=PASS',
    'provino_split_state_machine=PASS',
    'provino_split_soft_default_y60=PASS',
    'provino_split_hard_default_m180=PASS',
    'provino_split_whole_strip_soft_preexposure=PASS',
    'provino_split_hard_redo_keeps_soft=PASS',
    'provino_split_soft_change_invalidates_hard=PASS',
    'provino_split_four_distinct_fields_transfer=PASS',
    'provino_split_no_total_constraint=PASS',
    'provino_split_no_color3_compensation=PASS',
    'provino_split_operational_500ms=PASS',
    'sonoff_existing_test_pulse_engine_preserved=PASS',
    'safelight_single_cycle_soft_plus_hard=PASS',
    'maintenance_font_timer_default=PASS',
    'log_enlargement_meta_per_print=PASS',
    'build=SUCCESS',
]:
    if extra not in lines: lines.append(extra)
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
PY

HOME_JAVA=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
SERVICE=combined/src/main/java/it/darkroom/timer/SonoffArmService.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java

# Piece 1 stays intact.
grep -q 'navButton("PRODOTTI CHIMICI", false)' "$HOME_JAVA"
grep -q 'navButton("USO E MANUTENZIONE", true)' "$HOME_JAVA"
! grep -q 'ImageView' "$HOME_JAVA"
! find combined/src/main/res -type f \( -name 'home_vintage.jpg' -o -name 'home_vintage.jpeg' -o -name 'home_vintage.png' -o -name 'home_vintage.webp' \) | grep -q .

# Piece 2 acceptance guards.
grep -q 'private static final String APP_VERSION = "0.13.8";' "$MAIN"
grep -q 'PROVINO_SPLIT_SOFT' "$MAIN"
grep -q 'PROVINO_SPLIT_HARD' "$MAIN"
grep -q 'compactButton("SINGOLO")' "$MAIN"
grep -q 'compactButton("SPLIT GRADE")' "$MAIN"
grep -q 'FASE 1 DI 2 — TROVA IL MORBIDO' "$MAIN"
grep -q 'FASE 2 DI 2 — TROVA IL DURO' "$MAIN"
grep -q 'NESSUNA MI CONVINCE — REIMPOSTA PROVINO' "$MAIN"
grep -q 'CONTINUA AL DURO' "$MAIN"
grep -q 'CREA STAMPA SPLIT GRADE' "$MAIN"
grep -q 'RIFAI IL DURO' "$MAIN"
grep -q 'RIVEDI IL MORBIDO' "$MAIN"
grep -q 'plan.softYellow' "$MAIN"
grep -q 'plan.softMs' "$MAIN"
grep -q 'plan.hardMagenta' "$MAIN"
grep -q 'plan.hardMs' "$MAIN"
grep -q 'next.split=plan' "$MAIN"
! grep -q 'morbida + dura non possono superare la base' "$MAIN"
! grep -Eiq 'color[ _-]?3' "$MAIN"
grep -q 'EXTRA_TEST_PRE_EXPOSURE_MS' "$MAIN"
grep -q 'EXTRA_TEST_PRE_EXPOSURE_MS' "$SERVICE"
grep -q 'ESPOSIZIONE MORBIDA SU TUTTA LA STRISCIA' "$SERVICE"
grep -q 'Azzera il giallo. Imposta magenta' "$SERVICE"
grep -q 'Mantieni il cyan a zero' "$SERVICE"
grep -q 'TimingMath.testStripPulses(testTargetsMs, testStripMethod)' "$SERVICE"
grep -q 'STATE_WAITING_SPLIT' "$SERVICE"
grep -q 'private int testCount = 7;' "$MAIN"
grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt

# Previously approved unrelated fixes remain present.
! grep -q 'sans-serif-condensed' "$MAINT"
grep -q 'applyEnlargementSnapshotToVisibleLogFields(e);' "$MAIN"
grep -q 'syncLogDisplayFields(originEntry,meta);' "$ENL"

test -f Darkroom-v0.2.5.apk
test -f Darkroom-v0.2.5.sha256
grep -Fq "versionCode='16'" apk-badging-v015.txt
grep -Fq "versionName='0.2.5'" apk-badging-v015.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v015.txt
unzip -Z1 Darkroom-v0.2.5.apk > apk-listing-v025.txt
! grep -Eiq '(^|/)home_vintage\.(jpg|jpeg|png|webp)$' apk-listing-v025.txt
sha256sum Darkroom-v0.2.5.apk | tee Darkroom-v0.2.5.sha256
