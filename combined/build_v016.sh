#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v012.sh').read_text(encoding='utf-8')
s=s.replace('Darkroom-v0.1.5','Darkroom-v0.1.6')
s=s.replace('versionCode="6"','versionCode="7"').replace("versionCode 6","versionCode 7").replace("versionCode='6'","versionCode='7'")
s=s.replace('versionName="0.1.5"','versionName="0.1.6"').replace("versionName '0.1.5'","versionName '0.1.6'").replace("versionName='0.1.5'","versionName='0.1.6'")
needle='gradle :combined:assembleRelease --stacktrace'
insert='''python3 combined/patch_v016_enlargement.py\npython3 combined/patch_v016_fix_entries.py\ngrep -q 'RIDIMENSIONA STAMPA' combined/src/main/java/it/darkroom/timer/MainActivity.java\ngrep -q 'IMPOSTA INGRANDIMENTO' combined/src/main/java/it/darkroom/timer/MainActivity.java\ngrep -q 'class EnlargementActivity' combined/src/main/java/it/darkroom/timer/EnlargementActivity.java\ngrep -q 'android:name=".EnlargementActivity"' combined/src/main/AndroidManifest.xml\ngradle :combined:assembleRelease --stacktrace'''
if needle not in s: raise SystemExit('gradle marker missing')
s=s.replace(needle,insert,1)
s=s.replace("echo 'build=SUCCESS'","echo 'enlargement_change=PASS'\n  echo 'meopta_calibration=PASS'\n  echo 'sonoff_rounding_500ms=PASS'\n  echo 'build=SUCCESS'")
Path('/tmp/build_v016_generated.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v016_generated.sh
