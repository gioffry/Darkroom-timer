#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.1: real-device Home repair + typography and visible LOG fields.
# Base: verified successful Darkroom v0.2.0 branch; Timer/SONOFF timing untouched.
python3 - <<'PY'
from pathlib import Path
src = Path('combined/build_v020.sh')
s = src.read_text(encoding='utf-8')
required = [
    'Darkroom-v0.2.0',
    'versionCode="11"',
    'versionName="0.2.0"',
    "python3 combined/patch_v020_visual_coherence.py",
    'completed enlargement/log flow',
]
for marker in required:
    if marker not in s:
        raise SystemExit('v0.2.1 build wrapper: v0.2.0 marker missing: ' + marker)

# Release identity.
s = s.replace('Darkroom-v0.2.0', 'Darkroom-v0.2.1')
s = s.replace('Darkroom v0.2.0', 'Darkroom v0.2.1')
s = s.replace('v0.2.0:', 'v0.2.1:')
s = s.replace('versionCode="11"', 'versionCode="12"')
s = s.replace('versionCode 11', 'versionCode 12')
s = s.replace("versionCode='11'", "versionCode='12'")
s = s.replace('versionCode=11', 'versionCode=12')
s = s.replace('versionName="0.2.0"', 'versionName="0.2.1"')
s = s.replace("versionName '0.2.0'", "versionName '0.2.1'")
s = s.replace("versionName='0.2.0'", "versionName='0.2.1'")
s = s.replace('versionName=0.2.0', 'versionName=0.2.1')

# Apply the real-device repair after all v0.2.0 source transformations and
# before Gradle assembles/signs the APK.
needle = "               + 'python3 combined/patch_v020_visual_coherence.py\\\\n')"
replacement = ("               + 'python3 combined/patch_v020_visual_coherence.py\\\\n'\n"
               "               + 'python3 combined/patch_v021_home_font_log_fix.py\\\\n')")
if s.count(needle) != 1:
    raise SystemExit('v0.2.1 build wrapper: visual patch insertion point ambiguous')
s = s.replace(needle, replacement, 1)
s = s.replace('/tmp/build_v020_generated.sh', '/tmp/build_v021_generated.sh')
Path('/tmp/build_v021_full.sh').write_text(s, encoding='utf-8')
PY

bash /tmp/build_v021_full.sh

# Strong real-device guards that v0.2.0 did not have.
HOME=combined/src/main/res/drawable-nodpi/home_vintage.jpg
test -s "$HOME"
test ! -e combined/src/main/res/drawable-nodpi/home_vintage.webp
test "$(head -c 2 "$HOME" | od -An -tx1 | tr -d ' \n')" = "ffd8"
test "$(tail -c 2 "$HOME" | od -An -tx1 | tr -d ' \n')" = "ffd9"
ffmpeg -v error -xerror -i "$HOME" -frames:v 1 -f null -
HOME_DIMS="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$HOME")"
test "$HOME_DIMS" = "864x1536"

HOME_JAVA=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java

grep -q 'hotspot("USO E MANUTENZIONE")' "$HOME_JAVA"
grep -q 'ART_W = 864f' "$HOME_JAVA"
grep -q 'ART_H = 1536f' "$HOME_JAVA"
! grep -q 'secondaryButton()' "$HOME_JAVA"
! grep -q 'sans-serif-condensed' "$MAINT"
grep -q 'Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL' "$MAINT"
grep -q 'applyEnlargementSnapshotToVisibleLogFields(e);' "$MAIN"
grep -q 'entry.columnHeight = value;' "$MAIN"
grep -q 'entry.paper = current + " · " + format;' "$MAIN"
grep -q 'formato carta ' "$MAIN"
grep -q 'Formato e ingrandimento:' "$MAIN"
grep -q 'syncLogDisplayFields(originEntry,meta);' "$ENL"
grep -q 'syncLogDisplayFields(d,x.newMeta);' "$ENL"

# Verify the packaged resource is present and decodable too, not merely the
# pre-build source file.
unzip -Z1 Darkroom-v0.2.1.apk > /tmp/v021-apk-files.txt
APK_HOME="$(grep -E '^res/drawable[^/]*/home_vintage\.(jpg|jpeg)$' /tmp/v021-apk-files.txt | head -n1)"
test -n "$APK_HOME"
unzip -p Darkroom-v0.2.1.apk "$APK_HOME" > /tmp/v021-packaged-home.jpg
ffmpeg -v error -xerror -i /tmp/v021-packaged-home.jpg -frames:v 1 -f null -
PACKAGED_DIMS="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 /tmp/v021-packaged-home.jpg)"
test "$PACKAGED_DIMS" = "864x1536"

grep -Fq "versionCode='12'" apk-badging-v015.txt
grep -Fq "versionName='0.2.1'" apk-badging-v015.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v015.txt

python3 - <<'PY'
from pathlib import Path
p = Path('validation-v015.txt')
lines = p.read_text(encoding='utf-8').splitlines()
extras = [
    'home_asset_format=JPEG',
    'home_asset_dimensions=864x1536',
    'home_source_full_decode=PASS',
    'home_packaged_full_decode=PASS',
    'home_visible_button_from_artwork=PASS',
    'home_duplicate_overlay_removed=PASS',
    'maintenance_font_timer_default=PASS',
    'new_log_paper_dimensions=PASS',
    'new_log_column_visible_field=PASS',
    'build=SUCCESS',
]
# Remove stale duplicate build line so the final status is unambiguous.
lines = [x for x in lines if x != 'build=SUCCESS']
for item in extras:
    if item not in lines:
        lines.append(item)
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY

# Recompute final checksum after all checks (APK itself is unchanged by checks).
sha256sum Darkroom-v0.2.1.apk | tee Darkroom-v0.2.1.sha256
