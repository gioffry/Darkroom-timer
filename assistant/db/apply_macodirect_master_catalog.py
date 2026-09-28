#!/usr/bin/env python3
from pathlib import Path
import csv, json, re, sqlite3, unicodedata, shutil

DB=Path("combined/src/main/assets/mdc_full.sqlite")
PROPOSAL=Path("build-output/macodirect-proposal/catalog_proposal.json")
LISTINGS=Path("build-output/macodirect-master/macodirect_products.json")
SNAP=Path("assistant/db/snapshots/macodirect-2026-09-28")
CHECKED_AT="2026-09-28"
RETAILER="MACODIRECT"

def ws(s): return re.sub(r"\s+"," ",str(s or "")).strip()
def norm(s):
    s=unicodedata.normalize("NFKD",ws(s)).encode("ascii","ignore").decode("ascii").lower()
    return " ".join(re.sub(r"[^a-z0-9+]+"," ",s).split())
def compact(s): return re.sub(r"[^a-z0-9]+","",norm(s))
def split_pipe(s): return [x.strip() for x in str(s or "").split("|") if x.strip()]
def merge_pipe(*vals):
    out=[]; seen=set()
    for v in vals:
        for x in split_pipe(v):
            k=norm(x)
            if k and k not in seen:
                seen.add(k); out.append(x)
    return "|".join(out)
def infer_iso(name):
    n=ws(name)
    # Only explicit speed-like values, avoiding product-number tails when possible.
    pats=[
        r"(?i)\bISO\s*(\d{2,5})\b",
        r"(?i)\b(?:PAN|APX|NP|RPX|DELTA|T[- ]?MAX|TRI[- ]?X|FOMAPAN|RETROPAN|PANCRO|XX)\s*(\d{2,5})\b",
        r"(?i)\b(\d{2,5})\s*(?:ISO)?\s*$",
    ]
    for p in pats:
        m=re.search(p,n)
        if m:
            try:
                v=int(m.group(1))
                if 6 <= v <= 12800: return v
            except Exception: pass
    return 0

proposal=json.loads(PROPOSAL.read_text(encoding="utf-8"))
listings=json.loads(LISTINGS.read_text(encoding="utf-8"))
assert len(listings) >= 500, len(listings)
assert len(proposal) >= 200, len(proposal)
assert sum(int(r["listing_count"]) for r in proposal)==len(listings)

con=sqlite3.connect(DB)
con.row_factory=sqlite3.Row
cur=con.cursor()
cur.execute("PRAGMA foreign_keys=ON")
assert cur.execute("PRAGMA quick_check").fetchone()[0]=="ok"

# The current user-visible catalog is tiny. Specialist tables (MDC films/developers/times)
# remain intact: MacoDirect gates VISIBILITY, it must not destroy specialist history.
existing={r["id"]:dict(r) for r in cur.execute("SELECT * FROM catalog_products")}
existing_by_norm={norm(r["name"]):dict(r) for r in existing.values()}

cur.executescript("""
CREATE TABLE IF NOT EXISTS retailer_catalog_listings(
  retailer TEXT NOT NULL,
  product_id TEXT NOT NULL,
  listing_title TEXT NOT NULL,
  listing_url TEXT NOT NULL,
  availability TEXT NOT NULL DEFAULT '',
  categories TEXT NOT NULL DEFAULT '',
  role_hints INTEGER NOT NULL DEFAULT 0,
  checked_at TEXT NOT NULL,
  PRIMARY KEY(retailer, listing_url)
);
CREATE INDEX IF NOT EXISTS idx_retailer_catalog_product
  ON retailer_catalog_listings(retailer,product_id);

CREATE TABLE IF NOT EXISTS catalog_specialist_links(
  product_id TEXT NOT NULL,
  specialist_kind TEXT NOT NULL,
  specialist_name TEXT NOT NULL,
  relation TEXT NOT NULL,
  evidence_kind TEXT NOT NULL,
  checked_at TEXT NOT NULL,
  PRIMARY KEY(product_id,specialist_kind)
);
CREATE INDEX IF NOT EXISTS idx_catalog_specialist_name
  ON catalog_specialist_links(specialist_kind,specialist_name);
""")

# Freeze current specialist equivalence table. Product identity links are a DIFFERENT concept.
equiv_before=[tuple(r) for r in cur.execute("""
SELECT selected_developer_norm,selected_developer,selected_dilution_norm,selected_dilution,
       source_developer_norm,source_developer,source_dilution_norm,source_dilution,evidence_kind
FROM developer_time_equivalents ORDER BY 1,3,5,7
""")]

