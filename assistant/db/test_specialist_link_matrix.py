#!/usr/bin/env python3
from pathlib import Path
import sqlite3, re, unicodedata, json

DB=Path("combined/src/main/assets/mdc_full.sqlite")

def norm(s):
    s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode("ascii").lower()
    s=s.replace("–"," ").replace("—"," ").replace("-"," ")
    return " ".join(re.sub(r"[^a-z0-9+]+"," ",s).split())

con=sqlite3.connect(DB)
con.row_factory=sqlite3.Row
cur=con.cursor()
assert cur.execute("PRAGMA quick_check").fetchone()[0]=="ok"

films=[dict(r) for r in cur.execute("""
  SELECT p.id,p.name,l.specialist_name
  FROM catalog_products p
  JOIN catalog_specialist_links l ON l.product_id=p.id AND l.specialist_kind='film'
  WHERE (p.roles & 128)<>0
  ORDER BY p.name
""")]
devs=[dict(r) for r in cur.execute("""
  SELECT p.id,p.name,l.specialist_name
  FROM catalog_products p
  JOIN catalog_specialist_links l ON l.product_id=p.id AND l.specialist_kind='developer'
  WHERE (p.roles & 1)<>0
  ORDER BY p.name
""")]

assert len(films)==56, len(films)
assert len(devs)==58, len(devs)

film_fail=[]
film_rows=0
film_name_differences=0
for r in films:
    if norm(r["name"])!=norm(r["specialist_name"]):
        film_name_differences+=1
    fn=norm(r["specialist_name"])
    exists=cur.execute("SELECT COUNT(*) FROM films WHERE norm_name=?",(fn,)).fetchone()[0]
    rows=cur.execute("SELECT COUNT(*) FROM times WHERE film_norm=?",(fn,)).fetchone()[0]
    if not exists or not rows:
        film_fail.append((r["name"],r["specialist_name"],exists,rows))
    film_rows+=rows
assert not film_fail, film_fail[:20]
assert film_name_differences==29, film_name_differences

dev_fail=[]
dev_rows=0
dev_name_differences=0
for r in devs:
    if norm(r["name"])!=norm(r["specialist_name"]):
        dev_name_differences+=1
    dn=norm(r["specialist_name"])
    exists=cur.execute("SELECT COUNT(*) FROM developers WHERE norm_name=?",(dn,)).fetchone()[0]
    rows=cur.execute("SELECT COUNT(*) FROM times WHERE developer_norm=?",(dn,)).fetchone()[0]
    if not exists or not rows:
        dev_fail.append((r["name"],r["specialist_name"],exists,rows))
    dev_rows+=rows
assert not dev_fail, dev_fail[:20]
assert dev_name_differences==45, dev_name_differences

# The two mappings involved in the reported regression must be exact and explicit.
kent=cur.execute("""
 SELECT l.specialist_name
 FROM catalog_products p JOIN catalog_specialist_links l ON l.product_id=p.id
 WHERE p.name='KENTMERE PAN 100' AND l.specialist_kind='film'
""").fetchone()
excel=cur.execute("""
 SELECT l.specialist_name
 FROM catalog_products p JOIN catalog_specialist_links l ON l.product_id=p.id
 WHERE p.name='FOMADON Excel' AND l.specialist_kind='developer'
""").fetchone()
assert kent and kent[0]=='Kentmere 100', kent
assert excel and excel[0]=='Fomadon Excel', excel

# Preserve and verify the approved Fomadon Excel -> Xtol timing equivalences.
eq=[tuple(r) for r in cur.execute("""
 SELECT selected_developer,selected_dilution,source_developer,source_dilution
 FROM developer_time_equivalents
 WHERE selected_developer_norm=? AND selected_dilution_norm IN ('stock','1+1')
 ORDER BY selected_dilution_norm
""",(norm("Fomadon Excel"),))]
assert ("Fomadon Excel","1+1","Xtol","1+1") in eq, eq
assert ("Fomadon Excel","stock","Xtol","stock") in eq, eq

# Digitaltruth data for the reported film/source developer exists at ISO 100.
for dil in ("stock","1+1"):
    rows=cur.execute("""
      SELECT time35,time120,temp FROM times
      WHERE film_norm=? AND developer_norm=? AND dilution_norm=? AND iso=100
      ORDER BY temp
    """,(norm("Kentmere 100"),norm("Xtol"),dil)).fetchall()
    assert rows, ("Kentmere 100","Xtol",dil)
    assert any((r[0] or r[1]) for r in rows), (dil,[tuple(x) for x in rows])

# Every approved equivalence points to an actual specialist developer/dilution with data.
equiv_fail=[]
for r in cur.execute("""
 SELECT selected_developer,selected_dilution,source_developer,source_dilution,
        source_developer_norm,source_dilution_norm
 FROM developer_time_equivalents
"""):
    n=cur.execute("""
      SELECT COUNT(*) FROM times
      WHERE developer_norm=? AND dilution_norm=?
    """,(r["source_developer_norm"],r["source_dilution_norm"])).fetchone()[0]
    if n==0:
        equiv_fail.append((r["selected_developer"],r["selected_dilution"],
                           r["source_developer"],r["source_dilution"]))
assert not equiv_fail, equiv_fail

summary={
  "linked_films":len(films),
  "film_name_differences":film_name_differences,
  "linked_developers":len(devs),
  "developer_name_differences":dev_name_differences,
  "approved_equivalences":cur.execute("SELECT COUNT(*) FROM developer_time_equivalents").fetchone()[0],
  "kentmere100_xtol_stock":"PASS",
  "kentmere100_xtol_1+1":"PASS",
  "all_specialist_links_have_data":"PASS",
  "all_equivalence_sources_have_data":"PASS"
}
print(json.dumps(summary,ensure_ascii=False,indent=2))
con.close()
