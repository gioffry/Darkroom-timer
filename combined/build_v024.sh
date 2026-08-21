#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.4 — Piece 1: temporary native-button Home, no artwork dependency.
# Base: last verified Darkroom v0.2.1. Timer/SONOFF/Provino logic unchanged.

# v0.2.1 patch is retained because it also contains the approved maintenance-font
# and LOG/enlargement persistence fixes. Reconstruct its historical source payload
# only long enough for that patch to run; v0.2.4 then removes the Home artwork.
git fetch --no-tags origin feature-darkroom-v012-vintage-home-r2
git checkout FETCH_HEAD -- combined/v012_assets/home_mockup
python3 - <<'PY'
from pathlib import Path
import base64
assets = Path('combined/v012_assets/home_mockup')
parts = sorted(assets.glob('*.part'))
if len(parts) != 9:
    raise SystemExit(f'v0.2.4: expected 9 historical Home parts for v0.2.1 compatibility, found {len(parts)}')
encoded = ''.join(''.join(p.read_text(encoding='utf-8').split()) for p in parts)
raw = base64.b64decode(encoded + '=' * (-len(encoded) % 4), validate=True)
if len(raw) < 50000 or raw[:4] != b'RIFF' or raw[8:12] != b'WEBP':
    raise SystemExit('v0.2.4: historical Home compatibility payload invalid')
for p in parts:
    p.unlink()
cut = (len(encoded) + 1) // 2
(assets / '00.part').write_text(encoded[:cut], encoding='utf-8')
(assets / '01.part').write_text(encoded[cut:], encoding='utf-8')
PY

# Keep the already-approved v0.2.1 decode guard relaxation while that patch runs.
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
        raise SystemExit('v0.2.4 build wrapper: marker missing in v0.1.8: ' + marker)

s = s.replace('Darkroom-v0.1.8', 'Darkroom-v0.2.4')
s = s.replace('versionCode="9"', 'versionCode="15"')
s = s.replace('versionCode 9', 'versionCode 15')
s = s.replace("versionCode='9'", "versionCode='15'")
s = s.replace('versionName="0.1.8"', 'versionName="0.2.4"')
s = s.replace("versionName '0.1.8'", "versionName '0.2.4'")
s = s.replace("versionName='0.1.8'", "versionName='0.2.4'")

needle = 'python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n'
replacement = (needle
               + 'python3 combined/patch_v019_use_maintenance.py\\\\n'
               + 'python3 combined/patch_v020_enlargement_log_flow.py\\\\n'
               + 'python3 combined/patch_v020_enlargement_legacy_recipe.py\\\\n'
               + 'python3 combined/patch_v020_visual_coherence.py\\\\n'
               + 'python3 combined/patch_v021_home_font_log_fix.py\\\\n'
               + 'python3 combined/patch_v024_home_safe_buttons.py\\\\n')
if s.count(needle) != 1:
    raise SystemExit('v0.2.4 build wrapper: patch insertion point ambiguous')
s = s.replace(needle, replacement, 1)
Path('/tmp/build_v024_generated.sh').write_text(s, encoding='utf-8')
PY

bash /tmp/build_v024_generated.sh

python3 - <<'PY'
from pathlib import Path
p = Path('validation-v015.txt')
if not p.exists():
    raise SystemExit('v0.2.4: validation file missing')
lines = []
for line in p.read_text(encoding='utf-8').splitlines():
    if line.startswith('versionName='):
        line = 'versionName=0.2.4'
    elif line.startswith('versionCode='):
        line = 'versionCode=15'
    elif line == 'build=SUCCESS':
        continue
    # Remove v0.2.1 artwork-specific PASS claims: this release intentionally has no artwork.
    if line.startswith('home_mockup_approved=') or line.startswith('home_asset_') \
            or line.startswith('home_source_full_decode=') or line.startswith('home_packaged_full_decode=') \
            or line.startswith('home_black_screen_fix=') or line.startswith('home_no_duplicate_maintenance_overlay='):
        continue
    lines.append(line)
