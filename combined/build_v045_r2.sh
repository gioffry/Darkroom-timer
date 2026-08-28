#!/usr/bin/env bash
set -euo pipefail

# Generate the v0.4.5 build from the existing recipe, changing only the v0.4.5
# FAQ validator to inspect each Java array body independently.
python3 - <<'PY'
from pathlib import Path
p=Path('combined/build_v045.sh')
s=p.read_text(encoding='utf-8')
s=s.replace('python3 combined/patch_v045_zone_minolta_ev_faqs_r2.py | tee validation-v045-zone-minolta.txt',
            'python3 combined/patch_v045_zone_minolta_ev_faqs_r3.py | tee validation-v045-zone-minolta.txt',1)
old='''def block(a,b):
    x=s.index('private static final String[] '+a)
    y=s.index('private static final String[] '+b,x)
    return s[x:y]
def nstrings(x): return len(re.findall(r'\"(?:\\\\.|[^\"\\\\])*\"',x))
qm=block('Q_MINOLTA','A_MINOLTA')
am=block('A_MINOLTA','Q_PROCESS_WASH')
qz=block('Q_ZONE','A_ZONE')
az=block('A_ZONE','Q_PRINT')
assert nstrings(qm)==12, nstrings(qm)
assert nstrings(am)==12, nstrings(am)
assert nstrings(qz)==11, nstrings(qz)
assert nstrings(az)==11, nstrings(az)
'''
new='''def array_body(name):
    marker='private static final String[] '+name+' = {'
    x=s.index(marker)
    a=s.index('{',x)+1
    b=s.index('\\n    };',a)
    return s[a:b]
def nstrings(x): return len(re.findall(r'\"(?:\\\\.|[^\"\\\\])*\"',x))
qm=array_body('Q_MINOLTA')
am=array_body('A_MINOLTA')
qz=array_body('Q_ZONE')
az=array_body('A_ZONE')
assert nstrings(qm)==12, nstrings(qm)
assert nstrings(am)==12, nstrings(am)
assert nstrings(qz)==11, nstrings(qz)
assert nstrings(az)==11, nstrings(az)
'''
if old not in s:
    raise SystemExit('v0.4.5 r2 build validator marker missing')
s=s.replace(old,new,1)
Path('/tmp/build_v045_generated.sh').write_text(s,encoding='utf-8')
PY
bash /tmp/build_v045_generated.sh
