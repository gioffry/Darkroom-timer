#!/usr/bin/env python3
from pathlib import Path
import csv, json, sqlite3, re, unicodedata

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'src/main/assets/mdc_full.sqlite'
SCOPE=Path(__file__).resolve().parent/'macodirect_current_scope.json'
OUT_TXT=Path('macodirect-scope-audit.txt')
OUT_CSV=Path('macodirect-scope-missing.csv')

def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode('ascii').lower()
    s=s.replace('–',' ').replace('—',' ').replace('-',' ')
    return ' '.join(re.sub(r'[^a-z0-9+]+',' ',s).split())

def present(v): return bool(str(v or '').strip())

def complete_core(r):
    fixed=['manufacturer','physical_state','preparation','reuse_mode','capacity_text']
    shelf=['shelf_life_unopened','shelf_life_opened','shelf_life_stock','shelf_life_working']
    return all(present(r[k]) for k in fixed) and any(present(r[k]) for k in shelf)

def missing_core(r):
    miss=[k for k in ['manufacturer','physical_state','preparation','reuse_mode','capacity_text'] if not present(r[k])]
    if not any(present(r[k]) for k in ['shelf_life_unopened','shelf_life_opened','shelf_life_stock','shelf_life_working']):
        miss.append('at_least_one_shelf_life')
    return miss

scope=json.loads(SCOPE.read_text(encoding='utf-8'))
records=scope.get('records',[])
if len(records)!=21: raise SystemExit(f'expected frozen scope of 21, found {len(records)}')
con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; cur=con.cursor()
profiles={norm(r['developer_name']):r for r in cur.execute('SELECT * FROM developer_profiles')}
rows=[]; missing_names=[]; completed=0
for item in records:
    p=profiles.get(norm(item['developer']))
    if p is None:
        missing_names.append(item['developer']); continue
    ok=complete_core(p); completed += 1 if ok else 0
    rows.append({
        'developer':p['developer_name'],'macodirect_name':item.get('macodirectName',''),
        'macodirect_status':item.get('status',''),'complete_core':'YES' if ok else 'NO',
        'missing_core':','.join(missing_core(p)),
        'mdc_combinations':p['mdc_combination_count'],'mdc_films':p['mdc_film_count'],
        'evidence_url':item.get('evidenceUrl','')})
if missing_names: raise SystemExit('scope developers missing from DB: '+', '.join(missing_names))
with OUT_CSV.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
base_incomplete=int(scope.get('basisIncompleteCount',186))
lines=[
 'macodirect_scope_audit=PASS',
 f'basis_run_id={scope.get("basisRunId","")}',
 f'basis_incomplete={base_incomplete}',
 f'macodirect_scope_total={len(rows)}',
 f'macodirect_scope_complete_core={completed}',
 f'macodirect_scope_incomplete_core={len(rows)-completed}',
 f'outside_scope_incomplete_ignored={base_incomplete-len(rows)}',
 'macodirect_role=COMMERCE_FILTER_ONLY',
 'technical_sources=MANUFACTURERS_ONLY',
 'sold_out_current_listing_counts=true',
 'scope_file=assistant/db/macodirect_current_scope.json',
 f'scope_missing_report={OUT_CSV.name}'
]
OUT_TXT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
con.close()
