#!/usr/bin/env python3
from pathlib import Path
import ast, hashlib, re, sqlite3, sys

DB=Path(sys.argv[1]) if len(sys.argv)>1 else Path('combined/src/main/assets/mdc_full.sqlite')
source=Path('assistant/db/complete_italian_preparations_v035.py').read_text(encoding='utf-8')
tree=ast.parse(source)
P=None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='P' for t in node.targets):
        P=ast.literal_eval(node.value); break
if P is None: raise SystemExit('preparation translation dictionary missing')
# Avoid English generic words even when an official product name contained them.
P['ilfotec dd']='Diluire ILFOTEC DD 1+4 e usare con ILFOTEC DD Starter seguendo le istruzioni del processo con reintegro.'
P['tmax rs']='Preparare la soluzione alla concentrazione di lavoro secondo il formato della confezione. Kodak indica che T-MAX RS produce una soluzione di lavoro utilizzata anche come reintegratore.'

con=sqlite3.connect(DB); cur=con.cursor()
PROTECTED=('films','developers','times','developer_dilutions')
def fp(table):
    h=hashlib.sha256(); cols=[r[1] for r in cur.execute(f'PRAGMA table_info({table})')]
    order=','.join('"'+c+'"' for c in cols)
    for row in cur.execute(f'SELECT * FROM {table} ORDER BY {order}'):
        h.update(repr(tuple(row)).encode()); h.update(b'\n')
    return h.hexdigest()
before={t:fp(t) for t in PROTECTED}
for dn,text in P.items():
    cur.execute('UPDATE developer_profiles SET preparation_it=?,translation_status=? WHERE developer_norm=?',(text,'v035_strict_it_complete_prep',dn))
con.commit()

raw_count=cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(preparation,'')<>''").fetchone()[0]
it_count=cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(preparation_it,'')<>''").fetchone()[0]
if raw_count!=79 or it_count!=79:
    missing=cur.execute("SELECT developer_norm,developer_name FROM developer_profiles WHERE COALESCE(preparation,'')<>'' AND COALESCE(preparation_it,'')='' ORDER BY developer_name").fetchall()
    raise SystemExit(f'Italian preparation coverage mismatch raw={raw_count} it={it_count} missing={missing}')
bad=re.compile(r'\b(the|and|with|when|should|stored|working solution|original package|minimum|defines|processing|explicitly|before|protected|darkness|oxidation|later use|replace|guaranteed|direct sun|air access|unopened|opened concentrate|prepared|manufacturer states|depending on|once opened|use once|discard|per litre|per liter|rolls|sheets|developer|full tightly|half full)\b',re.I)
for dn,v in cur.execute("SELECT developer_norm,preparation_it FROM developer_profiles WHERE COALESCE(preparation_it,'')<>''"):
    if bad.search(v) or '\\n' in v:
        raise SystemExit(f'Bad Italian preparation {dn}: {v}')
after={t:fp(t) for t in PROTECTED}
for t in PROTECTED:
    if before[t]!=after[t]: raise SystemExit(f'protected MDC changed: {t}')
print('developer_preparation_raw=79')
print('developer_preparation_clean_italian=79')
print('preparation_translation_coverage=79/79')
print('preparation_literal_backslash_n=0')
for t in PROTECTED: print(f'protected_{t}_unchanged_after_preparation_completion=PASS')
con.close()
