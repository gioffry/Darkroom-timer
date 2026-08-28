#!/usr/bin/env python3
from pathlib import Path
import json, re, subprocess, sys, unicodedata

HERE = Path(__file__).resolve().parent
SCOPE = HERE / 'macodirect_current_scope.json'
APPLIER = HERE / 'apply_manufacturer_batch.py'
if len(sys.argv) != 2:
    raise SystemExit('usage: apply_macodirect_scoped_batch.py BATCH.json')
batch = Path(sys.argv[1])
if not batch.exists(): raise SystemExit('missing batch: '+str(batch))

def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode('ascii').lower()
    s=s.replace('–',' ').replace('—',' ').replace('-',' ')
    return ' '.join(re.sub(r'[^a-z0-9+]+',' ',s).split())

scope=json.loads(SCOPE.read_text(encoding='utf-8'))
allowed={norm(r['developer']):r['developer'] for r in scope.get('records',[])}
payload=json.loads(batch.read_text(encoding='utf-8'))
if payload.get('hierarchy')!='MDC_FIRST_MANUFACTURER_FILL_ONLY':
    raise SystemExit('invalid hierarchy in '+batch.name)
violations=[]
for rec in payload.get('records',[]):
    matches=[norm(x) for x in rec.get('matchNames',[]) if str(x).strip()]
    if not matches or not any(x in allowed for x in matches):
        violations.append(' | '.join(rec.get('matchNames',[])))
if violations:
    raise SystemExit('OUTSIDE_MACODIRECT_SCOPE: '+'; '.join(violations))
print(f'macodirect_scope_guard=PASS batch={batch.name} records={len(payload.get("records",[]))}')
subprocess.run([sys.executable,str(APPLIER),str(batch)],check=True)
