#!/usr/bin/env python3
from pathlib import Path
import json,re,sqlite3,unicodedata

DB=Path("combined/src/main/assets/mdc_full.sqlite")
DATA=Path("assistant/db/macodirect_technical_fallback_v1.json")

def norm(s):
    s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode("ascii").lower()
    return " ".join(re.sub(r"[^a-z0-9+]+"," ",s).split())

def merge(existing, extra):
    vals=[]; seen=set()
    for x in str(existing or "").split("|") + list(extra or []):
        x=str(x).strip()
        k=norm(x)
        if x and k not in seen:
            seen.add(k); vals.append(x)
    return "|".join(vals)

data=json.loads(DATA.read_text(encoding="utf-8"))
assert data.get("hierarchy")=="MACODIRECT_GATE_TECHNICAL_RETAILER_FALLBACK"
db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
cur=db.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS catalog_technical_sources(
  product_id TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  source_title TEXT NOT NULL,
  source_url TEXT NOT NULL,
  checked_at TEXT NOT NULL,
  fields TEXT NOT NULL DEFAULT '',
  PRIMARY KEY(product_id,source_kind,source_url)
);
""")
applied=0
for rec in data["records"]:
    p=cur.execute("SELECT * FROM catalog_products WHERE norm_name=? LIMIT 1",(norm(rec["name"]),)).fetchone()
    if p is None:
        raise SystemExit("retailer technical product missing from Maco-gated catalog: "+rec["name"])
    updates={}
    if rec.get("filmDilutions"):
        updates["film_dilutions"]=merge(p["film_dilutions"],rec["filmDilutions"])
    if rec.get("paperDilutions"):
        updates["paper_dilutions"]=merge(p["paper_dilutions"],rec["paperDilutions"])
    if rec.get("physicalState") and not str(p["physical_state"] or "").strip():
        updates["physical_state"]=rec["physicalState"]
    if updates:
        cur.execute("UPDATE catalog_products SET "+",".join(k+"=?" for k in updates)+" WHERE id=?",
                    list(updates.values())+[p["id"]])
    fields="|".join(sorted(updates)) or "REFERENCE_ONLY"
    cur.execute("""INSERT OR REPLACE INTO catalog_technical_sources(
        product_id,source_kind,source_title,source_url,checked_at,fields)
        VALUES(?,?,?,?,?,?)""",
        (p["id"],"TECHNICAL_RETAILER","MacoDirect product technical data",
         p["source_url"],data["checkedAt"],fields))
    applied+=1

db.commit()
assert cur.execute("PRAGMA quick_check").fetchone()[0]=="ok"
print("macodirect_technical_fallback=PASS")
print("records="+str(applied))
print("technical_retailer_sources="+str(cur.execute(
    "SELECT COUNT(*) FROM catalog_technical_sources WHERE source_kind='TECHNICAL_RETAILER'").fetchone()[0]))
db.close()
