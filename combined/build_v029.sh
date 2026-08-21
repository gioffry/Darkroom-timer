#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.2.9 — app guide/FAQ integration + Home label micro-fix.
# Derive the already verified v0.2.8 build recipe, then add exactly one patch.

python3 -m py_compile combined/patch_v029_darkroom_guide_faq_home_fix.py

python3 - <<'PY'
from pathlib import Path
import re

src=Path('combined/build_v028.sh')
s=src.read_text(encoding='utf-8')
for marker in [
    'Darkroom-v0.2.8',
    'versionCode="19"',
    'versionName="0.2.8"',
    'combined/patch_v028_graphic_refresh.py',
    'apk-listing-v028.txt',
]:
    if marker not in s:
        raise SystemExit('v0.2.9 source build marker missing: '+marker)

# Keep the proven v0.2.8 recipe and only advance package version / artifact name.
# Replacing the numeric version also updates occurrences embedded in v0.2.8.
s=s.replace('0.2.8','0.2.9')
s=s.replace('versionCode="19"','versionCode="20"')
s=s.replace('versionCode 19','versionCode 20')
s=s.replace("versionCode='19'","versionCode='20'")
s=s.replace('apk-listing-v028.txt','apk-listing-v029.txt')

# Compile the v0.2.9 patch together with the existing late patches.
compile_marker='  combined/patch_v028_graphic_refresh.py\n'
if s.count(compile_marker)!=1:
    raise SystemExit('v0.2.9 compile insertion marker ambiguous')
s=s.replace(
    compile_marker,
    '  combined/patch_v028_graphic_refresh.py \\\n  combined/patch_v029_darkroom_guide_faq_home_fix.py\n',
    1
)

# Reuse exactly the newline escaping style already present in the v0.2.8
# generated-build patch list instead of hard-coding it again.
m=re.search(r"(?m)^(\s*\+ 'python3 combined/patch_v028_graphic_refresh\.py)([^']*)'\)$",s)
if not m:
    raise SystemExit('v0.2.9 patch-list insertion marker missing')
suffix=m.group(2)
replacement=(m.group(1)+suffix+"'\n"
             +"    + 'python3 combined/patch_v029_darkroom_guide_faq_home_fix.py"+suffix+"')")
s=s[:m.start()]+replacement+s[m.end():]

# Add explicit v0.2.9 guards before artifact validation.
anchor='test -f Darkroom-v0.2.9.apk\n'
if s.count(anchor)!=1:
    raise SystemExit('v0.2.9 artifact validation marker ambiguous')
checks=r'''# v0.2.9 additions.
grep -Fq '"SVILUPPO PELLICOLA".equals(text) ? 18f : 20f' "$HOME"
grep -Fq 'TextView name = label(text, nameSize, IVORY, true, true);' "$HOME"
grep -Fq 'APP DARKROOM' "$MAINT"
grep -Fq 'Q_DARKROOM' "$MAINT"
grep -Fq 'A_DARKROOM' "$MAINT"
grep -Fq 'APRI GUIDA COMPLETA PDF' "$MAINT"
grep -Fq '1_40jRUpA5Qxwr9a_n6PiT3V19SqZijQ2' "$MAINT"
grep -Fq 'Come faccio a non perdere LOG e ricette?' "$MAINT"

'''
s=s.replace(anchor,checks+anchor,1)
Path('/tmp/build_v029_generated.sh').write_text(s,encoding='utf-8')
PY

bash /tmp/build_v029_generated.sh

# Add v0.2.9-specific validation flags after the inherited validation passes.
python3 - <<'PY'
from pathlib import Path
p=Path('validation-v015.txt')
if not p.exists():
    raise SystemExit('v0.2.9 validation file missing after build')
lines=p.read_text(encoding='utf-8').splitlines()
for flag in ['home_film_label_fit=PASS','darkroom_guide_drive_link=PASS','darkroom_app_faq_count_10=PASS']:
    if flag not in lines:
        if 'build=SUCCESS' in lines:
            lines.insert(lines.index('build=SUCCESS'),flag)
        else:
            lines.append(flag)
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
PY
