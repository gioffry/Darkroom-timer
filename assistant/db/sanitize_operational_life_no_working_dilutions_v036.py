#!/usr/bin/env python3
from pathlib import Path
import hashlib, sqlite3, sys

DB=Path(sys.argv[1]) if len(sys.argv)>1 else Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(DB); cur=con.cursor()
PROTECTED=('films','developers','times','developer_dilutions')

def fp(table):
    h=hashlib.sha256(); cols=[r[1] for r in cur.execute(f'pragma table_info({table})')]
    order=','.join('"'+c+'"' for c in cols)
    for row in cur.execute(f'select * from {table} order by {order}'):
        h.update(repr(tuple(row)).encode()); h.update(b'\n')
    return h.hexdigest()

before={t:fp(t) for t in PROTECTED}

# Operational expiration must describe only the stored concentrate/stock.
# Working dilutions belong to the technical card, never to expiration.
cur.execute("""
UPDATE auxiliary_chemical_profiles
SET operational_life_it='Concentrato aperto: conservare in bottiglia piena e ben chiusa. La documentazione FOMA disponibile non indica un intervallo numerico separato dopo l’apertura.'
WHERE norm_name='fomafix'
""")
con.commit()

for table in ('developer_profiles','auxiliary_chemical_profiles'):
    bad=cur.execute(f"select count(*) from {table} where coalesce(operational_life_it,'') glob '*1+*'").fetchone()[0]
    if bad:
        rows=cur.execute(f"select * from {table} where coalesce(operational_life_it,'') glob '*1+*'").fetchall()
        raise SystemExit(f'working dilution leaked into operational life: {table} {rows}')

after={t:fp(t) for t in PROTECTED}
for t in PROTECTED:
    if before[t]!=after[t]: raise SystemExit(f'protected MDC changed: {t}')

print('operational_working_dilution_references=0')
print('fomafix_operational_life_1plusX_removed=PASS')
for t in PROTECTED: print(f'protected_{t}_unchanged_after_operational_sanitize=PASS')
con.close()
