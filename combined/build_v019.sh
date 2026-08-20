#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.1.9 build wrapper. Base: verified Darkroom v0.1.8.
python3 - <<'PY'
from pathlib import Path
src_path = Path('combined/build_v018.sh')
s = src_path.read_text(encoding='utf-8')

required = [
    'Darkroom-v0.1.8',
    'versionCode="9"',
    'versionName="0.1.8"',
    'python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n',
]
for marker in required:
    if marker not in s:
        raise SystemExit('v0.1.9 build wrapper: marker missing in v0.1.8: ' + marker)

s = s.replace('Darkroom-v0.1.8', 'Darkroom-v0.1.9')
s = s.replace('versionCode="9"', 'versionCode="10"')
s = s.replace('versionCode 9', 'versionCode 10')
s = s.replace("versionCode='9'", "versionCode='10'")
s = s.replace('versionName="0.1.8"', 'versionName="0.1.9"')
s = s.replace("versionName '0.1.8'", "versionName '0.1.9'")
s = s.replace("versionName='0.1.8'", "versionName='0.1.9'")

needle = 'python3 combined/patch_v018_enlargement_fixes_r2.py\\\\n'
replacement = needle + 'python3 combined/patch_v019_use_maintenance.py\\\\n'
if s.count(needle) != 1:
    raise SystemExit('v0.1.9 build wrapper: v0.1.8 patch insertion point ambiguous')
s = s.replace(needle, replacement, 1)

Path('/tmp/build_v019_generated.sh').write_text(s, encoding='utf-8')
PY

bash /tmp/build_v019_generated.sh

# Post-build regression and package guards.
grep -q 'USO E MANUTENZIONE' combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'getPackageInfo(getPackageName(), 0)' combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'class UseMaintenanceActivity' combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
grep -q 'android:name=".maintenance.UseMaintenanceActivity"' combined/src/main/AndroidManifest.xml
grep -q 'MINOLTA_PENDING' combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
grep -q 'Q_SPLIT' combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
grep -q 'Q_ZONE' combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
grep -q 'Q_PRINT' combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java

test -f Darkroom-v0.1.9.apk
test -f Darkroom-v0.1.9.sha256
grep -Fq "versionCode='10'" apk-badging-v015.txt
grep -Fq "versionName='0.1.9'" apk-badging-v015.txt
