#!/usr/bin/env python3
from pathlib import Path
import sqlite3,json
DB=Path("combined/src/main/assets/mdc_full.sqlite")
OUT=Path("build-output/db-postgate-audit")
OUT.mkdir(parents=True,exist_ok=True)
db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
q=lambda sql,args=(): [dict(r) for r in db.execute(sql,args)]
one=lambda sql,args=(): db.execute(sql,args).fetchone()[0]
report={}
report["quick_check"]=one("PRAGMA quick_check")
report["catalog_products"]=one("SELECT COUNT(*) FROM catalog_products")
report["listings"]=one("SELECT COUNT(*) FROM retailer_catalog_listings WHERE retailer='MACODIRECT'")
report["aliases"]=one("SELECT COUNT(*) FROM catalog_aliases")
report["specialist_links"]=one("SELECT COUNT(*) FROM catalog_specialist_links")
report["orphan_products"]=q("""SELECT p.id,p.name FROM catalog_products p
LEFT JOIN retailer_catalog_listings r ON r.product_id=p.id AND r.retailer='MACODIRECT'
WHERE r.product_id IS NULL""")
report["orphan_listings"]=q("""SELECT r.listing_title,r.listing_url,r.product_id FROM retailer_catalog_listings r
LEFT JOIN catalog_products p ON p.id=r.product_id WHERE p.id IS NULL""")
report["duplicate_norm_names"]=q("""SELECT norm_name,COUNT(*) n,GROUP_CONCAT(name,' | ') names
FROM catalog_products GROUP BY norm_name HAVING COUNT(*)>1""")
report["duplicate_compact_names"]=q("""SELECT compact_name,COUNT(*) n,GROUP_CONCAT(name,' | ') names
FROM catalog_products GROUP BY compact_name HAVING COUNT(*)>1""")
report["alias_norm_collisions"]=q("""SELECT a.norm_alias,COUNT(DISTINCT a.product_id) n,
GROUP_CONCAT(DISTINCT p.name) products
FROM catalog_aliases a JOIN catalog_products p ON p.id=a.product_id
GROUP BY a.norm_alias HAVING COUNT(DISTINCT a.product_id)>1""")
report["alias_compact_collisions"]=q("""SELECT a.compact_alias,COUNT(DISTINCT a.product_id) n,
GROUP_CONCAT(DISTINCT p.name) products
FROM catalog_aliases a JOIN catalog_products p ON p.id=a.product_id
GROUP BY a.compact_alias HAVING COUNT(DISTINCT a.product_id)>1""")
report["broken_developer_links"]=q("""SELECT l.*,p.name product_name FROM catalog_specialist_links l
JOIN catalog_products p ON p.id=l.product_id
LEFT JOIN developers d ON d.norm_name=lower(replace(l.specialist_name,'-',' '))
WHERE l.specialist_kind='developer' AND NOT EXISTS(
 SELECT 1 FROM developers d2 WHERE d2.name=l.specialist_name
)""")
report["broken_film_links"]=q("""SELECT l.*,p.name product_name FROM catalog_specialist_links l
JOIN catalog_products p ON p.id=l.product_id
WHERE l.specialist_kind='film' AND NOT EXISTS(
 SELECT 1 FROM films f WHERE f.name=l.specialist_name
)""")
report["shared_specialist_links"]=q("""SELECT specialist_kind,specialist_name,COUNT(*) n,GROUP_CONCAT(p.name,' | ') products
FROM catalog_specialist_links l JOIN catalog_products p ON p.id=l.product_id
GROUP BY specialist_kind,specialist_name HAVING COUNT(*)>1 ORDER BY n DESC,specialist_name""")
report["dual_role"]=q("""SELECT p.id,p.name,l.specialist_name
FROM catalog_products p LEFT JOIN catalog_specialist_links l ON l.product_id=p.id AND l.specialist_kind='developer'
WHERE (p.roles&1)<>0 AND (p.roles&2)<>0 ORDER BY p.name""")
report["adotol"]=q("""SELECT p.*, GROUP_CONCAT(a.alias,' || ') alias_rows
FROM catalog_products p LEFT JOIN catalog_aliases a ON a.product_id=p.id
WHERE lower(p.name) LIKE '%adotol%' GROUP BY p.id""")
report["technical_gaps"]={
  "film_dev_no_dilution": q("""SELECT p.name,l.specialist_name FROM catalog_products p
     LEFT JOIN catalog_specialist_links l ON l.product_id=p.id AND l.specialist_kind='developer'
     WHERE (p.roles&1)<>0 AND trim(COALESCE(p.film_dilutions,''))='' ORDER BY p.name"""),
  "paper_dev_no_dilution": q("""SELECT p.name,l.specialist_name FROM catalog_products p
     LEFT JOIN catalog_specialist_links l ON l.product_id=p.id AND l.specialist_kind='developer'
     WHERE (p.roles&2)<>0 AND trim(COALESCE(p.paper_dilutions,''))='' ORDER BY p.name"""),
  "films_no_iso": q("""SELECT p.name,p.formats,l.specialist_name FROM catalog_products p
     LEFT JOIN catalog_specialist_links l ON l.product_id=p.id AND l.specialist_kind='film'
     WHERE (p.roles&128)<>0 AND COALESCE(p.nominal_iso,0)<=0 ORDER BY p.name"""),
  "films_no_format": q("""SELECT p.name,p.nominal_iso,l.specialist_name FROM catalog_products p
     LEFT JOIN catalog_specialist_links l ON l.product_id=p.id AND l.specialist_kind='film'
     WHERE (p.roles&128)<>0 AND trim(COALESCE(p.formats,''))='' ORDER BY p.name""")
}
eq=q("""SELECT selected_developer,selected_dilution,source_developer,source_dilution,evidence_kind
FROM developer_time_equivalents ORDER BY selected_developer,selected_dilution""")
report["timing_equivalences_count"]=len(eq)
report["timing_equivalence_non_direct"]=[r for r in eq if r["evidence_kind"]!="AUDITED_DIRECT_ONE_HOP"]

