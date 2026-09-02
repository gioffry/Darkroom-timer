#!/usr/bin/env python3
"""Build a complete, release-gated MDC snapshot for offline use.

The historical builder downloaded developer pages only. Digitaltruth can serve
those pages from a lagging representation, while the public film pages already
contain newer rows. This patch makes both indexes first-class inputs, gives the
current film index priority, preserves source-addressed verified rows when the
public and automation-facing views differ, and refuses incomplete releases.
"""

from pathlib import Path


BUILDER = Path("assistant/build_mdc_sqlite_asset_v032.py")
source = BUILDER.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v0.5.7 {label}: expected one marker, found {count}")
    return text.replace(old, new, 1)


# Preserve v0.5.6's small source-addressed supplement. MDC's public chart and
# automation-facing endpoints can expose different revisions; these rows have
# stable devrow URLs and are data, not runtime exceptions. The final release
# tests below still verify the resulting offline database independently.
if "allrows.extend(verified_rows)" not in source:
    raise SystemExit("v0.5.7 verified MDC supplement missing")

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
    """Parse Digitaltruth's stable row-oriented text index for one film."""
    rows=parse(txt,url,'')
    wanted=norm(requested_film)
    return [row for row in rows if norm(row['film'])==wanted]

'''
source = replace_once(source, one_marker, film_parser + one_marker, "film-page parser")

guard = """allrows.extend(verified_rows)

OUT.parent.mkdir(parents=True,exist_ok=True)"""

pipeline = r"""allrows.extend(verified_rows)

# Independently crawl every canonical film page. These are the pages shown to
# users by the current Massive Dev Chart and therefore define the release
# snapshot. A failed page blocks the release instead of silently shipping a
# partial database. This index is deliberately sequential and rate-limited:
# The film and developer indexes share the stable row-oriented endpoint.
def one_film(film):
    url=('https://www.digitaltruth.com/chart/search_text.php?Film=' +
         quote_plus(film))
    last=''
    for attempt in range(8):
        try:
            txt=fetch(url)
            if not txt or '<html' not in txt.lower():
                raise RuntimeError('invalid HTML response')
            rows=parse_film_page(txt,url,film)
            if film=='Fomapan 100':
                keys={(norm(r['developer']),norm_dilution(r['dilution']),r['iso'],
                       r['time35'],r['time120'],r['timesheet'],r['temp']) for r in rows}
                required={
                    ('fx 39','1+9',100,'7','7','7',20.0),
                    ('d 76','1+1',100,'10','10','10',20.0),
                    ('fomadon excel','1+1',100,'8-9','8-9','8-9',20.0),
                }
                missing=required-keys
                if len(rows)<100 or missing:
                    raise SystemExit(
                        f'Fomapan 100 current-page smoke test failed: '
                        f'rows={len(rows)} missing={sorted(missing)}')
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
 'snapshot_policy':'current film pages first; developer indexes and source-addressed verified rows as fallback',
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
print("Darkroom v0.5.7 MDC pipeline: dual index, source-addressed verification, gated snapshot")
