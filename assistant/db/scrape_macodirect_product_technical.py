#!/usr/bin/env python3
from pathlib import Path
import json,re,time,unicodedata
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

SNAP=Path("assistant/db/snapshots/macodirect-2026-09-28/catalog_proposal.json")
OUT=Path("build-output/macodirect-technical")
OUT.mkdir(parents=True,exist_ok=True)
rows=json.loads(SNAP.read_text(encoding="utf-8"))

session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 DarkroomCatalogAudit/1.0"})

def clean(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()

def normkey(s):
    s=unicodedata.normalize("NFKD",clean(s)).encode("ascii","ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

def get_props(html):
    soup=BeautifulSoup(html,"html.parser")
    props={}
    # Shopware product property tables and generic tables.
    for tr in soup.find_all("tr"):
        cells=tr.find_all(["th","td"])
        if len(cells)>=2:
            k=clean(cells[0].get_text(" ",strip=True))
            v=clean(cells[1].get_text(" ",strip=True))
            if k and v and len(k)<120 and len(v)<800:
                props.setdefault(k,v)
    # Some Shopware themes render properties as div rows.
    for row in soup.select(".product--properties-row, .product-detail-properties-table-row, .product-detail-properties-row"):
        kids=[clean(x.get_text(" ",strip=True)) for x in row.find_all(recursive=False)]
        kids=[x for x in kids if x]
        if len(kids)>=2:
            props.setdefault(kids[0],kids[1])
    # Last fallback: dt/dd pairs.
    dts=soup.find_all("dt")
    for dt in dts:
        dd=dt.find_next_sibling("dd")
        if dd:
            k=clean(dt.get_text(" ",strip=True)); v=clean(dd.get_text(" ",strip=True))
            if k and v: props.setdefault(k,v)
    desc=""
    for sel in [".product--description", ".product-detail-description-text", ".product-detail-description"]:
        el=soup.select_one(sel)
        if el:
            desc=clean(el.get_text(" ",strip=True))
            if desc: break
    return props,desc

# Crawl every processing chemical that can appear in a functional bath selector.
# Pure film stocks and generic kits/accessories are intentionally excluded here.
targets=[r for r in rows if r.get("kind")=="chemical" and r.get("source_url")
         and (int(r.get("roles",0)) & (1|2|4|8|16|32)) != 0]

def fetch_one(r):
    url=r["source_url"]
    local=requests.Session()
    local.headers.update({"User-Agent":"Mozilla/5.0 DarkroomCatalogAudit/1.0"})
    try:
        resp=local.get(url,timeout=10)
        status=resp.status_code
        props,desc=get_props(resp.text) if status==200 else ({}, "")
        err=""
    except Exception as e:
        status=0; props={}; desc=""; err=type(e).__name__+":"+str(e)
    return {
      "id":r["id"],"name":r["name"],"roles":r["roles"],"url":url,
      "status":status,"properties":props,"description":desc,"error":err
    }

out=[]
with ThreadPoolExecutor(max_workers=12) as ex:
    futures={ex.submit(fetch_one,r):r for r in targets}
    done=0
    for fut in as_completed(futures):
        rec=fut.result(); out.append(rec); done+=1
        props=rec["properties"]
        keys={normkey(k):v for k,v in props.items()}
        dilution=next((v for k,v in keys.items() if "dilution" in k or "verdunnung" in k), "")
        state=next((v for k,v in keys.items() if k in ("type","verarbeitungszustand","processing state")), "")
        if dilution or state:
            print(f"{done:03d}/{len(targets)} {rec['name']} | state={state} | dilution={dilution}")
out.sort(key=lambda x:x["name"].lower())

(OUT/"macodirect_technical.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
summary={
 "targets":len(targets),
 "http_200":sum(1 for x in out if x["status"]==200),
 "with_properties":sum(1 for x in out if x["properties"]),
 "with_dilution":sum(1 for x in out if any("dilution" in normkey(k) or "verdunnung" in normkey(k) for k in x["properties"])),
}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
