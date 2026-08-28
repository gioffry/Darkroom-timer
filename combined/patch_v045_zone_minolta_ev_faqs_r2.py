#!/usr/bin/env python3
from pathlib import Path

src = Path('combined/patch_v045_zone_minolta_ev_faqs.py')
code = src.read_text(encoding='utf-8')
anchor = '# Order and counts: Minolta table first, Minolta Zone second; Zone quick guide first.\n'
helper = '''# Count Java string literals robustly: some historical FAQ arrays keep several entries on one source line.\nimport re\ndef count_java_strings(block):\n    return len(re.findall(r'\"(?:\\\\.|[^\"\\\\])*\"', block))\n\n'''
if anchor not in code:
    raise SystemExit('v0.4.5 r2: validation anchor missing')
code = code.replace(anchor, helper + anchor, 1)
repls = {
    "q_min.count('            \"')": "count_java_strings(q_min)",
    "a_min.count('            \"')": "count_java_strings(a_min)",
    "out[qz_start:qz_end].count('            \"')": "count_java_strings(out[qz_start:qz_end])",
    "out[az_start:az_end].count('            \"')": "count_java_strings(out[az_start:az_end])",
}
for old,new in repls.items():
    if old not in code:
        raise SystemExit('v0.4.5 r2: count marker missing: ' + old)
    code = code.replace(old,new,1)
exec(compile(code, str(src), 'exec'), {'__name__':'__main__'})
