#!/usr/bin/env python3
from pathlib import Path
import json, re, sqlite3, unicodedata
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'src/main/assets/mdc_full.sqlite'
ENRICH = Path(__file__).resolve().parent / 'producer_enrichment.json'

if not DB.exists():
    raise SystemExit(f'missing MDC database: {DB}')
if not ENRICH.exists():
    raise SystemExit(f'missing producer enrichment: {ENRICH}')


def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode('ascii').lower()
    s = s.replace('–', ' ').replace('—', ' ').replace('-', ' ')
    return ' '.join(re.sub(r'[^a-z0-9+]+', ' ', s).split())


def blank(v):
    return v is None or (isinstance(v, str) and not v.strip())


def norm_dilution(s):
    s = str(s or '').strip()
    if not s:
        return ''
    if s.lower() == 'stock':
        return 'stock'
    return s.replace(':', '+').replace(' ', '').lower()


payload = json.loads(ENRICH.read_text(encoding='utf-8'))
records = payload.get('records', [])
checked_at = payload.get('checkedAt') or datetime.now(timezone.utc).strftime('%Y-%m-%d')

con = sqlite3.connect(DB)
cur = con.cursor()
cur.executescript('''
CREATE TABLE IF NOT EXISTS developer_profiles(
  developer_norm TEXT PRIMARY KEY,
  developer_name TEXT NOT NULL,
  manufacturer TEXT,
  product_name TEXT,
  physical_state TEXT,
  preparation TEXT,
  reuse_mode TEXT,
  reuse_instructions TEXT,
  capacity_text TEXT,
  shelf_life_unopened TEXT,
  shelf_life_opened TEXT,
  shelf_life_stock TEXT,
  shelf_life_working TEXT,
  storage_notes TEXT,
  exhaustion_notes TEXT,
  mdc_combination_count INTEGER NOT NULL DEFAULT 0,
  mdc_film_count INTEGER NOT NULL DEFAULT 0,
  profile_updated TEXT
);
CREATE TABLE IF NOT EXISTS developer_dilutions(
  developer_norm TEXT NOT NULL,
  dilution TEXT NOT NULL,
  dilution_norm TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  source_url TEXT,
  source_title TEXT,
  verified_at TEXT,
  PRIMARY KEY(developer_norm,dilution_norm)
);
CREATE TABLE IF NOT EXISTS developer_profile_sources(
  developer_norm TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_title TEXT,
  source_date TEXT,
  checked_at TEXT,
  PRIMARY KEY(developer_norm,source_url)
);
CREATE TABLE IF NOT EXISTS developer_field_provenance(
  developer_norm TEXT NOT NULL,
  field_name TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  source_url TEXT,
  source_title TEXT,
  checked_at TEXT,
  PRIMARY KEY(developer_norm,field_name)
);
CREATE TABLE IF NOT EXISTS developer_enrichment_unmatched(
  match_names TEXT PRIMARY KEY,
  source_url TEXT,
  checked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_developer_profiles_manufacturer ON developer_profiles(manufacturer);
CREATE INDEX IF NOT EXISTS idx_developer_dilutions_dev ON developer_dilutions(developer_norm);
''')

# Rebuild profile rows from the canonical MDC developer table, while retaining
# existing manufacturer-enriched values if this script is run repeatedly.
for dev_name, dev_norm in cur.execute('SELECT name,norm_name FROM developers ORDER BY name').fetchall():
    combo_count = cur.execute('SELECT COUNT(*) FROM times WHERE developer_norm=?', (dev_norm,)).fetchone()[0]
    film_count = cur.execute('SELECT COUNT(DISTINCT film_norm) FROM times WHERE developer_norm=?', (dev_norm,)).fetchone()[0]
    cur.execute('''INSERT INTO developer_profiles
      (developer_norm,developer_name,mdc_combination_count,mdc_film_count,profile_updated)
      VALUES(?,?,?,?,?)
      ON CONFLICT(developer_norm) DO UPDATE SET
        developer_name=excluded.developer_name,
        mdc_combination_count=excluded.mdc_combination_count,
        mdc_film_count=excluded.mdc_film_count,
        profile_updated=excluded.profile_updated''',
      (dev_norm, dev_name, combo_count, film_count, checked_at))
    cur.execute('''INSERT OR REPLACE INTO developer_field_provenance
      (developer_norm,field_name,source_kind,source_url,source_title,checked_at)
      VALUES(?,?,?,?,?,?)''',
      (dev_norm, 'developer_name', 'MDC', '', 'Massive Dev Chart / Digitaltruth', checked_at))

# MDC dilutions are imported first and therefore always win the provenance tie.
for dev_norm, dilution, dilution_norm, source_url in cur.execute('''
    SELECT developer_norm,dilution,dilution_norm,MIN(source_url)
    FROM times
    WHERE COALESCE(dilution_norm,'')<>''
    GROUP BY developer_norm,dilution_norm
    ORDER BY developer_norm,dilution_norm
''').fetchall():
    cur.execute('''INSERT OR IGNORE INTO developer_dilutions
      (developer_norm,dilution,dilution_norm,source_kind,source_url,source_title,verified_at)
      VALUES(?,?,?,?,?,?,?)''',
      (dev_norm, dilution or dilution_norm, dilution_norm, 'MDC', source_url or '', 'Massive Dev Chart / Digitaltruth', checked_at))

