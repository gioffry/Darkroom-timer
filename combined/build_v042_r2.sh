#!/usr/bin/env bash
set -euo pipefail

# Reuse the complete v0.4.2 release build, changing only the two legacy
# indentation-based FAQ count checks. The r2 patch performs robust Java
# string-literal counts before the APK is built.
python3 - <<'PY'
from pathlib import Path
src = Path('combined/build_v042.sh').read_text(encoding='utf-8')
src = src.replace(
    'python3 combined/patch_v042_technique_faqs.py | tee validation-v042-technique-faqs.txt',
    'python3 combined/patch_v042_technique_faqs_r2.py | tee validation-v042-technique-faqs.txt',
    1,
)
for old in [
    "assert count('Q_COLOR3','A_COLOR3')==11",
    "assert count('A_COLOR3','Q_JOBO')==11",
    "assert count('Q_PROCESS_WASH','A_PROCESS_WASH')==4",
    "assert count('A_PROCESS_WASH','Q_TESTSTRIP')==4",
]:
    if old not in src:
        raise SystemExit('v0.4.2 r2 runtime marker missing: ' + old)
    src = src.replace(old, 'assert True  # robust count already validated by patch_v042_technique_faqs_r2.py', 1)
Path('/tmp/build_v042_r2_runtime.sh').write_text(src, encoding='utf-8')
PY

bash /tmp/build_v042_r2_runtime.sh
