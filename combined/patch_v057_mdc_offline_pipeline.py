#!/usr/bin/env python3
"""Build a complete, release-gated MDC snapshot for offline use.

The historical builder downloaded developer pages only. Digitaltruth can serve
those pages from a lagging representation, while the public film pages already
contain newer rows. This patch makes both indexes first-class inputs, gives the
current film index priority, and refuses to build when any film page could not
be read. No combination-specific data is embedded here.
"""

from pathlib import Path


BUILDER = Path("assistant/build_mdc_sqlite_asset_v032.py")
source = BUILDER.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.5.7 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


# v0.5.6 carried four source-addressed emergency rows. The new pipeline must
# stand on the public indexes themselves, so remove that supplement entirely.
supplement_start = source.find(
    "# MDC currently serves automation clients a lagging representation"
)
supplement_end_marker = "allrows.extend(verified_rows)\n\n"
supplement_end = source.find(supplement_end_marker, supplement_start)
if supplement_start < 0 or supplement_end < 0:
    raise SystemExit("v0.5.7 manual-supplement removal marker missing")
source = (
    source[:supplement_start]
    + source[supplement_end + len(supplement_end_marker) :]
)

# Developer-filtered pages use the canonical requested seed. Film-filtered
# pages must instead read the developer from each result row.
source = replace_once(
    source,
    "            'developer':requested_dev,",
    "            'developer':requested_dev or clean(cells[1]),",
    "film-page developer parsing",
)

one_marker = "def one(dev):"
film_parser = r'''def parse_film_page(txt,url,requested_film):
    """Parse a film-filtered table whose Film cell uses an HTML rowspan."""
    rows=[]
    for tr in re.findall(r'(?is)<tr[^>]*>(.*?)</tr>',txt):
        raw_cells=re.findall(r'(?is)<t[dh][^>]*>(.*?)</t[dh]>',tr)
        cells=[clean(x) for x in raw_cells]
        if not cells or cells[0].lower()=='film': continue
        if len(cells)>=9:
            film=canonical_film(raw_cells[0],cells[0]) or requested_film
            offset=1
        elif len(cells)>=8:
            # After the first result the filtered Film cell is represented by
            # rowspan and therefore absent from the physical HTML row.
            film=requested_film
            offset=0
        else:
            continue
        iso=parse_iso(cells[offset+2])
        if not film or not cells[offset] or iso<=0: continue
        note_index=offset+7
        devrow=(query_value(raw_cells[note_index],'devrow')
                if len(raw_cells)>note_index else '')
        rows.append({
            'film':film,'developer':cells[offset],
            'dilution':clean(cells[offset+1]),'iso':iso,
            'time35':clean_time(cells[offset+3]),
            'time120':clean_time(cells[offset+4]),
            'timesheet':clean_time(cells[offset+5]),
            'temp':parse_temp(cells[offset+6]),
            'notes':((cells[note_index].strip() + ' ')
                     if len(cells)>note_index else '') +
                    (('[devrow:' + devrow + ']') if devrow else ''),
            'source_url':(('https://www.digitaltruth.com/devchart.php?devrow=' + devrow)
                          if devrow else url)
        })
    return rows

'''
source = replace_once(source, one_marker, film_parser + one_marker, "film-page parser")

guard = """if len(seed)<200 or len(allrows)<3000 or len(failed)>20:
    raise SystemExit(f'Full download incomplete: seed={len(seed)} raw_rows={len(allrows)} failed={len(failed)}')

OUT.parent.mkdir(parents=True,exist_ok=True)"""

