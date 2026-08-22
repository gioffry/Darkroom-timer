#!/usr/bin/env python3
from pathlib import Path
import sqlite3, re, unicodedata

DB=Path('assistant/src/main/assets/mdc_full.sqlite')
OUT=Path('validation-v029-catalog.txt')
if not DB.exists(): raise SystemExit('v029 validation: DB missing')

def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode('ascii').lower()
    s=s.replace('–',' ').replace('—',' ').replace('-',' ')
    return ' '.join(re.sub(r'[^a-z0-9+]+',' ',s).split())
def compact(s): return re.sub(r'[^a-z0-9]+','',norm(s))

def score(q,name):
    qn,n=norm(q),norm(name); qc,nc=compact(q),compact(name)
    if qn==n or qc==nc: return 1000
    if n.startswith(qn) or nc.startswith(qc): return 950
    if qn.startswith(n) or qc.startswith(nc) or qn.endswith(' '+n) or qc.endswith(nc): return 930
    if qn in n or (qc and qc in nc): return 850
    qt=qn.split()
    if qt and all(t in n for t in qt): return 760
    return 0

def best_name(q,names):
    pairs=sorted(((score(q,n),n) for n in names),reverse=True)
    return pairs[0][1] if pairs and pairs[0][0]>=620 else None

con=sqlite3.connect(DB); cur=con.cursor()
quick=cur.execute('PRAGMA quick_check').fetchone()[0]
uv=cur.execute('PRAGMA user_version').fetchone()[0]
counts={
 'films':cur.execute('SELECT COUNT(*) FROM films').fetchone()[0],
 'developers':cur.execute('SELECT COUNT(*) FROM developers').fetchone()[0],
 'combinations':cur.execute('SELECT COUNT(*) FROM times').fetchone()[0],
 'catalog_products':cur.execute('SELECT COUNT(*) FROM catalog_products').fetchone()[0],
 'catalog_aliases':cur.execute('SELECT COUNT(*) FROM catalog_aliases').fetchone()[0],
}
film_names=[r[0] for r in cur.execute('SELECT name FROM films')]
dev_names=[r[0] for r in cur.execute('SELECT name FROM developers')]
local_names=[r[0] for r in cur.execute('SELECT name FROM catalog_products')]
alias_rows=list(cur.execute('SELECT p.name,a.alias FROM catalog_aliases a JOIN catalog_products p ON p.id=a.product_id'))
search_names=dev_names+local_names+[a for _,a in alias_rows]

errors=[]
def require(cond,msg):
    if not cond: errors.append(msg)

require(quick=='ok','PRAGMA quick_check != ok')
require(uv==3,f'user_version expected 3 got {uv}')
require(counts['films']>=250,f"films too few: {counts['films']}")
require(counts['developers']>=180,f"developers too few: {counts['developers']}")
require(counts['combinations']>=3000,f"MDC combinations too few: {counts['combinations']}")
require(counts['catalog_products']>=20,f"local products too few: {counts['catalog_products']}")

film_tests=['Fomapan 100','Fomapan 200','Fomapan 400','Ilford FP4 Plus','Ilford HP5 Plus','Kodak Tri-X 400','Kodak T-Max 100','Kodak T-Max 400']
resolved_films={q:best_name(q,film_names+local_names+[a for _,a in alias_rows]) for q in film_tests}
for q,v in resolved_films.items(): require(v is not None,'film search missing: '+q)

dev_tests=['Kodak D-76','Kodak XTOL','Ilford ID-11','Ilford DD-X','Rodinal','Adox Rodinal','Fomadon Excel','Fomadon P','Fomadon R09']
resolved_devs={q:best_name(q,search_names) for q in dev_tests}
for q,v in resolved_devs.items(): require(v is not None,'developer search missing: '+q)

