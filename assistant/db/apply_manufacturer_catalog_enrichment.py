#!/usr/bin/env python3
from pathlib import Path
import sqlite3,json,re,unicodedata

DB=Path("combined/src/main/assets/mdc_full.sqlite")
DATA=Path("assistant/db/manufacturer_catalog_enrichment_v1.json")

def norm(s):
    s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode("ascii").lower()
    return " ".join(re.sub(r"[^a-z0-9+]+"," ",s).split())

d=json.loads(DATA.read_text(encoding="utf-8"))
assert d.get("hierarchy")=="MACODIRECT_GATE_MANUFACTURER_TECHNICAL"

con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
cur=con.cursor()
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
cols=[r[1] for r in cur.execute("PRAGMA table_info(auxiliary_chemical_profiles)")]
assert "norm_name" in cols

for rec in d["records"]:
    row=cur.execute("SELECT * FROM catalog_products WHERE norm_name=? LIMIT 1",(norm(rec["name"]),)).fetchone()
    if not row:
        raise SystemExit("manufacturer enrichment product missing from Maco-gated catalog: "+rec["name"])
    pid=row["id"]
    updates={}
    if rec.get("paperDilutions"): updates["paper_dilutions"]="|".join(rec["paperDilutions"])
    if rec.get("filmDilutions"): updates["film_dilutions"]="|".join(rec["filmDilutions"])
    if rec.get("physicalState"): updates["physical_state"]=rec["physicalState"]
    if "stockPrep" in rec: updates["stock_prep"]=1 if rec["stockPrep"] else 0
    if updates:
        sql="UPDATE catalog_products SET "+",".join(k+"=?" for k in updates)+" WHERE id=?"
        cur.execute(sql, list(updates.values())+[pid])

    # Technical prose is kept in the existing auxiliary profile table so the current
    # app can consume it later without inventing a parallel semantic store.
    aux={
      "norm_name":norm(rec["name"]),
      "name":rec["name"],
      "manufacturer":rec.get("manufacturer",""),
      "product_type_it":rec.get("productTypeIt",""),
      "physical_state_it":rec.get("physicalStateIt",""),
      "preparation_it":rec.get("preparationIt",""),
      "capacity_it":rec.get("capacityIt",""),
      "shelf_life_unopened_it":rec.get("shelfLifeUnopenedIt",""),
      "shelf_life_opened_it":rec.get("shelfLifeOpenedIt",""),
      "shelf_life_stock_it":rec.get("shelfLifeStockIt",""),
      "shelf_life_working_it":rec.get("shelfLifeWorkingIt",""),
      "storage_notes_it":rec.get("storageNotesIt",""),
      "notes_it":rec.get("notesIt",""),
      "source_title":rec["sourceTitle"],
      "source_url":rec["sourceUrl"],
      "source_date":"",
      "verified":1,
      "operational_life_kind":rec.get("operationalLifeKind",""),
      "operational_life_it":rec.get("operationalLifeIt",""),
      "operational_life_months":rec.get("operationalLifeMonths"),
      "operational_life_days":rec.get("operationalLifeDays"),
      "operational_life_hours":rec.get("operationalLifeHours"),
      "operational_life_condition_it":rec.get("operationalLifeConditionIt",""),
      "operational_source_kind":"MANUFACTURER",
      "operational_source_title":rec["sourceTitle"],
      "operational_source_url":rec["sourceUrl"],
    }
    names=list(aux)
    cur.execute(
      "INSERT INTO auxiliary_chemical_profiles("+",".join(names)+") VALUES("+",".join("?" for _ in names)+") "
      "ON CONFLICT(norm_name) DO UPDATE SET "+",".join(k+"=excluded."+k for k in names if k!="norm_name"),
      [aux[k] for k in names]
    )
    cur.execute("""INSERT OR REPLACE INTO catalog_technical_sources(
        product_id,source_kind,source_title,source_url,checked_at,fields)
        VALUES(?,?,?,?,?,?)""",
        (pid,"MANUFACTURER",rec["sourceTitle"],rec["sourceUrl"],d["checkedAt"],
         "|".join(sorted(updates.keys()))+"|AUXILIARY_PROFILE"))

con.commit()
assert cur.execute("PRAGMA quick_check").fetchone()[0]=="ok"
for rec in d["records"]:
    row=cur.execute("SELECT paper_dilutions FROM catalog_products WHERE norm_name=?",(norm(rec["name"]),)).fetchone()
    assert row is not None
print("manufacturer_catalog_enrichment=PASS")
print("records="+str(len(d["records"])))
print("adotol="+str(cur.execute("SELECT paper_dilutions FROM catalog_products WHERE norm_name='adox adotol konstant ii'").fetchone()[0]))
print("manufacturer_sources="+str(cur.execute("SELECT COUNT(*) FROM catalog_technical_sources WHERE source_kind='MANUFACTURER'").fetchone()[0]))
con.close()