# Graph cycle check at developer level (dilution ignored only for cycle detection).
edges={}
for r in eq: edges.setdefault(r["selected_developer"],set()).add(r["source_developer"])
cycles=[]
for start in edges:
    stack=[(start,[start])]
    while stack:
        node,path=stack.pop()
        for nxt in edges.get(node,set()):
            if nxt==start:
                cycles.append(path+[nxt]); continue
            if nxt not in path and len(path)<8: stack.append((nxt,path+[nxt]))
report["timing_equivalence_cycles"]=cycles

assert report["quick_check"]=="ok"
assert report["catalog_products"]==235
assert report["listings"]==523
assert not report["orphan_products"] and not report["orphan_listings"]
assert not report["duplicate_norm_names"] and not report["duplicate_compact_names"]
assert not report["alias_norm_collisions"] and not report["alias_compact_collisions"]
assert not report["broken_developer_links"] and not report["broken_film_links"]
assert len(report["adotol"])==1
assert report["timing_equivalences_count"]==39
assert not report["timing_equivalence_non_direct"]
# Reciprocal A<->B rows are intentional direct equivalences. The engine consumes
# this table one hop at a time; therefore they are reported, not treated as a failure.
(OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({
 "quick_check":report["quick_check"],
 "catalog_products":report["catalog_products"],
 "listings":report["listings"],
 "aliases":report["aliases"],
 "specialist_links":report["specialist_links"],
 "dual_role":[x["name"] for x in report["dual_role"]],
 "shared_specialist_links":report["shared_specialist_links"],
 "film_dev_no_dilution":[x["name"] for x in report["technical_gaps"]["film_dev_no_dilution"]],
 "paper_dev_no_dilution":[x["name"] for x in report["technical_gaps"]["paper_dev_no_dilution"]],
 "films_no_iso":[x["name"] for x in report["technical_gaps"]["films_no_iso"]],
 "films_no_format":[x["name"] for x in report["technical_gaps"]["films_no_format"]],
 "adotol":report["adotol"],
},ensure_ascii=False,indent=2))
db.close()
