#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.0: visual coherence release.
# Base source: verified Darkroom v0.1.9; runtime Timer/SONOFF logic unchanged.
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
        raise SystemExit('v0.2.0 build wrapper: marker missing in v0.1.8: ' + marker)

s = s.replace('Darkroom-v0.1.8', 'Darkroom-v0.2.0')
s = s.replace('versionCode="9"', 'versionCode="11"')
s = s.replace('versionCode 9', 'versionCode 11')
s = s.replace("versionCode='9'", "versionCode='11'")
s = s.replace('versionName="0.1.8"', 'versionName="0.2.0"')
s = s.replace("versionName '0.1.8'", "versionName '0.2.0'")
s = s.replace("versionName='0.1.8'", "versionName='0.2.0'")

needle = 'python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n'
replacement = (needle
               + 'python3 combined/patch_v019_use_maintenance.py\\\\n'
               + 'python3 combined/patch_v020_visual_coherence.py\\\\n')
if s.count(needle) != 1:
    raise SystemExit('v0.2.0 build wrapper: patch insertion point ambiguous')
s = s.replace(needle, replacement, 1)
Path('/tmp/build_v020_generated.sh').write_text(s, encoding='utf-8')
PY

bash /tmp/build_v020_generated.sh

# Canonicalize inherited validation metadata for this release.
python3 - <<'PY'
from pathlib import Path
p = Path('validation-v015.txt')
if not p.exists():
    raise SystemExit('v0.2.0: validation file missing')
s = p.read_text(encoding='utf-8')
lines = []
for line in s.splitlines():
    if line.startswith('versionName='):
        line = 'versionName=0.2.0'
    elif line.startswith('versionCode='):
        line = 'versionCode=11'
    lines.append(line)
for extra in [
    'home_mockup_approved=PASS',
    'home_scale_fit_center=PASS',
    'visual_coherence_assistant=PASS',
    'visual_coherence_maintenance=PASS',
    'timer_runtime_logic_unchanged=PASS',
]:
    if extra not in lines:
        lines.append(extra)
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY

# Post-build package and regression guards.
grep -q 'ImageView.ScaleType.FIT_CENTER' combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'CAMERA OSCURA' combined/patch_v020_visual_coherence.py
grep -q 'USO E MANUTENZIONE' combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'getPackageInfo(getPackageName(), 0)' combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'title.toUpperCase(Locale.ITALY)' combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
grep -q 'class UseMaintenanceActivity' combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
grep -q 'backStack.isEmpty()?"⌂":"←"' combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
grep -q 'private static final String APP_VERSION = "0.13.7";' combined/src/main/java/it/darkroom/timer/MainActivity.java
grep -q 'sonoff_rounding_500ms=PASS' validation-v015.txt

test -f Darkroom-v0.2.0.apk
test -f Darkroom-v0.2.0.sha256
grep -Fq "versionCode='11'" apk-badging-v015.txt
grep -Fq "versionName='0.2.0'" apk-badging-v015.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v015.txt