proposal_ids={r["id"] for r in proposal}

# Replace the user-visible catalog gate, but preserve existing technical fields where the
# canonical product already existed.
cur.execute("DELETE FROM catalog_aliases")
cur.execute("DELETE FROM retailer_catalog_listings")
cur.execute("DELETE FROM catalog_specialist_links")

# Delete non-Maco products from user-visible catalog only.
for pid in list(existing):
    if pid not in proposal_ids:
        cur.execute("DELETE FROM catalog_products WHERE id=?",(pid,))

for r in proposal:
    pid=r["id"]; name=ws(r["name"]); nk=norm(name)
    old=existing.get(pid) or existing_by_norm.get(nk)
    roles=int(r["roles"])
    aliases=r.get("aliases","")
    if old:
        aliases=merge_pipe(old.get("aliases",""),aliases)
    categories=r.get("categories","")
    source_url=r.get("source_url","")
    manufacturer=ws(r.get("manufacturer",""))
    verification="MACODIRECT_CURRENT_LISTING"
    source_id="macodirect"

    physical_state=old.get("physical_state","") if old else ""
    film_dilutions=old.get("film_dilutions","") if old else ""
    paper_dilutions=old.get("paper_dilutions","") if old else ""
    working_dilution=old.get("working_dilution","") if old else ""
    stock_prep=int(old.get("stock_prep",0) or 0) if old else 0
    subtitle=old.get("subtitle","") if old else ""
    nominal_iso=int(old.get("nominal_iso",0) or 0) if old else 0
    formats=r.get("formats","") or (old.get("formats","") if old else "")

    sk=r.get("specialist_kind","")
    sn=r.get("specialist_name","")
    if sk=="developer" and sn:
        dn=norm(sn)
        # Expose MDC dilutions for linked film developers without conflating product identity.
        vals=[x[0] for x in cur.execute(
            "SELECT DISTINCT dilution FROM times WHERE developer_norm=? AND dilution<>'' ORDER BY dilution",
            (dn,)).fetchall()]
        if vals and (roles & 1) and not film_dilutions:
            film_dilutions="|".join(vals)
        # Reuse structured physical state when the specialist profile has it.
        prof=cur.execute("SELECT physical_state FROM developer_profiles WHERE developer_norm=?",(dn,)).fetchone()
        if prof and prof[0] and not physical_state:
            physical_state=prof[0]
    elif sk=="film" and sn:
        fn=norm(sn)
        if nominal_iso<=0:
            rows=cur.execute("""
                SELECT iso,COUNT(*) n FROM times WHERE film_norm=? AND iso>0
                GROUP BY iso ORDER BY n DESC, iso ASC
            """,(fn,)).fetchall()
            if rows: nominal_iso=int(rows[0][0])
    if nominal_iso<=0 and r.get("kind")=="film":
        nominal_iso=infer_iso(name)

    cols=(pid,name,nk,compact(name),manufacturer,categories,roles,aliases,subtitle,
          source_id,source_url,verification,physical_state,film_dilutions,paper_dilutions,
          working_dilution,stock_prep,nominal_iso,formats)
    cur.execute("""
      INSERT INTO catalog_products(
        id,name,norm_name,compact_name,manufacturer,categories,roles,aliases,subtitle,
        source_id,source_url,verification,physical_state,film_dilutions,paper_dilutions,
        working_dilution,stock_prep,nominal_iso,formats
      ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(id) DO UPDATE SET
        name=excluded.name,norm_name=excluded.norm_name,compact_name=excluded.compact_name,
        manufacturer=excluded.manufacturer,categories=excluded.categories,roles=excluded.roles,
        aliases=excluded.aliases,subtitle=excluded.subtitle,source_id=excluded.source_id,
        source_url=excluded.source_url,verification=excluded.verification,
        physical_state=excluded.physical_state,film_dilutions=excluded.film_dilutions,
        paper_dilutions=excluded.paper_dilutions,working_dilution=excluded.working_dilution,
        stock_prep=excluded.stock_prep,nominal_iso=excluded.nominal_iso,formats=excluded.formats
    """,cols)

    # Only actual names/listing titles are aliases. Specialist equivalents are links, not aliases.
    alias_values=[name]+split_pipe(aliases)
    seen=set()
    for a in alias_values:
        k=norm(a)
        if not k or k in seen: continue
        seen.add(k)
        cur.execute("""INSERT OR REPLACE INTO catalog_aliases(product_id,alias,norm_alias,compact_alias)
                       VALUES(?,?,?,?)""",(pid,a,k,compact(a)))

    if sk and sn:
        cur.execute("""INSERT INTO catalog_specialist_links(
            product_id,specialist_kind,specialist_name,relation,evidence_kind,checked_at)
            VALUES(?,?,?,?,?,?)""",
            (pid,sk,sn,r.get("specialist_relation","") or "DIRECT_PRODUCT_MAPPING",
             "AUDITED_MACODIRECT_TO_SPECIALIST",CHECKED_AT))

