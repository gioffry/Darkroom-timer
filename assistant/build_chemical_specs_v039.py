#!/usr/bin/env python3
from pathlib import Path
import json, re, sqlite3, unicodedata
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SEED = ROOT / 'src/main/assets/mdc_developers_seed.txt'
CURATED = ROOT / 'chemical_specs_it_v039.json'
OUT = ROOT / 'src/main/assets/chemical_specs.sqlite'


def norm(value):
    s = unicodedata.normalize('NFKC', value or '').lower()
    s = s.replace('–', ' ').replace('—', ' ').replace('-', ' ')
    s = re.sub(r'[^\w+]+', ' ', s, flags=re.UNICODE)
    return ' '.join(s.split())

seed = [x.strip() for x in SEED.read_text(encoding='utf-8').splitlines() if x.strip()]
curated = json.loads(CURATED.read_text(encoding='utf-8'))
if len(seed) < 180:
    raise SystemExit(f'MDC developer seed unexpectedly small: {len(seed)}')
if len(curated) < 8:
    raise SystemExit(f'Curated technical dataset unexpectedly small: {len(curated)}')

OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()
con = sqlite3.connect(OUT)
cur = con.cursor()
cur.executescript('''
PRAGMA journal_mode=DELETE;
PRAGMA synchronous=OFF;
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE products(
    name TEXT NOT NULL,
    norm_name TEXT PRIMARY KEY,
    manufacturer TEXT NOT NULL DEFAULT '',
    product_type_it TEXT NOT NULL DEFAULT '',
    form_it TEXT NOT NULL DEFAULT '',
    preparation_it TEXT NOT NULL DEFAULT '',
    shelf_unopened_it TEXT NOT NULL DEFAULT '',
    shelf_opened_it TEXT NOT NULL DEFAULT '',
    shelf_stock_it TEXT NOT NULL DEFAULT '',
    shelf_working_it TEXT NOT NULL DEFAULT '',
    storage_it TEXT NOT NULL DEFAULT '',
    capacity_it TEXT NOT NULL DEFAULT '',
    notes_it TEXT NOT NULL DEFAULT '',
    source_name TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    source_date TEXT NOT NULL DEFAULT '',
    verified INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE aliases(
    alias_norm TEXT PRIMARY KEY,
    product_norm TEXT NOT NULL,
    FOREIGN KEY(product_norm) REFERENCES products(norm_name)
);
CREATE INDEX idx_products_name ON products(norm_name);
''')

# Every Massive Dev Chart developer gets a technical placeholder. This guarantees
# a stable 1:1 lookup while leaving unknown facts EMPTY rather than guessing them.
for name in seed:
    n = norm(name)
    cur.execute('''INSERT OR IGNORE INTO products(name,norm_name,verified)
                   VALUES(?,?,0)''', (name, n))
    cur.execute('INSERT OR IGNORE INTO aliases(alias_norm,product_norm) VALUES(?,?)', (n, n))

fields = [
    'manufacturer', 'product_type_it', 'form_it', 'preparation_it',
    'shelf_unopened_it', 'shelf_opened_it', 'shelf_stock_it',
    'shelf_working_it', 'storage_it', 'capacity_it', 'notes_it',
    'source_name', 'source_url', 'source_date'
]
for item in curated:
    name = str(item['name']).strip()
    n = norm(name)
    vals = [str(item.get(k, '') or '').strip() for k in fields]
    cur.execute('''INSERT OR REPLACE INTO products(
        name,norm_name,manufacturer,product_type_it,form_it,preparation_it,
        shelf_unopened_it,shelf_opened_it,shelf_stock_it,shelf_working_it,
        storage_it,capacity_it,notes_it,source_name,source_url,source_date,verified)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        [name, n] + vals + [1 if item.get('verified') else 0])
    aliases = [name] + list(item.get('aliases') or [])
    for alias in aliases:
        an = norm(str(alias))
        if an:
            cur.execute('INSERT OR REPLACE INTO aliases(alias_norm,product_norm) VALUES(?,?)', (an, n))

meta = {
    'schema': 'chemical_specs_v039',
    'authority': 'technical_product_facts_only_no_mdc_combo_fields',
    'last_build': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
    'mdc_seed_count': str(len(seed)),
    'verified_product_count': str(sum(1 for x in curated if x.get('verified'))),
    'language': 'it'
}
for k, v in meta.items():
    cur.execute('INSERT INTO meta(key,value) VALUES(?,?)', (k, v))
cur.execute('PRAGMA user_version=39')
con.commit()

columns = {r[1] for r in cur.execute('PRAGMA table_info(products)')}
for forbidden in {'film', 'iso', 'time35', 'time120', 'temperature', 'temp', 'developer_dilution'}:
    if forbidden in columns:
        raise SystemExit(f'Conflict guard failed: technical DB contains MDC field {forbidden}')
count = cur.execute('SELECT COUNT(*) FROM products').fetchone()[0]
verified = cur.execute('SELECT COUNT(*) FROM products WHERE verified=1').fetchone()[0]
qc = cur.execute('PRAGMA quick_check').fetchone()[0]
con.close()
if count < len(seed) or verified < 8 or qc != 'ok':
    raise SystemExit(f'chemical_specs integrity failed products={count} verified={verified} qc={qc}')
print(f'BUILT chemical_specs.sqlite products={count} verified={verified} quick_check={qc} size={OUT.stat().st_size}')
