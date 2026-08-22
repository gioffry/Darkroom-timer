#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path
p=Path('combined/build_v035.sh')
s=p.read_text(encoding='utf-8')
needle="""python3 assistant/db/fix_italian_technical_profiles_v035.py combined/src/main/assets/mdc_full.sqlite \\
  | tee validation-v035-technical-db.txt
"""
if s.count(needle)!=1:
    raise SystemExit('v0.3.5 final insertion marker missing')
insert=needle+"""python3 assistant/db/complete_italian_preparations_v035_r2.py combined/src/main/assets/mdc_full.sqlite \\
  | tee validation-v035-preparations.txt
python3 assistant/db/complete_italian_durations_v035.py combined/src/main/assets/mdc_full.sqlite \\
  | tee validation-v035-durations.txt
"""
s=s.replace(needle,insert,1)
old='cat validation-v034.txt validation-v035-technical-db.txt validation-v035-bundled-db.txt > validation-v035.txt'
new='cat validation-v034.txt validation-v035-technical-db.txt validation-v035-preparations.txt validation-v035-durations.txt validation-v035-bundled-db.txt > validation-v035.txt'
if old not in s:
    raise SystemExit('v0.3.5 final validation concat marker missing')
s=s.replace(old,new,1)
Path('/tmp/build_v035_final_generated.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v035_final_generated.sh