# Map exact current Maco listings back to canonical products through proposal aliases.
alias_to_pid={}
for r in proposal:
    for a in [r["name"]]+split_pipe(r.get("aliases","")):
        alias_to_pid.setdefault(norm(a),r["id"])

unmapped=[]
for p in listings:
    pid=alias_to_pid.get(norm(p["title"]))
    if not pid:
        unmapped.append(p["title"]); continue
    cur.execute("""INSERT INTO retailer_catalog_listings(
       retailer,product_id,listing_title,listing_url,availability,categories,role_hints,checked_at)
       VALUES(?,?,?,?,?,?,?,?)""",
       (RETAILER,pid,p["title"],p["url"],p.get("availability",""),
        "|".join(p.get("categories",[])),int(p.get("role_hints",0)),CHECKED_AT))
assert not unmapped, unmapped[:10]

# Critical architecture invariants.
assert cur.execute("SELECT COUNT(*) FROM catalog_products").fetchone()[0]==len(proposal)
assert cur.execute("SELECT COUNT(*) FROM retailer_catalog_listings WHERE retailer='MACODIRECT'").fetchone()[0]==len(listings)
assert cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 2)<>0").fetchone()[0] >= 25
assert cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 1)<>0 AND (roles & 2)<>0").fetchone()[0] >= 4
assert cur.execute("SELECT COUNT(*) FROM catalog_products WHERE lower(name) LIKE '%adotol%'").fetchone()[0] >= 1
assert cur.execute("""SELECT COUNT(*) FROM catalog_aliases a JOIN catalog_products p ON p.id=a.product_id
                      WHERE lower(a.alias) LIKE '%adotol%'""").fetchone()[0] >= 1

equiv_after=[tuple(r) for r in cur.execute("""
SELECT selected_developer_norm,selected_developer,selected_dilution_norm,selected_dilution,
       source_developer_norm,source_developer,source_dilution_norm,source_dilution,evidence_kind
FROM developer_time_equivalents ORDER BY 1,3,5,7
""")]
assert equiv_after==equiv_before, "developer_time_equivalents changed"

# Every catalog product is Maco-gated.
orphan=cur.execute("""
SELECT p.id,p.name FROM catalog_products p
LEFT JOIN retailer_catalog_listings r ON r.product_id=p.id AND r.retailer='MACODIRECT'
WHERE r.product_id IS NULL
""").fetchall()
assert not orphan, orphan[:10]

con.commit()
assert cur.execute("PRAGMA quick_check").fetchone()[0]=="ok"

# Freeze the exact retailer evidence and canonical proposal used for this DB revision.
SNAP.mkdir(parents=True,exist_ok=True)
shutil.copy2(LISTINGS,SNAP/"macodirect_products.json")
shutil.copy2(PROPOSAL,SNAP/"catalog_proposal.json")
summary={
  "checked_at":CHECKED_AT,
  "macodirect_listing_rows":len(listings),
  "catalog_products":cur.execute("SELECT COUNT(*) FROM catalog_products").fetchone()[0],
  "catalog_aliases":cur.execute("SELECT COUNT(*) FROM catalog_aliases").fetchone()[0],
  "specialist_links":cur.execute("SELECT COUNT(*) FROM catalog_specialist_links").fetchone()[0],
  "film_products":cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 128)<>0").fetchone()[0],
  "film_developers":cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 1)<>0").fetchone()[0],
  "paper_developers":cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 2)<>0").fetchone()[0],
  "dual_film_paper_developers":cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 1)<>0 AND (roles & 2)<>0").fetchone()[0],
  "stops":cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 4)<>0").fetchone()[0],
  "fixers":cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 8)<>0").fetchone()[0],
  "wetting":cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 16)<>0").fetchone()[0],
  "washing":cur.execute("SELECT COUNT(*) FROM catalog_products WHERE (roles & 32)<>0").fetchone()[0],
  "developer_time_equivalents_preserved":len(equiv_after),
}
(SNAP/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False,indent=2))
con.close()
