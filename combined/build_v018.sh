#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v016.sh').read_text(encoding='utf-8')
s=s.replace('Darkroom-v0.1.6','Darkroom-v0.1.8')
s=s.replace('versionCode="7"','versionCode="9"').replace('versionCode 7','versionCode 9').replace("versionCode='7'","versionCode='9'")
s=s.replace('versionName="0.1.6"','versionName="0.1.8"').replace("versionName '0.1.6'","versionName '0.1.8'").replace("versionName='0.1.6'","versionName='0.1.8'")
s=s.replace('python3 combined/patch_v016_fix_entries.py\\n','python3 combined/patch_v016_fix_entries.py\\npython3 combined/patch_v017_polish.py\\npython3 combined/patch_v017_settings_scroll.py\\npython3 combined/patch_v018_enlargement_fixes_r2.py\\n')
s=s.replace("grep -q 'class EnlargementActivity'", "grep -q 'LARGHEZZA CARTA (cm)' combined/src/main/java/it/darkroom/timer/EnlargementActivity.java\\ngrep -q 'ORIENTAMENTO · ORIZZONTALE' combined/src/main/java/it/darkroom/timer/EnlargementActivity.java\\ngrep -q 'RIDIMENSIONA STAMPA' combined/src/main/java/it/darkroom/timer/MainActivity.java\\ngrep -q 'enlargementMeta' combined/src/main/java/it/darkroom/timer/LogEntry.java\\ngrep -q 'enlargementReloadPending' combined/src/main/java/it/darkroom/timer/MainActivity.java\\ngrep -q 'class EnlargementActivity'")
Path('/tmp/build_v018_generated.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v018_generated.sh
