#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p=Path('combined/build_v025.sh')
s=p.read_text(encoding='utf-8')
needle="               + 'python3 combined/patch_v025_split_grade_provino.py\\\\\\\\n')"
replacement=("               + 'python3 combined/patch_v025_split_grade_provino.py\\\\\\\\n'\n"
             "               + 'python3 combined/patch_v025_split_grade_provino_fix.py\\\\\\\\n')")
if needle not in s:
    raise SystemExit('v0.2.5 final wrapper: v025 patch insertion marker missing')
s=s.replace(needle,replacement,1)
Path('/tmp/build_v025_final_generated.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v025_final_generated.sh
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
grep -q 'Due esposizioni consecutive, con tempi distinti.' "$MAIN"
! grep -q 'tempi indipendenti' "$MAIN"
grep -q 'putString("testBaseFilterType",testBaseFilterType)' "$MAIN"
