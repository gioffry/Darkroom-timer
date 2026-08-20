#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.1: Home JPEG runtime fix + font coherence + explicit LOG fields.
# Base: verified Darkroom v0.2.0 source line; Timer/SONOFF timing remains unchanged.

# Recover the complete approved CAMERA OSCURA artwork used by the mockup.
git fetch --no-tags origin feature-darkroom-v012-vintage-home-r2
git checkout FETCH_HEAD -- combined/v012_assets/home_mockup
python3 - <<'PY'
from pathlib import Path
import base64
assets = Path('combined/v012_assets/home_mockup')
parts = sorted(assets.glob('*.part'))
if len(parts) != 9:
    raise SystemExit(f'v0.2.1: expected 9 historical Home asset parts, found {len(parts)}')
encoded = ''.join(''.join(p.read_text(encoding='utf-8').split()) for p in parts)
raw = base64.b64decode(encoded + '=' * (-len(encoded) % 4), validate=True)
if len(raw) < 50000 or raw[:4] != b'RIFF' or raw[8:12] != b'WEBP':
    raise SystemExit('v0.2.1: historical approved Home asset is not a valid WebP')
for p in parts:
    p.unlink()
cut = (len(encoded) + 1) // 2
(assets / '00.part').write_text(encoded[:cut], encoding='utf-8')
(assets / '01.part').write_text(encoded[cut:], encoding='utf-8')
print('Approved CAMERA OSCURA source restored:', len(raw), 'bytes')
PY

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
        raise SystemExit('v0.2.1 build wrapper: marker missing in v0.1.8: ' + marker)

s = s.replace('Darkroom-v0.1.8', 'Darkroom-v0.2.1')
s = s.replace('versionCode="9"', 'versionCode="12"')
s = s.replace('versionCode 9', 'versionCode 12')
s = s.replace("versionCode='9'", "versionCode='12'")
s = s.replace('versionName="0.1.8"', 'versionName="0.2.1"')
s = s.replace("versionName '0.1.8'", "versionName '0.2.1'")
s = s.replace("versionName='0.1.8'", "versionName='0.2.1'")

needle = 'python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n'
replacement = (needle
               + 'python3 combined/patch_v019_use_maintenance.py\\\\n'
               + 'python3 combined/patch_v020_enlargement_log_flow.py\\\\n'
               + 'python3 combined/patch_v020_enlargement_legacy_recipe.py\\\\n'
               + 'python3 combined/patch_v020_visual_coherence.py\\\\n'
               + 'python3 combined/patch_v021_home_font_log_fix.py\\\\n')
if s.count(needle) != 1:
    raise SystemExit('v0.2.1 build wrapper: patch insertion point ambiguous')
s = s.replace(needle, replacement, 1)
Path('/tmp/build_v021_generated.sh').write_text(s, encoding='utf-8')
PY

bash /tmp/build_v021_generated.sh

python3 - <<'PY'
from pathlib import Path
p = Path('validation-v015.txt')
if not p.exists():
    raise SystemExit('v0.2.1: validation file missing')
lines = []
for line in p.read_text(encoding='utf-8').splitlines():
    if line.startswith('versionName='):
        line = 'versionName=0.2.1'
    elif line.startswith('versionCode='):
        line = 'versionCode=12'
    lines.append(line)
for extra in [
    'home_mockup_approved=PASS',
    'home_asset_format=JPEG',
    'home_asset_dimensions=864x1536',
    'home_jpeg_full_decode=PASS',
    'home_black_screen_fix=PASS',
    'home_no_duplicate_maintenance_overlay=PASS',
    'maintenance_font_timer_default=PASS',
    'log_enlargement_meta_per_print=PASS',
    'log_visible_paper_size=PASS',
    'log_visible_column_height=PASS',
    'legacy_log_display_backfill=PASS',
    'derived_log_display_fields=PASS',
    'timer_runtime_logic_unchanged=PASS',
]:
    if extra not in lines:
        lines.append(extra)
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY

HOME=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
JPG=combined/src/main/res/drawable-nodpi/home_vintage.jpg

# Home must be a real, fully decodable JPEG, not the WebP that rendered black.
test -s "$JPG"
test ! -f combined/src/main/res/drawable-nodpi/home_vintage.webp
test "$(head -c 2 "$JPG" | od -An -tx1 | tr -d ' \n')" = "ffd8"
test "$(tail -c 2 "$JPG" | od -An -tx1 | tr -d ' \n')" = "ffd9"
ffmpeg -v error -xerror -i "$JPG" -frames:v 1 -f null -
test "$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$JPG")" = "864x1536"
grep -q 'ImageView.ScaleType.FIT_CENTER' "$HOME"
grep -q 'ART_W = 864f' "$HOME"
grep -q 'UseMaintenanceActivity.class' "$HOME"
grep -q 'getPackageInfo(getPackageName(), 0)' "$HOME"
! grep -q 'secondaryButton()' "$HOME"
! grep -q 'ic_wrench_bronze' "$HOME"

# Uso e Manutenzione must use the same default operational sans font as Timer.
grep -q 'Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL' "$MAINT"
! grep -q 'sans-serif-condensed' "$MAINT"

# Every print keeps complete metadata and synchronizes visible paper/column fields.
grep -q 'syncEnlargementDisplayFields(e, e.enlargementMeta);' "$MAIN"
grep -q 'entry.columnHeight = value;' "$MAIN"
grep -q 'entry.paper = current + " · " + format;' "$MAIN"
grep -q 'pendingEnlargementMeta' "$MAIN"
grep -q 'syncLogDisplayFields(originEntry,meta);' "$ENL"
grep -q 'syncLogDisplayFields(d,x.newMeta);' "$ENL"
grep -q 'orientation=LANDSCAPE' "$ENL"
grep -q 'paper=%.1fx%.1f' "$ENL"
grep -q 'col=%.8f' "$ENL"

# Protected runtime invariants.
grep -q 'private static final String APP_VERSION = "0.13.7";' "$MAIN"
grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt

test -f Darkroom-v0.2.1.apk
test -f Darkroom-v0.2.1.sha256
grep -Fq "versionCode='12'" apk-badging-v015.txt
grep -Fq "versionName='0.2.1'" apk-badging-v015.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v015.txt
unzip -l Darkroom-v0.2.1.apk > apk-listing-v021.txt
grep -q 'home_vintage' apk-listing-v021.txt