alias_tests={'d76':'Kodak D-76','xtol':'Kodak XTOL','hp5':'Ilford HP5 Plus','foma 200':'Fomapan 200','trix':'Kodak Tri-X 400'}
for q,target in alias_tests.items():
    hit=best_name(q,search_names+film_names)
    require(hit is not None, f'alias search missing: {q}')

row=cur.execute("SELECT manufacturer,categories,physical_state,paper_dilutions,source_url,roles FROM catalog_products WHERE norm_name=?",(norm('FOMATOL LQN'),)).fetchone()
require(row is not None,'FOMATOL LQN missing')
if row:
    manufacturer,cats,state,pd,src,roles=row
    require(norm(manufacturer)=='foma','FOMATOL LQN manufacturer not FOMA')
    require('PAPER_DEVELOPER' in (cats or ''),'FOMATOL LQN PAPER_DEVELOPER missing')
    require('liquid' in norm(state) or 'liquido' in norm(state),'FOMATOL LQN liquid state missing')
    require('1+7' in (pd or ''),'FOMATOL LQN paper dilution 1+7 missing')
    require('foma.cz' in (src or ''),'FOMATOL LQN official Foma source missing')
    require((roles & 2)!=0,'FOMATOL LQN role bit missing')

required_foma=['FOMADON Excel','FOMADON P','FOMADON LQN','FOMADON R09','FOMA Universal','FOMATOL LQN','FOMATOL P','FOMATOL PW','FOMACITRO','FOMAFIX','FOTONAL']
for name in required_foma:
    require(cur.execute('SELECT 1 FROM catalog_products WHERE norm_name=?',(norm(name),)).fetchone() is not None,'required Foma product missing: '+name)

coverage=[]
for query in ['Fomapan 100','Fomapan 200','Ilford HP5 Plus','Ilford FP4 Plus','Kodak Tri-X 400']:
    canon=best_name(query,film_names)
    if not canon: continue
    fn=norm(canon)
    dcount=cur.execute('SELECT COUNT(DISTINCT developer_norm) FROM times WHERE film_norm=?',(fn,)).fetchone()[0]
    dilcount=cur.execute("SELECT COUNT(DISTINCT dilution_norm) FROM times WHERE film_norm=? AND dilution_norm<>''",(fn,)).fetchone()[0]
    coverage.append((canon,dcount,dilcount))
require(sum(1 for _,d,di in coverage if d>=2 and di>=2)>=3,'insufficient multi-developer/multi-dilution film coverage')

dups=cur.execute('SELECT norm_name,COUNT(*) FROM catalog_products GROUP BY norm_name HAVING COUNT(*)>1').fetchall()
require(not dups,'duplicate local canonical products: '+repr(dups[:5]))

unique=set(norm(x) for x in film_names+dev_names+local_names if x)
lines=[
 'catalog_validation=PASS' if not errors else 'catalog_validation=FAIL',
 f"sqlite_user_version={uv}",f"sqlite_quick_check={quick}",
 f"total_products_indexed={len(unique)}",
 f"total_films={counts['films']}",f"total_film_developers={counts['developers']}",
 f"total_mdc_combinations={counts['combinations']}",f"local_technical_products={counts['catalog_products']}",
 f"alias_entries={counts['catalog_aliases']}",
 'offline_mode=FULL_BUNDLED_SQLITE',
 'sources=Massive Dev Chart / Digitaltruth + verified manufacturer catalog-v2',
 'fomatol_lqn=PASS' if row and '1+7' in (row[3] or '') else 'fomatol_lqn=FAIL',
]
for canon,d,di in coverage: lines.append(f"coverage::{canon}::developers={d}::dilutions={di}")
for q,v in resolved_films.items(): lines.append(f"film_test::{q}::{v or 'MISS'}")
for q,v in resolved_devs.items(): lines.append(f"developer_test::{q}::{v or 'MISS'}")
if errors: lines += ['ERROR::'+e for e in errors]
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
con.close()
print('\n'.join(lines))
if errors: raise SystemExit('v029 catalog validation failed: '+'; '.join(errors))
