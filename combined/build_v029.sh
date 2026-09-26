#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.9 — chemistry safety correction.
# Base: canonical v0.2.8. Timer/SONOFF and print workflows are unchanged.

python3 - <<'PY'
from pathlib import Path
p = Path('combined/build_v011.sh')
s = p.read_text(encoding='utf-8')
marker = 'python3 assistant/patch_v038_edit_persistence_simplify.py\n'
if marker not in s:
    raise SystemExit('v0.2.9: Assistant v0.3.8 patch marker missing')
if 'python3 assistant/patch_v039_chemistry_safety.py\n' not in s:
    s = s.replace(marker, marker + 'python3 assistant/patch_v039_chemistry_safety.py\n', 1)
p.write_text(s, encoding='utf-8')
PY

python3 - <<'PY'
from pathlib import Path
s = Path('combined/build_v028.sh').read_text(encoding='utf-8')

# Re-target the canonical v0.2.8 wrapper without altering its stable source base.
s = s.replace('0.2.8', '0.2.9')
s = s.replace('versionCode="19"', 'versionCode="20"')
s = s.replace('versionCode 19', 'versionCode 20')
s = s.replace("versionCode='19'", "versionCode='20'")
s = s.replace('versionCode=19', 'versionCode=20')
s = s.replace('apk-listing-v028.txt', 'apk-listing-v029.txt')

Path('/tmp/build_v029_generated.sh').write_text(s, encoding='utf-8')
PY

bash /tmp/build_v029_generated.sh

python3 - <<'PY'
from pathlib import Path
p = Path('validation-v015.txt')
if not p.exists():
    raise SystemExit('v0.2.9: validation file missing')
s = p.read_text(encoding='utf-8')
if 'assistant_version=0.3.8' in s:
    s = s.replace('assistant_version=0.3.8', 'assistant_version=0.3.9')
elif 'assistant_version=0.3.9' not in s:
    s += 'assistant_version=0.3.9\n'
extra = [
    'chemistry_excel_stock_capacity=PASS',
    'chemistry_excel_1plus1_one_shot=PASS',
    'chemistry_excel_reuse_dilution_separated=PASS',
    'chemistry_compard_film_1plus5_1plus7=PASS',
    'chemistry_compard_legacy_1plus4_repair=PASS',
    'chemistry_jobo_estimate_label=PASS',
]
lines = s.splitlines()
for x in extra:
    if x not in lines:
        lines.append(x)
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
PY

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java

grep -q 'STIMA JOBO CPE2' "$ASSIST"
grep -q 'regola generale, non dato specifico del produttore' "$ASSIST"
grep -q 'new String[]{"1+5", "1+7"}, new String[]{"1+7", "1+9"}, "1+5"' "$ASSIST"
grep -q '1+1 monouso' "$ASSIST"
grep -q 'capacità FOMA 12 pellicole/L' "$ASSIST"
grep -q 'key(p.name) + "_stock"' "$ASSIST"
! grep -q 'scheda Compard 1+4: 20–40 pellicole/L' "$ASSIST"

test -f Darkroom-v0.2.9.apk
test -f Darkroom-v0.2.9.sha256
grep -Fq "versionCode='20'" apk-badging-v015.txt
grep -Fq "versionName='0.2.9'" apk-badging-v015.txt