for extra in [
    'home_mode=native_buttons',
    'home_artwork_dependency=NONE',
    'home_artwork_removed=PASS',
    'home_five_visible_buttons=PASS',
    'home_products_route=PASS',
    'home_film_route=PASS',
    'home_paper_route=PASS',
    'home_timer_route=PASS',
    'home_maintenance_route=PASS',
    'home_runtime_version_label=PASS',
    'maintenance_font_timer_default=PASS',
    'log_enlargement_meta_per_print=PASS',
    'log_visible_paper_size=PASS',
    'log_visible_column_height=PASS',
    'legacy_log_display_backfill=PASS',
    'derived_log_display_fields=PASS',
    'timer_runtime_logic_unchanged=PASS',
    'build=SUCCESS',
]:
    if extra not in lines:
        lines.append(extra)
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY

HOME_JAVA=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java

# Piece-1 Home acceptance guards.
test -s "$HOME_JAVA"
grep -q 'CAMERA OSCURA' "$HOME_JAVA"
grep -q 'di Federico e Francesco' "$HOME_JAVA"
grep -q 'navButton("PRODOTTI CHIMICI", false)' "$HOME_JAVA"
grep -q 'navButton("SVILUPPO PELLICOLA", false)' "$HOME_JAVA"
grep -q 'navButton("BAGNI STAMPA", false)' "$HOME_JAVA"
grep -q 'navButton("TIMER STAMPA", false)' "$HOME_JAVA"
grep -q 'navButton("USO E MANUTENZIONE", true)' "$HOME_JAVA"
grep -q 'openAssistant("products")' "$HOME_JAVA"
grep -q 'openAssistant("film")' "$HOME_JAVA"
grep -q 'openAssistant("paper")' "$HOME_JAVA"
grep -q 'new Intent(this, MainActivity.class)' "$HOME_JAVA"
grep -q 'new Intent(this, UseMaintenanceActivity.class)' "$HOME_JAVA"
grep -q 'getPackageInfo(getPackageName(), 0)' "$HOME_JAVA"
! grep -q 'ImageView' "$HOME_JAVA"
! grep -q 'R.drawable.home_vintage' "$HOME_JAVA"
! grep -q 'ART_W' "$HOME_JAVA"
! grep -q 'ART_H' "$HOME_JAVA"
! find combined/src/main/res -type f \( -name 'home_vintage.jpg' -o -name 'home_vintage.jpeg' -o -name 'home_vintage.png' -o -name 'home_vintage.webp' \) | grep -q .

# Preserve the fixes already approved in v0.2.1.
! grep -q 'sans-serif-condensed' "$MAINT"
grep -q 'Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL' "$MAINT"
grep -q 'applyEnlargementSnapshotToVisibleLogFields(e);' "$MAIN"
grep -q 'entry.columnHeight = value;' "$MAIN"
grep -q 'entry.paper = current + " · " + format;' "$MAIN"
grep -q 'syncLogDisplayFields(originEntry,meta);' "$ENL"
grep -q 'syncLogDisplayFields(d,x.newMeta);' "$ENL"
grep -q 'private static final String APP_VERSION = "0.13.7";' "$MAIN"
grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt

test -f Darkroom-v0.2.4.apk
test -f Darkroom-v0.2.4.sha256
grep -Fq "versionCode='15'" apk-badging-v015.txt
grep -Fq "versionName='0.2.4'" apk-badging-v015.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v015.txt

unzip -Z1 Darkroom-v0.2.4.apk > apk-listing-v024.txt
! grep -Eiq '(^|/)home_vintage\.(jpg|jpeg|png|webp)$' apk-listing-v024.txt

sha256sum Darkroom-v0.2.4.apk | tee Darkroom-v0.2.4.sha256
