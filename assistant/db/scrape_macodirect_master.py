#!/usr/bin/env python3
from pathlib import Path
import csv, json, re, sqlite3, sys, time, unicodedata
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE="https://www.macodirect.de"
CATEGORIES=[
    ("bw_film",128,"https://www.macodirect.de/en/film/black-white-films/"),
    ("film_developer",1,"https://www.macodirect.de/en/chemistry/black-white-chemistry/film-developing/film-developer/"),
    ("paper_developer",2,"https://www.macodirect.de/en/chemistry/black-white-chemistry/paper-developing/paper-developer/"),
    ("film_stop",4,"https://www.macodirect.de/en/chemistry/black-white-chemistry/film-developing/stop-bath/"),
    ("paper_stop",4,"https://www.macodirect.de/en/chemistry/black-white-chemistry/paper-developing/stop-bath/"),
    ("film_fixer",8,"https://www.macodirect.de/en/chemistry/black-white-chemistry/film-developing/fixer/"),
    ("paper_fixer",8,"https://www.macodirect.de/en/chemistry/black-white-chemistry/paper-developing/fixer/"),
    ("film_wetting",16,"https://www.macodirect.de/en/chemistry/black-white-chemistry/film-developing/wetting-agent/"),
    ("paper_wetting",16,"https://www.macodirect.de/en/chemistry/black-white-chemistry/paper-developing/wetting-agent/"),
    ("film_aux",0,"https://www.macodirect.de/en/chemistry/black-white-chemistry/film-developing/auxiliaries/"),
    ("paper_aux",0,"https://www.macodirect.de/en/chemistry/black-white-chemistry/paper-developing/auxiliaries/"),
]
OUT=Path("build-output/macodirect-master")
OUT.mkdir(parents=True,exist_ok=True)
DB=Path("combined/src/main/assets/mdc_full.sqlite")

def norm(s):
    s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode("ascii").lower()
    s=s.replace("–","-").replace("—","-")
    return " ".join(re.sub(r"[^a-z0-9+]+"," ",s).split())

def compact(s): return re.sub(r"[^a-z0-9]+","",norm(s))

def clean_title(s):
    s=" ".join((s or "").split())
    s=re.sub(r"^(?:OUR CHOICE\s+)+","",s,flags=re.I)
    s=re.sub(r"^Versand nur innerhalb der EU\*\s*","",s,flags=re.I)
    return s.strip()

def availability(txt):
    t=" ".join(txt.split()).lower()
    if "sold out" in t or "currently not available" in t: return "sold_out"
    if "ready to ship" in t: return "ready_to_ship"
    if "delivery time" in t: return "orderable"
    return "listed"

def product_box(a):
    x=a
    for _ in range(8):
        if x is None: break
        cls=" ".join(x.get("class",[])) if hasattr(x,"get") else ""
        if "product--box" in cls or "product-box" in cls: return x
        x=x.parent
    return a.parent

sess=requests.Session()
sess.headers.update({"User-Agent":"Mozilla/5.0 (Darkroom catalog audit; contact: local app project)"})
raw=[]
seen_pages={}

for label,role,url in CATEGORIES:
    cat_seen=set()
    page=1
    while page<=12:
        page_url=url if page==1 else url+("?p="+str(page))
        r=sess.get(page_url,timeout=35)
        print(f"FETCH {label} p={page} status={r.status_code} bytes={len(r.content)}")
        r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser")
        anchors=soup.select("a.product--title")
        if not anchors:
            anchors=[a for a in soup.find_all("a",href=True) if "product" in " ".join(a.get("class",[])).lower() and (a.get("title") or a.get_text(strip=True))]
        page_keys=[]
        for a in anchors:
            title=clean_title(a.get("title") or a.get_text(" ",strip=True))
            href=urljoin(BASE,a.get("href",""))
            if not title or not href.startswith(BASE): continue
            key=(title,href)
            if key in cat_seen: continue
            cat_seen.add(key); page_keys.append(key)
            box=product_box(a)
            txt=box.get_text(" ",strip=True) if box else ""
            raw.append({
                "category":label,"role_hint":role,"title":title,"url":href,
                "availability":availability(txt),"page":page,"category_url":url
            })
        if not page_keys:
            break
        signature=tuple(sorted(page_keys))
        if signature in seen_pages.get(label,set()):
            break
        seen_pages.setdefault(label,set()).add(signature)
        # Stop if pagination says this is the last page.
        text=soup.get_text(" ",strip=True)
        m=re.search(r"\b(\d+)\s+of\s+(\d+)\b",text,re.I)
        if m and page>=int(m.group(2)): break
        page+=1
        time.sleep(0.15)

