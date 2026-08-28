#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.0 — five camera manuals + 25 FAQs in Uso e Manutenzione.
# Base: verified Darkroom v0.2.9. Timer/Split Grade/SONOFF behavior is preserved.

python3 -m py_compile \
  combined/patch_v029_darkroom_guide_faq_home_fix.py \
  combined/patch_v030_camera_manuals_faq.py

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
        raise SystemExit('v0.3.0 source build marker missing: '+marker)

# Reuse the verified v0.2.8 reconstruction recipe, preserving v0.2.9 and adding v0.3.0.
s=s.replace('0.2.8','0.3.0')
s=s.replace('versionCode="19"','versionCode="21"')
s=s.replace('versionCode 19','versionCode 21')
s=s.replace("versionCode='19'","versionCode='21'")
s=s.replace('apk-listing-v028.txt','apk-listing-v030.txt')

compile_marker='  combined/patch_v028_graphic_refresh.py\n'
if s.count(compile_marker)!=1:
    raise SystemExit('v0.3.0 compile insertion marker ambiguous')
s=s.replace(
    compile_marker,
    '  combined/patch_v028_graphic_refresh.py \\\n  combined/patch_v029_darkroom_guide_faq_home_fix.py \\\n  combined/patch_v030_camera_manuals_faq.py\n',
    1
)

# Append the v0.2.9 and v0.3.0 patches to the generated-build patch list.
m=re.search(r"(?m)^(\s*\+ 'python3 combined/patch_v028_graphic_refresh\.py)([^']*)'\)$",s)
if not m:
    raise SystemExit('v0.3.0 patch-list insertion marker missing')
suffix=m.group(2)
replacement=(m.group(1)+suffix+"'\n"
             +"    + 'python3 combined/patch_v029_darkroom_guide_faq_home_fix.py"+suffix+"'\n"
             +"    + 'python3 combined/patch_v030_camera_manuals_faq.py"+suffix+"')")
s=s[:m.start()]+replacement+s[m.end():]

anchor='test -f Darkroom-v0.3.0.apk\n'
if s.count(anchor)!=1:
    raise SystemExit('v0.3.0 artifact validation marker ambiguous')
checks=r'''# v0.2.9 preserved additions.
grep -Fq '"SVILUPPO PELLICOLA".equals(text) ? 18f : 20f' "$HOME"
grep -Fq 'APP DARKROOM' "$MAINT"
grep -Fq 'Q_DARKROOM' "$MAINT"
grep -Fq 'A_DARKROOM' "$MAINT"
grep -Fq '1_40jRUpA5Qxwr9a_n6PiT3V19SqZijQ2' "$MAINT"

# v0.3.0 camera manuals and 25 FAQs.
grep -Fq 'FOTOCAMERE' "$MAINT"
grep -Fq 'NIKON L35AF' "$MAINT"
grep -Fq 'NIKON D100' "$MAINT"
grep -Fq 'NIKON ZOOM 100 AF' "$MAINT"
grep -Fq 'ROLLEIFLEX 3.5 AUTOMAT MX' "$MAINT"
grep -Fq 'ROLLEIFLEX 2.8 E2' "$MAINT"
grep -Fq 'Q_NIKON_L35AF' "$MAINT"
grep -Fq 'Q_NIKON_D100' "$MAINT"
grep -Fq 'Q_NIKON_ZOOM100' "$MAINT"
grep -Fq 'Q_ROLLEI_35_MX' "$MAINT"
grep -Fq 'Q_ROLLEI_28_E2' "$MAINT"
grep -Fq 'FAQ count must be 5 or 10 for ' "$MAINT"
grep -Fq '1jIPGhIIwLcnDRN4D4Bb8AtLZMV6UsqPT' "$MAINT"
grep -Fq '1-6_YrOo-hJwlLB4en3-vcBupuHxQm1l9' "$MAINT"
grep -Fq '1hyDsxIw4Qic4peEWu-vRP95pfMh1BxWI' "$MAINT"
grep -Fq '1vt9usyPAyd0N5Zd1LS-UTKvMZmBJVAmm' "$MAINT"
grep -Fq '1aES38tuDIy9I8RQlGTJDVNAVyzf3SdiS' "$MAINT"

'''
s=s.replace(anchor,checks+anchor,1)
Path('/tmp/build_v030_generated.sh').write_text(s,encoding='utf-8')
PY

bash /tmp/build_v030_generated.sh

python3 - <<'PY'
from pathlib import Path
p=Path('validation-v015.txt')
if not p.exists():
    raise SystemExit('v0.3.0 validation file missing after build')
lines=[]
for line in p.read_text(encoding='utf-8').splitlines():
    if line.startswith('versionName='):
        line='versionName=0.3.0'
    elif line.startswith('versionCode='):
        line='versionCode=21'
    lines.append(line)
for flag in [
    'home_film_label_fit=PASS',
    'darkroom_guide_drive_link=PASS',
    'darkroom_app_faq_count_10=PASS',
    'camera_manual_count_5=PASS',
    'camera_faq_total_25=PASS',
    'camera_drive_links_5=PASS',
]:
    if flag not in lines:
        if 'build=SUCCESS' in lines:
            lines.insert(lines.index('build=SUCCESS'),flag)
        else:
            lines.append(flag)
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
PY