profile_columns = {
    'manufacturer': 'manufacturer',
    'productName': 'product_name',
    'physicalState': 'physical_state',
    'preparation': 'preparation',
    'reuseMode': 'reuse_mode',
    'reuseInstructions': 'reuse_instructions',
    'capacityText': 'capacity_text',
    'shelfLifeUnopened': 'shelf_life_unopened',
    'shelfLifeOpened': 'shelf_life_opened',
    'shelfLifeStock': 'shelf_life_stock',
    'shelfLifeWorking': 'shelf_life_working',
    'storageNotes': 'storage_notes',
    'exhaustionNotes': 'exhaustion_notes',
}

canonical = {norm(name): (name, dn) for name, dn in cur.execute('SELECT name,norm_name FROM developers').fetchall()}
unmatched = []
applied_fields = 0
added_manufacturer_dilutions = 0
matched_records = 0

for rec in records:
    match = None
    for candidate in rec.get('matchNames', []):
        if norm(candidate) in canonical:
            match = canonical[norm(candidate)]
            break
    source_url = str(rec.get('sourceUrl') or '').strip()
    source_title = str(rec.get('sourceTitle') or '').strip()
    source_date = str(rec.get('sourceDate') or '').strip()
    if match is None:
        key = ' | '.join(rec.get('matchNames', []))
        unmatched.append(key)
        cur.execute('INSERT OR REPLACE INTO developer_enrichment_unmatched VALUES(?,?,?)', (key, source_url, checked_at))
        continue

    matched_records += 1
    _, dev_norm = match
    if source_url:
        cur.execute('''INSERT OR REPLACE INTO developer_profile_sources
          (developer_norm,source_kind,source_url,source_title,source_date,checked_at)
          VALUES(?,?,?,?,?,?)''',
          (dev_norm, 'MANUFACTURER', source_url, source_title, source_date, checked_at))

    current = cur.execute('SELECT * FROM developer_profiles WHERE developer_norm=?', (dev_norm,)).fetchone()
    col_names = [d[0] for d in cur.description]
    row = dict(zip(col_names, current))
    for json_key, column in profile_columns.items():
        value = rec.get(json_key)
        if blank(value) or not blank(row.get(column)):
            continue
        cur.execute(f'UPDATE developer_profiles SET {column}=?, profile_updated=? WHERE developer_norm=?',
                    (str(value).strip(), checked_at, dev_norm))
        cur.execute('''INSERT OR REPLACE INTO developer_field_provenance
          (developer_norm,field_name,source_kind,source_url,source_title,checked_at)
          VALUES(?,?,?,?,?,?)''',
          (dev_norm, column, 'MANUFACTURER', source_url, source_title, checked_at))
        applied_fields += 1
        row[column] = value

    # Manufacturer dilutions only add values that MDC did not already supply.
    # Existing MDC dilution rows are never replaced.
    for dilution in rec.get('dilutions', []) or []:
        dn = norm_dilution(dilution)
        if not dn:
            continue
        before = con.total_changes
        cur.execute('''INSERT OR IGNORE INTO developer_dilutions
          (developer_norm,dilution,dilution_norm,source_kind,source_url,source_title,verified_at)
          VALUES(?,?,?,?,?,?,?)''',
          (dev_norm, str(dilution), dn, 'MANUFACTURER', source_url, source_title, checked_at))
        if con.total_changes > before:
            added_manufacturer_dilutions += 1

cur.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)', ('developer_profile_hierarchy', 'MDC_FIRST_MANUFACTURER_FILL_ONLY'))
cur.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)', ('developer_profile_checked_at', checked_at))
cur.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)', ('developer_profile_manufacturer_records', str(matched_records)))
cur.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)', ('developer_profile_manufacturer_fields_applied', str(applied_fields)))
cur.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)', ('developer_profile_manufacturer_dilutions_added', str(added_manufacturer_dilutions)))
con.commit()

profiles = cur.execute('SELECT COUNT(*) FROM developer_profiles').fetchone()[0]
devs = cur.execute('SELECT COUNT(*) FROM developers').fetchone()[0]
mdc_dils = cur.execute("SELECT COUNT(*) FROM developer_dilutions WHERE source_kind='MDC'").fetchone()[0]
manufacturer_dils = cur.execute("SELECT COUNT(*) FROM developer_dilutions WHERE source_kind='MANUFACTURER'").fetchone()[0]
quick = cur.execute('PRAGMA quick_check').fetchone()[0]
con.close()

print(f'developer_profiles={profiles}/{devs}')
print(f'manufacturer_records_matched={matched_records}')
print(f'manufacturer_fields_applied={applied_fields}')
print(f'dilutions_mdc={mdc_dils}')
print(f'dilutions_manufacturer_added={manufacturer_dils}')
print(f'unmatched_enrichment_records={len(unmatched)}')
if unmatched:
    print('unmatched=' + '; '.join(unmatched))
print(f'quick_check={quick}')

if profiles != devs or quick != 'ok':
    raise SystemExit('developer profile enrichment integrity failure')