# Merge identical URLs/titles across category roles.
merged={}
for x in raw:
    key=(x["url"],norm(x["title"]))
    m=merged.setdefault(key,{
        "title":x["title"],"url":x["url"],"availability":x["availability"],
        "categories":[],"role_hints":0,"source_pages":[]
    })
    if x["category"] not in m["categories"]: m["categories"].append(x["category"])
    m["role_hints"] |= x["role_hint"]
    if x["category_url"] not in m["source_pages"]: m["source_pages"].append(x["category_url"])
    # Prefer strongest availability.
    rank={"ready_to_ship":3,"orderable":2,"listed":1,"sold_out":0}
    if rank.get(x["availability"],0)>rank.get(m["availability"],0): m["availability"]=x["availability"]

products=list(merged.values())
products.sort(key=lambda x:(x["categories"],norm(x["title"])))

# Current DB names + aliases for matching.
con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
catalog=[dict(r) for r in con.execute("SELECT id,name,manufacturer,roles,aliases FROM catalog_products ORDER BY name")]
alias_rows=[dict(r) for r in con.execute("""SELECT p.id,p.name,p.roles,a.alias FROM catalog_aliases a JOIN catalog_products p ON p.id=a.product_id""")]
developers=[r[0] for r in con.execute("SELECT name FROM developers")]
films=[r[0] for r in con.execute("SELECT name FROM films")]

candidates=[]
for r in catalog:
    candidates.append(("catalog",r["id"],r["name"],r["name"],r["roles"]))
    for a in (r["aliases"] or "").split("|"):
        if a.strip(): candidates.append(("catalog_alias",r["id"],r["name"],a.strip(),r["roles"]))
for r in alias_rows:
    candidates.append(("catalog_alias",r["id"],r["name"],r["alias"],r["roles"]))
for name in developers: candidates.append(("mdc_developer","",name,name,1))
for name in films: candidates.append(("mdc_film","",name,name,128))

def score(q,c):
    qn,n=norm(q),norm(c)
    qc,nc=compact(q),compact(c)
    if not qn or not n: return 0
    if qc==nc: return 1000
    if qn==n: return 1000
    if qc and (qc in nc or nc in qc): return 860-min(120,abs(len(qc)-len(nc))*3)
    qt=set(qn.split()); nt=set(n.split())
    inter=len(qt&nt); union=max(1,len(qt|nt))
    j=inter/union
    # brand/packaging titles often contain the canonical name plus units.
    seq=__import__("difflib").SequenceMatcher(None,qn,n).ratio()
    return int(max(j,seq)*700)

for p in products:
    scored=[]
    for typ,pid,pname,term,roles in candidates:
        s=score(p["title"],term)
        if s>0: scored.append((s,typ,pid,pname,term,roles))
    scored.sort(reverse=True,key=lambda x:x[0])
    best=scored[:5]
    p["matches"]=[{"score":s,"type":typ,"id":pid,"name":pname,"term":term,"roles":roles} for s,typ,pid,pname,term,roles in best]
    b=best[0] if best else None
    p["best_score"]=b[0] if b else 0
    p["best_type"]=b[1] if b else ""
    p["best_name"]=b[3] if b else ""
    # conservative auto-match only; lower scores remain REVIEW.
    p["match_state"]="MATCH" if b and b[0]>=820 else "REVIEW"

summary={
    "raw_rows":len(raw),"unique_listing_rows":len(products),
    "category_counts":{},"catalog_count":len(catalog),
    "current_role_counts":{},
}
for label,role,url in CATEGORIES:
    summary["category_counts"][label]=sum(1 for p in products if label in p["categories"])
for bit,label in [(1,"FILM_DEV"),(2,"PAPER_DEV"),(4,"STOP"),(8,"FIX"),(16,"WETTING"),(32,"WASHING"),(64,"CHEMISTRY"),(128,"FILM")]:
    summary["current_role_counts"][label]=con.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & ?)<>0",(bit,)).fetchone()[0]
summary["review_count"]=sum(p["match_state"]=="REVIEW" for p in products)
summary["match_count"]=sum(p["match_state"]=="MATCH" for p in products)

(OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"macodirect_raw.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"macodirect_products.json").write_text(json.dumps(products,ensure_ascii=False,indent=2),encoding="utf-8")
with (OUT/"macodirect_products.csv").open("w",newline="",encoding="utf-8") as f:
    fields=["title","url","availability","categories","role_hints","best_score","best_type","best_name","match_state"]
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for p in products:
        row={k:p.get(k,"") for k in fields}
        row["categories"]="|".join(p["categories"])
        w.writerow(row)

print(json.dumps(summary,ensure_ascii=False,indent=2))
print("\nREVIEW CANDIDATES:")
for p in products:
    if p["match_state"]=="REVIEW":
        print(f"{p['role_hints']:3} | {p['title']} | {p['availability']} | best={p['best_score']} {p['best_type']} {p['best_name']}")
con.close()
