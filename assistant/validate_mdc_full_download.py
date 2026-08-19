#!/usr/bin/env python3
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote_plus
import concurrent.futures, re, html, sys, time

seed = [x.strip() for x in Path('assistant/src/main/assets/mdc_developers_seed.txt').read_text(encoding='utf-8').splitlines() if x.strip()]
UA='Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36'

def fetch(url):
    req=Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml','Referer':'https://www.digitaltruth.com/'})
    with urlopen(req,timeout=30) as r:
        return r.read(2500000).decode('utf-8','ignore')

def clean(x):
    x=re.sub(r'(?is)<[^>]+>',' ',x)
    return ' '.join(html.unescape(x).replace('\xa0',' ').split())

def parse(txt):
    rows=[]
    for tr in re.findall(r'(?is)<tr[^>]*>(.*?)</tr>',txt):
        cells=[clean(x) for x in re.findall(r'(?is)<t[dh][^>]*>(.*?)</t[dh]>',tr)]
        if len(cells)<8: continue
        if cells[0].lower()=='film' or cells[1].lower()=='developer': continue
        iso=re.sub(r'\D','',cells[3])
        if not cells[0] or not cells[1] or not iso: continue
        rows.append(cells[:9])
    return rows

def one(dev):
    enc=quote_plus(dev)
    urls=[f'https://ftp.digitaltruth.com/chart/search_text.php?Developer={enc}',
          f'https://www.digitaltruth.com/chart/search_text.php?Developer={enc}']
    last=''
    for url in urls:
        for attempt in range(2):
            try:
                rows=parse(fetch(url))
                if rows: return dev, rows, url, ''
                last='no rows'
            except Exception as e:
                last=repr(e)
            time.sleep(.12*(attempt+1))
    return dev, [], '', last

allrows=[]; failed=[]; films=set(); devs=set()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    futs={ex.submit(one,d):d for d in seed}
    done=0
    for f in concurrent.futures.as_completed(futs):
        dev,rows,url,err=f.result(); done+=1
        if rows:
            allrows.extend(rows); devs.add(dev)
            films.update(r[0] for r in rows)
        else: failed.append((dev,err))
        if done%20==0 or done==len(seed):
            print(f'progress {done}/{len(seed)} developers, rows={len(allrows)}, films={len(films)}, failed={len(failed)}',flush=True)

print(f'FULL DOWNLOAD CHECK: seed={len(seed)} developer_pages_with_rows={len(devs)} films={len(films)} rows={len(allrows)} failed={len(failed)}')
if failed:
    print('FAILED SAMPLE:', failed[:20])

# Guardrails: this validates the complete-download mechanism without packaging/re-publishing the third-party dataset.
if len(seed) < 200 or len(devs) < 180 or len(films) < 250 or len(allrows) < 3000:
    raise SystemExit('Digitaltruth full-download validation did not reach completeness thresholds')
