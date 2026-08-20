#!/usr/bin/env bash
set -euo pipefail
# Darkroom v0.1.7 build trigger
python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v016.sh').read_text(encoding='utf-8')
s=s.replace('Darkroom-v0.1.6','Darkroom-v0.1.7')
s=s.replace('versionCode="7"','versionCode="8"').replace('versionCode 7','versionCode 8').replace("versionCode='7'","versionCode='8'")
s=s.replace('versionName="0.1.6"','versionName="0.1.7"').replace("versionName '0.1.6'","versionName '0.1.7'").replace("versionName='0.1.6'","versionName='0.1.7'")
s=s.replace('python3 combined/patch_v016_fix_entries.py\\n','python3 combined/patch_v016_fix_entries.py\\npython3 combined/patch_v017_polish.py\\npython3 combined/patch_v017_settings_scroll.py\\n')
s=s.replace("grep -q 'class EnlargementActivity'", "grep -q 'FORMATO CARTA FOMA' combined/src/main/java/it/darkroom/timer/EnlargementActivity.java\\ngrep -q 'enlargementReloadPending' combined/src/main/java/it/darkroom/timer/MainActivity.java\\ngrep -q 'settingsScroll' combined/src/main/java/it/darkroom/timer/MainActivity.java\\ngrep -q 'class EnlargementActivity'")
Path('/tmp/build_v017_generated.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v017_generated.sh
