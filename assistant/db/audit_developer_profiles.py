#!/usr/bin/env python3
from pathlib import Path
import csv, sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'src/main/assets/mdc_full.sqlite'
OUT_TXT = Path('developer-db-audit.txt')
OUT_CSV = Path('developer-db-missing.csv')

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

required_tables = {'developers','times','developer_profiles','developer_dilutions','developer_field_provenance','developer_profile_sources'}
tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
missing_tables = sorted(required_tables - tables)
if missing_tables:
    raise SystemExit('missing tables: ' + ', '.join(missing_tables))

fields = [
    'manufacturer','physical_state','preparation','reuse_mode','capacity_text',
    'shelf_life_unopened','shelf_life_opened','shelf_life_stock','shelf_life_working'
]
core_fields = ['manufacturer','physical_state','preparation','reuse_mode','capacity_text']
shelf_fields = ['shelf_life_unopened','shelf_life_opened','shelf_life_stock','shelf_life_working']
profiles = cur.execute('SELECT * FROM developer_profiles ORDER BY developer_name COLLATE NOCASE').fetchall()
dev_count = cur.execute('SELECT COUNT(*) FROM developers').fetchone()[0]
time_count = cur.execute('SELECT COUNT(*) FROM times').fetchone()[0]
film_count = cur.execute('SELECT COUNT(*) FROM films').fetchone()[0]
quick = cur.execute('PRAGMA quick_check').fetchone()[0]

if len(profiles) != dev_count:
    raise SystemExit(f'profile coverage mismatch {len(profiles)} != {dev_count}')

coverage = {f: sum(1 for r in profiles if str(r[f] or '').strip()) for f in fields}
with_source = cur.execute("SELECT COUNT(DISTINCT developer_norm) FROM developer_profile_sources WHERE source_kind='MANUFACTURER'").fetchone()[0]
mdc_dilutions = cur.execute("SELECT COUNT(*) FROM developer_dilutions WHERE source_kind='MDC'").fetchone()[0]
manufacturer_dilutions = cur.execute("SELECT COUNT(*) FROM developer_dilutions WHERE source_kind='MANUFACTURER'").fetchone()[0]
profiles_with_any_dilution = cur.execute('SELECT COUNT(DISTINCT developer_norm) FROM developer_dilutions').fetchone()[0]

def filled(r, field):
    return bool(str(r[field] or '').strip())

def complete_core(r):
    return all(filled(r, f) for f in core_fields) and any(filled(r, f) for f in shelf_fields)

profiles_complete_core = sum(1 for r in profiles if complete_core(r))
profiles_missing_core = len(profiles) - profiles_complete_core

missing_rows = []
for r in profiles:
    missing = [f for f in fields if not filled(r, f)]
    missing_rows.append((r['developer_name'], r['manufacturer'] or '', 'YES' if complete_core(r) else 'NO', ','.join(missing), r['mdc_combination_count'], r['mdc_film_count']))

with OUT_CSV.open('w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['developer','manufacturer','complete_core','missing_fields','mdc_combinations','mdc_films'])
    w.writerows(missing_rows)

# Regression: FOMADON Excel must now be a real film-developer profile, not an empty shell.
excel = cur.execute("SELECT * FROM developer_profiles WHERE developer_norm='fomadon excel'").fetchone()
if excel is None:
    raise SystemExit('FOMADON Excel profile missing')
excel_dils = [r[0] for r in cur.execute("SELECT dilution FROM developer_dilutions WHERE developer_norm='fomadon excel' ORDER BY dilution_norm")]
excel_sources = [r[0] for r in cur.execute("SELECT source_url FROM developer_profile_sources WHERE developer_norm='fomadon excel' AND source_kind='MANUFACTURER'")]
checks = {
    'excel_manufacturer': bool(excel['manufacturer']),
    'excel_physical_state': bool(excel['physical_state']),
    'excel_preparation': bool(excel['preparation']),
    'excel_capacity': bool(excel['capacity_text']),
    'excel_dilutions': bool(excel_dils),
    'excel_manufacturer_source': any('foma.cz' in s for s in excel_sources),
    'quick_check': quick == 'ok',
}
if not all(checks.values()):
    raise SystemExit('FOMADON Excel / integrity regression failed: ' + repr(checks))

# Hierarchy regression: any duplicate dilution keeps the first source; MDC rows must not be overwritten.
bad_priority = cur.execute('''
    SELECT COUNT(*) FROM developer_dilutions d
    JOIN times t ON t.developer_norm=d.developer_norm AND t.dilution_norm=d.dilution_norm
    WHERE d.source_kind<>'MDC'
''').fetchone()[0]
if bad_priority:
    raise SystemExit(f'MDC dilution priority violated for {bad_priority} rows')

lines = [
    'database_audit=PASS',
    'hierarchy=MDC_FIRST_MANUFACTURER_FILL_ONLY',
    f'developers={dev_count}',
    f'films={film_count}',
    f'combinations={time_count}',
    f'profiles={len(profiles)}',
    f'profiles_with_manufacturer_source={with_source}',
    f'profiles_complete_core={profiles_complete_core}',
    f'profiles_missing_core={profiles_missing_core}',
    'complete_core_rule=manufacturer+physical_state+preparation+reuse_mode+capacity_text+at_least_one_shelf_life',
    f'profiles_with_any_dilution={profiles_with_any_dilution}',
    f'dilution_rows_mdc={mdc_dilutions}',
    f'dilution_rows_manufacturer_added={manufacturer_dilutions}',
]
for f in fields:
    lines.append(f'coverage_{f}={coverage[f]}/{len(profiles)}')
lines += [
    'fomadon_excel=PASS',
    'fomadon_excel_manufacturer=' + str(excel['manufacturer']),
    'fomadon_excel_physical_state=' + str(excel['physical_state']),
    'fomadon_excel_dilutions=' + '|'.join(excel_dils),
    'fomadon_excel_capacity=' + str(excel['capacity_text']),
    'mdc_priority_regression=PASS',
    f'sqlite_quick_check={quick}',
    f'missing_report={OUT_CSV.name}',
]
OUT_TXT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('\n'.join(lines))
con.close()
