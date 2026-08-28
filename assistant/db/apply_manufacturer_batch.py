#!/usr/bin/env python3
from pathlib import Path
import json, re, sqlite3, sys, unicodedata

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'src/main/assets/mdc_full.sqlite'
BATCH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / 'producer_enrichment_batch2.json'

if not DB.exists(): raise SystemExit('MDC database missing')
if not BATCH.exists(): raise SystemExit('manufacturer batch missing: '+str(BATCH))

def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode('ascii').lower()
    s=s.replace('–',' ').replace('—',' ').replace('-',' ')
    return ' '.join(re.sub(r'[^a-z0-9+]+',' ',s).split())

def norm_dilution(s):
    s=str(s or '').strip()
    if not s:return ''
    if s.lower()=='stock':return 'stock'
    return s.replace(':','+').replace(' ','').lower()

def blank(v): return v is None or (isinstance(v,str) and not v.strip())

payload=json.loads(BATCH.read_text(encoding='utf-8'))
checked_at=payload.get('checkedAt','')
records=payload.get('records',[])
if payload.get('hierarchy')!='MDC_FIRST_MANUFACTURER_FILL_ONLY':
    raise SystemExit('invalid enrichment hierarchy')

con=sqlite3.connect(DB); cur=con.cursor()
required={'developer_profiles','developer_dilutions','developer_profile_sources','developer_field_provenance'}
tables={r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
if not required.issubset(tables): raise SystemExit('base enriched profile tables missing')

canonical={norm(name):(name,dn) for name,dn in cur.execute('SELECT name,norm_name FROM developers')}
profile_columns={
 'manufacturer':'manufacturer','productName':'product_name','physicalState':'physical_state',
 'preparation':'preparation','reuseMode':'reuse_mode','reuseInstructions':'reuse_instructions',
 'capacityText':'capacity_text','shelfLifeUnopened':'shelf_life_unopened',
 'shelfLifeOpened':'shelf_life_opened','shelfLifeStock':'shelf_life_stock',
 'shelfLifeWorking':'shelf_life_working','storageNotes':'storage_notes','exhaustionNotes':'exhaustion_notes'}

matched=0; applied=0; mfr_dils=0; unmatched=[]; preserved=0
for rec in records:
    hit=None
    for candidate in rec.get('matchNames',[]):
        hit=canonical.get(norm(candidate))
        if hit: break
    url=str(rec.get('sourceUrl') or '').strip(); title=str(rec.get('sourceTitle') or '').strip()
    if not hit:
        key=' | '.join(rec.get('matchNames',[])); unmatched.append(key)
        cur.execute('INSERT OR REPLACE INTO developer_enrichment_unmatched VALUES(?,?,?)',(key,url,checked_at))
        continue
    matched+=1; _,dn=hit
    cur.execute('''INSERT OR REPLACE INTO developer_profile_sources
      (developer_norm,source_kind,source_url,source_title,source_date,checked_at) VALUES(?,?,?,?,?,?)''',
      (dn,'MANUFACTURER',url,title,str(rec.get('sourceDate') or ''),checked_at))
    row=cur.execute('SELECT * FROM developer_profiles WHERE developer_norm=?',(dn,)).fetchone()
    names=[d[0] for d in cur.description]; vals=dict(zip(names,row))
    for jkey,col in profile_columns.items():
        value=rec.get(jkey)
        if blank(value): continue
        if not blank(vals.get(col)):
            preserved+=1
            continue
        cur.execute(f'UPDATE developer_profiles SET {col}=?,profile_updated=? WHERE developer_norm=?',(str(value).strip(),checked_at,dn))
        cur.execute('''INSERT OR REPLACE INTO developer_field_provenance
          (developer_norm,field_name,source_kind,source_url,source_title,checked_at) VALUES(?,?,?,?,?,?)''',
          (dn,col,'MANUFACTURER',url,title,checked_at))
        vals[col]=value; applied+=1
    for dil in rec.get('dilutions',[]) or []:
        nd=norm_dilution(dil)
        if not nd: continue
        existing=cur.execute('SELECT source_kind FROM developer_dilutions WHERE developer_norm=? AND dilution_norm=?',(dn,nd)).fetchone()
        if existing:
            if existing[0]=='MDC': preserved+=1
            continue
        cur.execute('''INSERT INTO developer_dilutions
          (developer_norm,dilution,dilution_norm,source_kind,source_url,source_title,verified_at) VALUES(?,?,?,?,?,?,?)''',
          (dn,str(dil),nd,'MANUFACTURER',url,title,checked_at)); mfr_dils+=1

batch_key='manufacturer_batch_'+BATCH.stem
cur.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)',(batch_key,f'matched={matched};fields={applied};dilutions={mfr_dils};unmatched={len(unmatched)}'))
con.commit(); quick=cur.execute('PRAGMA quick_check').fetchone()[0]
con.close()
print(f'batch={BATCH.name}')
print(f'matched={matched}/{len(records)}')
print(f'fields_filled={applied}')
print(f'manufacturer_dilutions_added={mfr_dils}')
print(f'existing_values_preserved={preserved}')
print(f'unmatched={len(unmatched)}')
if unmatched: print('unmatched_names='+'; '.join(unmatched))
print('quick_check='+quick)
if unmatched or quick!='ok': raise SystemExit('manufacturer batch audit failed')
