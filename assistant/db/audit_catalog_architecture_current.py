#!/usr/bin/env python3
from pathlib import Path
import sqlite3, json, csv

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "src/main/assets/mdc_full.sqlite"
OUT = Path("build-output/db-audit")
OUT.mkdir(parents=True, exist_ok=True)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
interesting = [t for t in tables if any(k in t.lower() for k in (
    "catalog","alias","equiv","maco","developer","film","product","chem","profile","dilution"
))]

summary = {"db": str(DB), "tables": {}}
lines = []
lines.append("DATABASE ARCHITECTURE AUDIT")
lines.append("="*80)

for t in interesting:
    cols = [dict(r) for r in cur.execute(f"PRAGMA table_info({t})")]
    n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    summary["tables"][t] = {"count": n, "columns": cols}
    lines.append(f"\n[{t}] rows={n}")
    lines.append("columns=" + ", ".join(c["name"] for c in cols))

# Catalog products
if "catalog_products" in tables:
    rows = [dict(r) for r in cur.execute("SELECT * FROM catalog_products ORDER BY name")]
    summary["catalog_products"] = rows
    with (OUT/"catalog_products.csv").open("w",newline="",encoding="utf-8") as f:
        if rows:
            w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    lines.append("\nCATALOG PRODUCTS")
    for r in rows:
        lines.append(json.dumps(r, ensure_ascii=False, sort_keys=True))

if "catalog_aliases" in tables:
    rows = [dict(r) for r in cur.execute("""
        SELECT a.*, p.name AS product_name
        FROM catalog_aliases a
        LEFT JOIN catalog_products p ON p.id=a.product_id
        ORDER BY product_name, alias
    """)]
    summary["catalog_aliases"] = rows
    with (OUT/"catalog_aliases.csv").open("w",newline="",encoding="utf-8") as f:
        if rows:
            w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

# Any equivalence / Maco / profiles tables
for t in interesting:
    if t in ("catalog_products","catalog_aliases"): continue
    if any(k in t.lower() for k in ("equiv","maco","profile")):
        try:
            rows=[dict(r) for r in cur.execute(f"SELECT * FROM {t} ORDER BY 1")]
        except Exception:
            rows=[dict(r) for r in cur.execute(f"SELECT * FROM {t}")]
        summary[t]=rows
        with (OUT/f"{t}.csv").open("w",newline="",encoding="utf-8") as f:
            if rows:
                w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
        lines.append(f"\nDUMP {t}")
        for r in rows[:500]:
            lines.append(json.dumps(r, ensure_ascii=False, sort_keys=True))

# Role counts
if "catalog_products" in tables:
    role_defs = {
        1:"FILM_DEV",2:"PAPER_DEV",4:"STOP",8:"FIX",16:"WETTING",32:"WASHING",64:"CHEMISTRY",128:"FILM"
    }
    lines.append("\nROLE COUNTS")
    summary["role_counts"]={}
    for bit,label in role_defs.items():
        n=cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & ?)<>0",(bit,)).fetchone()[0]
        summary["role_counts"][label]=n
        lines.append(f"{label}={n}")
    dual=cur.execute("SELECT name,roles FROM catalog_products WHERE (roles & 1)<>0 AND (roles & 2)<>0 ORDER BY name").fetchall()
    summary["dual_film_paper_developers"]=[dict(r) for r in dual]
    lines.append("DUAL_FILM_PAPER=" + ", ".join(r["name"] for r in dual))

# exact probes relevant to current bug
probes=["adotol","neutol","print ne","pq universal","foma universal","ecoprint","d96","duo step"]
summary["probes"]={}
for q in probes:
    hits=[]
    if "catalog_products" in tables:
        hits += [dict(r) for r in cur.execute("SELECT id,name,manufacturer,roles,aliases FROM catalog_products WHERE lower(name) LIKE ? OR lower(aliases) LIKE ?",('%'+q+'%','%'+q+'%'))]
    if "catalog_aliases" in tables:
        hits += [dict(r) for r in cur.execute("""
            SELECT p.id,p.name,p.manufacturer,p.roles,a.alias
            FROM catalog_aliases a JOIN catalog_products p ON p.id=a.product_id
            WHERE lower(a.alias) LIKE ?
        """,('%'+q+'%',))]
    summary["probes"][q]=hits
    lines.append(f"PROBE {q}: {json.dumps(hits, ensure_ascii=False)}")

(OUT/"architecture.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"architecture.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
print("\n".join(lines[-80:]))
con.close()
