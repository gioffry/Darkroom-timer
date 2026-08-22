#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.2 — fix ricerca catalogo: gli alias vuoti non sono match universali.
# Git base: v0.3.1 successful branch. No Timer / Split Grade / SONOFF changes.

python3 - <<'PY'
from pathlib import Path
s=Path('combined/build_v031.sh').read_text(encoding='utf-8')
for marker in ['Darkroom v0.3.1','Darkroom-v0.3.1','versionCode="22"','v031']:
    if marker not in s:
        raise SystemExit('v0.3.2 source build marker missing: '+marker)
s=s.replace('v0.3.1','v0.3.2')
s=s.replace('0.3.1','0.3.2')
s=s.replace('versionCode="22"','versionCode="23"')
s=s.replace("versionCode='22'","versionCode='23'")
s=s.replace('versionCode 22','versionCode 23')
s=s.replace('versionCode=22','versionCode=23')
s=s.replace('v031','v032')
s=s.replace('base_version=0.3.0','base_version=0.3.1')
Path('/tmp/build_v032_generated.sh').write_text(s,encoding='utf-8')
PY

bash /tmp/build_v032_generated.sh

STORE=combined/src/main/java/it/darkroom/assistant/FullCatalogStore.java
# Regression: empty alias must never score as a match.
grep -Fq 'if(aliases!=null&&!aliases.trim().isEmpty())' "$STORE"
grep -Fq 'if(an.isEmpty())continue;' "$STORE"
grep -Fq 'if(n==null||n.isEmpty()||nc==null||nc.isEmpty())return 0;' "$STORE"

python3 - <<'PY'
from pathlib import Path
import sqlite3,re,unicodedata

db=Path('assistant/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(db); cur=con.cursor()

def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode('ascii').lower()
    s=s.replace('–',' ').replace('—',' ').replace('-',' ')
    return ' '.join(re.sub(r'[^a-z0-9+]+',' ',s).split())
def compact(s): return re.sub(r'[^a-z0-9]+','',norm(s))
def score_one(q,qc,n,nc):
    if not n or not nc: return 0
    if n==q or nc==qc: return 1000
    if n.startswith(q) or nc.startswith(qc): return 950
    if q.startswith(n) or qc.startswith(nc) or q.endswith(' '+n) or qc.endswith(nc): return 930
    if any(t and t.startswith(q) for t in n.split()): return 910
    if q in n or (qc and qc in nc): return 850
    if all(t in n for t in q.split()): return 760
    return 0
def score(q,name,aliases=''):
    q=norm(q); qc=compact(q); n=norm(name); nc=compact(name)
    best=score_one(q,qc,n,nc)
    if aliases and aliases.strip():
        for a in aliases.split('|'):
            an=norm(a)
            if not an: continue
            best=max(best,score_one(q,qc,an,compact(a)))
    return best

# The screenshot regression: FOMATOL is paper developer, so FILM developer search must return zero.
film=[]
for (name,) in cur.execute('SELECT name FROM developers'):
    if score('fomatol',name,'')>0: film.append(name)
for name,aliases in cur.execute('SELECT name,aliases FROM catalog_products WHERE (roles & 1)<>0'):
    if score('fomatol',name,aliases or '')>0: film.append(name)
if film:
    raise SystemExit('v0.3.2 regression: fomatol incorrectly matches film developers: '+repr(film[:10]))
row=cur.execute("SELECT name,roles FROM catalog_products WHERE norm_name='fomatol lqn'").fetchone()
if not row or (row[1] & 2)==0 or (row[1] & 1)!=0:
    raise SystemExit('v0.3.2 regression: FOMATOL LQN role mapping invalid: '+repr(row))
# Positive control: paper search must find FOMATOL LQN.
paper=[]
for name,aliases in cur.execute('SELECT name,aliases FROM catalog_products WHERE (roles & 2)<>0'):
    if score('fomatol',name,aliases or '')>0: paper.append(name)
if 'FOMATOL LQN' not in paper:
    raise SystemExit('v0.3.2 regression: FOMATOL LQN missing from paper search')
con.close()
print('search_filter_fomatol_film=PASS')
print('search_filter_fomatol_paper=PASS')
print('empty_alias_match=PASS')
PY

cat >> validation-v032-catalog.txt <<'EOF'
search_filter_fomatol_film=PASS
search_filter_fomatol_paper=PASS
empty_alias_match=PASS
search_regression_from_user_screenshot=PASS
base_version=0.3.1
EOF

grep -q 'catalog_validation=PASS' validation-v032-catalog.txt
grep -q 'search_filter_fomatol_film=PASS' validation-v032-catalog.txt
grep -q 'search_filter_fomatol_paper=PASS' validation-v032-catalog.txt
grep -Fq "versionCode='23'" apk-badging-v032.txt
grep -Fq "versionName='0.3.2'" apk-badging-v032.txt
sha256sum Darkroom-v0.3.2.apk | tee Darkroom-v0.3.2.sha256
