#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sqlite3,sys
DB=Path(sys.argv[1]) if len(sys.argv)>1 else Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(DB); cur=con.cursor()
PROTECTED=('films','developers','times','developer_dilutions')
def fp(t):
    h=hashlib.sha256(); cols=[r[1] for r in cur.execute(f'pragma table_info({t})')]
    order=','.join('"'+c+'"' for c in cols)
    for row in cur.execute(f'select * from {t} order by {order}'):
        h.update(repr(tuple(row)).encode()); h.update(b'\n')
    return h.hexdigest()
before={t:fp(t) for t in PROTECTED}

def full_only(v):
    if not v: return v
    s=' '.join(str(v).split())
    # Italian overlay texts put the full-bottle condition first. Drop all
    # alternatives for half-full / partially full containers.
    s=re.split(r';\s*(?=(?:\d|contenitore|bottiglia|a metà|metà))',s,maxsplit=1,flags=re.I)[0]
    s=re.split(r'\s+oppure\s+(?=\d)',s,maxsplit=1,flags=re.I)[0]
    s=re.split(r'\s*/\s*(?=\d+\s*(?:mesi|mese|giorni|ore))',s,maxsplit=1,flags=re.I)[0]
    return s.strip()

for table,key in [('developer_profiles','developer_norm'),('auxiliary_chemical_profiles','norm_name')]:
    rows=cur.execute(f"select {key},operational_life_it from {table} where coalesce(operational_life_it,'')<>''").fetchall()
    for k,v in rows:
        cur.execute(f'update {table} set operational_life_it=? where {key}=?',(full_only(v),k))
con.commit()

# The operational UI is full-bottle only: no half-bottle alternative may leak.
for table in ('developer_profiles','auxiliary_chemical_profiles'):
    bad=cur.execute(f"""select count(*) from {table} where lower(coalesce(operational_life_it,'')) like '%metà bottiglia%'
        or lower(coalesce(operational_life_it,'')) like '%half full%'
        or lower(coalesce(operational_life_it,'')) like '%half-full%'""").fetchone()[0]
    assert bad==0,(table,bad)
    badcond=cur.execute(f"select count(*) from {table} where coalesce(operational_life_it,'')<>'' and operational_life_condition_it!='bottiglia piena e ben chiusa, con minimo volume d’aria'").fetchone()[0]
    assert badcond==0,(table,badcond)

after={t:fp(t) for t in PROTECTED}
for t in PROTECTED:
    assert before[t]==after[t],f'protected MDC changed: {t}'
print('operational_condition=FULL_BOTTLE_ONLY')
print('half_bottle_alternatives_visible=0')
for t in PROTECTED: print(f'protected_{t}_unchanged_full_bottle_normalization=PASS')
con.close()
