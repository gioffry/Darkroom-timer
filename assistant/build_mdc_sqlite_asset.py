#!/usr/bin/env python3
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote_plus
import concurrent.futures, re, html, time, sqlite3, unicodedata
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SEED = ROOT / 'src/main/assets/mdc_developers_seed.txt'
OUT = ROOT / 'src/main/assets/mdc_full.sqlite'

seed = [x.strip() for x in SEED.read_text(encoding='utf-8').splitlines() if x.strip()]
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'

def fetch(url):
    req=Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml','Accept-Language':'en-US,en;q=0.8','Referer':'https://www.digitaltruth.com/'})
    with urlopen(req,timeout=35) as r:
        return r.read(2500000).decode('utf-8','ignore')

def clean(x):
    x=re.sub(r'(?is)<script.*?</script>',' ',x)
    x=re.sub(r'(?is)<style.*?</style>',' ',x)
    x=re.sub(r'(?is)<[^>]+>',' ',x)
    return ' '.join(html.unescape(x).replace('\xa0',' ').split())

def norm(s):
    s=(s or '').lower().replace('–',' ').replace('—',' ').replace('-',' ')
    s=unicodedata.normalize('NFKC',s)
    s=re.sub(r'[^\w+]+',' ',s,flags=re.UNICODE)
    return ' '.join(s.split())

def norm_dilution(s):
    s=clean(s or '').strip()
    if s.lower()=='stock': return 'stock'
    s=s.replace(':','+').replace(' ','')
    return s.lower()

def parse_iso(s):
    m=re.sub(r'\D','',s or '')
    return int(m) if m else 0

def parse_temp(s):
    t=(s or '').upper().replace('°','').replace('C','').replace(',','.')
    t=re.sub(r'[^0-9.]','',t)
    try: return float(t)
    except: return 20.0

def clean_time(s):
    return ''.join((s or '').replace('\xa0',' ').split())

def parse(txt,url):
    rows=[]
    for tr in re.findall(r'(?is)<tr[^>]*>(.*?)</tr>',txt):
        cells=[clean(x) for x in re.findall(r'(?is)<t[dh][^>]*>(.*?)</t[dh]>',tr)]
        if len(cells)<8: continue
        if cells[0].lower()=='film' or cells[1].lower()=='developer': continue
        film=cells[0].strip(); dev=cells[1].strip(); iso=parse_iso(cells[3])
        if not film or not dev or iso<=0: continue
        rows.append({
            'film':film,'developer':dev,'dilution':clean(cells[2]),'iso':iso,
            'time35':clean_time(cells[4]),'time120':clean_time(cells[5]),
            'timesheet':clean_time(cells[6]),'temp':parse_temp(cells[7]),
            'notes':cells[8].strip() if len(cells)>8 else '', 'source_url':url
        })
    return rows

def one(dev):
    enc=quote_plus(dev)
    urls=[f'https://ftp.digitaltruth.com/chart/search_text.php?Developer={enc}',
          f'https://www.digitaltruth.com/chart/search_text.php?Developer={enc}']
    last=''
    for url in urls:
        for attempt in range(3):
            try:
                rows=parse(fetch(url),url)
                if rows: return dev,rows,''
                last='no rows'
            except Exception as e:
                last=repr(e)
            time.sleep(.15*(attempt+1))
    return dev,[],last

allrows=[]; failed=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    futs={ex.submit(one,d):d for d in seed}
    done=0
    for f in concurrent.futures.as_completed(futs):
        dev,rows,err=f.result(); done+=1
        if rows: allrows.extend(rows)
        else: failed.append((dev,err))
        if done%20==0 or done==len(seed):
            print(f'progress {done}/{len(seed)} developers, raw_rows={len(allrows)}, failed={len(failed)}',flush=True)

if len(seed)<200 or len(allrows)<3000 or len(failed)>10:
    raise SystemExit(f'Full download incomplete: seed={len(seed)} raw_rows={len(allrows)} failed={len(failed)}')

OUT.parent.mkdir(parents=True,exist_ok=True)
if OUT.exists(): OUT.unlink()
con=sqlite3.connect(OUT)
cur=con.cursor()
cur.executescript('''
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=OFF;
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE films(name TEXT NOT NULL,norm_name TEXT PRIMARY KEY);
CREATE TABLE developers(name TEXT NOT NULL,norm_name TEXT PRIMARY KEY);
CREATE TABLE times(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 film TEXT NOT NULL,film_norm TEXT NOT NULL,
 developer TEXT NOT NULL,developer_norm TEXT NOT NULL,
 dilution TEXT,dilution_norm TEXT,iso INTEGER,
 time35 TEXT,time120 TEXT,timesheet TEXT,temp REAL,notes TEXT,source_url TEXT,
 UNIQUE(film_norm,developer_norm,dilution_norm,iso,time35,time120,timesheet,temp,notes)
);
CREATE INDEX idx_times_lookup ON times(film_norm,developer_norm,dilution_norm,iso);
CREATE INDEX idx_film_search ON films(norm_name);
CREATE INDEX idx_dev_search ON developers(norm_name);
''')
films={}; devs={}
for r in allrows:
    fn=norm(r['film']); dn=norm(r['developer']); diln=norm_dilution(r['dilution'])
    films.setdefault(fn,r['film']); devs.setdefault(dn,r['developer'])
    cur.execute('''INSERT OR IGNORE INTO times
      (film,film_norm,developer,developer_norm,dilution,dilution_norm,iso,time35,time120,timesheet,temp,notes,source_url)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
      (r['film'],fn,r['developer'],dn,r['dilution'],diln,r['iso'],r['time35'],r['time120'],r['timesheet'],r['temp'],r['notes'],r['source_url']))
for n,name in films.items(): cur.execute('INSERT OR IGNORE INTO films(name,norm_name) VALUES(?,?)',(name,n))
for n,name in devs.items(): cur.execute('INSERT OR IGNORE INTO developers(name,norm_name) VALUES(?,?)',(name,n))
meta={
 'last_sync':datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
 'source':'Massive Dev Chart / Digitaltruth',
 'seed_count':str(len(seed)),
 'failed_pages':str(len(failed)),
 'raw_rows':str(len(allrows)),
}
for k,v in meta.items(): cur.execute('INSERT INTO meta(key,value) VALUES(?,?)',(k,v))
cur.execute('PRAGMA user_version=1')
con.commit()
counts={
 'rows':cur.execute('SELECT COUNT(*) FROM times').fetchone()[0],
 'films':cur.execute('SELECT COUNT(*) FROM films').fetchone()[0],
 'developers':cur.execute('SELECT COUNT(*) FROM developers').fetchone()[0],
}
quick=cur.execute('PRAGMA quick_check').fetchone()[0]
con.close()
print(f"BUILT SQLITE: films={counts['films']} developers={counts['developers']} rows={counts['rows']} failed={len(failed)} quick_check={quick} size={OUT.stat().st_size}")
if counts['developers']<180 or counts['films']<250 or counts['rows']<3000 or quick!='ok':
    raise SystemExit('SQLite completeness/integrity check failed')