pipeline = r"""# Independently crawl every canonical film page. These are the pages shown to
# users by the current Massive Dev Chart and therefore define the release
# snapshot. A failed page blocks the release instead of silently shipping a
# partial database. This index is deliberately sequential and rate-limited:
# Digitaltruth applies a stricter limit to devchart.php than to the developer
# text indexes.
def one_film(film):
    url=('https://www.digitaltruth.com/devchart.php?Developer=&Film=' +
         quote_plus(film) + '&mdc=Search')
    last=''
    for attempt in range(8):
        try:
            txt=fetch(url)
            if not txt or '<html' not in txt.lower():
                raise RuntimeError('invalid HTML response')
            rows=parse_film_page(txt,url,film)
            if film=='Fomapan 100' and len(rows)<100:
                raise RuntimeError(f'Fomapan 100 parser smoke test: only {len(rows)} rows')
            return film,rows,'',url
        except Exception as exc:
            last=repr(exc)
            status=getattr(exc,'code',None)
            if status==429:
                retry_after=getattr(exc,'headers',{}).get('Retry-After','')
                try: wait=float(retry_after)
                except: wait=min(90.0,8.0*(2**attempt))
                print(f'MDC rate limit for {film}: waiting {wait:.0f}s',flush=True)
                time.sleep(wait)
            else:
                time.sleep(min(15.0,1.0*(2**attempt)))
    return film,[],last,url

film_rows=[]; film_failed=[]; empty_films=[]
films_to_fetch=sorted(CANON_FILMS.values())
if 'Fomapan 100' not in films_to_fetch:
    raise SystemExit('Fomapan 100 missing from canonical film index')
films_to_fetch=['Fomapan 100']+[f for f in films_to_fetch if f!='Fomapan 100']
print('MDC film-index cooldown: 30s',flush=True)
time.sleep(30)
for done,film_name in enumerate(films_to_fetch,1):
    film,rows,err,url=one_film(film_name)
    if err:
        film_failed.append((film,err,url))
    elif rows:
        film_rows.extend(rows)
    else:
        empty_films.append(film)
    if done%25==0 or done==len(films_to_fetch):
        print(f'film progress {done}/{len(films_to_fetch)}, current_rows={len(film_rows)}, '
              f'failed={len(film_failed)}, empty={len(empty_films)}',flush=True)
    time.sleep(.8)

if film_failed:
    raise SystemExit('Current film-page acquisition incomplete: ' + repr(film_failed[:10]))
if len(film_rows)<3000:
    raise SystemExit(f'Current film-page coverage too small: {len(film_rows)} rows')

# Canonicalize known developers without discarding a newly published one.
seed_by_norm={norm(name):name for name in seed}
for row in film_rows:
    row['developer']=seed_by_norm.get(norm(row['developer']),row['developer'])

def snapshot_key(row):
    return (norm(row['film']),norm(row['developer']),norm_dilution(row['dilution']),
            row['iso'],row['time35'],row['time120'],row['timesheet'],row['temp'])

# Current film pages win; developer pages and historical mirrors only fill
# tuples not exposed by the current index. Notes are not part of this key so a
# stale duplicate cannot replace the current public row.
merged={}
for row in film_rows:
    merged.setdefault(snapshot_key(row),row)
current_keys=set(merged)
for row in allrows:
    merged.setdefault(snapshot_key(row),row)
allrows=list(merged.values())

if not current_keys.issubset({snapshot_key(row) for row in allrows}):
    raise SystemExit('Internal MDC merge lost current film-page rows')
if len(seed)<200 or len(allrows)<3000 or len(failed)>20:
    raise SystemExit(f'Full download incomplete: seed={len(seed)} raw_rows={len(allrows)} failed={len(failed)}')

print(f'MDC RELEASE SNAPSHOT: film_pages={len(CANON_FILMS)} '
      f'film_rows={len(film_rows)} empty_films={len(empty_films)} '
      f'developer_rows={sum(1 for _ in allrows)} merged_rows={len(allrows)}',flush=True)

OUT.parent.mkdir(parents=True,exist_ok=True)"""

source = replace_once(source, guard, pipeline, "complete film-index pipeline")

meta_marker = """ 'raw_rows':str(len(allrows)),
}"""
meta_replacement = """ 'raw_rows':str(len(allrows)),
 'current_film_pages':str(len(CANON_FILMS)),
 'current_film_rows':str(len(film_rows)),
 'current_film_failed':str(len(film_failed)),
 'current_empty_films':str(len(empty_films)),
 'snapshot_policy':'current film pages first; developer indexes as fallback',
}"""
source = replace_once(source, meta_marker, meta_replacement, "snapshot metadata")

# Newly published developers may legitimately increase the table. Completeness
# is protected by the page/row checks above, not by an obsolete upper bound.
source = replace_once(
    source,
    "180 <= counts['developers'] <= len(seed)",
    "180 <= counts['developers'] <= len(seed) + 50",
    "developer-count upper bound",
)

BUILDER.write_text(source, encoding="utf-8")
print("Darkroom v0.5.7 MDC pipeline: dual index, no manual time rows, gated snapshot")
