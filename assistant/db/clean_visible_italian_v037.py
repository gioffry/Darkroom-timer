#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sqlite3, sys

DB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('combined/src/main/assets/mdc_full.sqlite')
if not DB.exists():
    raise SystemExit(f'missing database: {DB}')

PROTECTED = ('films', 'developers', 'times', 'developer_dilutions')
DEV_VISIBLE = (
    'physical_state_it', 'preparation_it', 'reuse_instructions_it', 'capacity_it',
    'storage_notes_it', 'notes_it', 'operational_life_it'
)
AUX_VISIBLE = (
    'product_type_it', 'physical_state_it', 'preparation_it', 'capacity_it',
    'storage_notes_it', 'notes_it', 'operational_life_it'
)

# v0.3.7 is deliberately strict: a field shown as Italian must be a complete
# Italian sentence, never a word-by-word hybrid. Brand names, STOCK, RC/FB,
# ISO and format codes are allowed; normal English prose is not.
ENGLISH = re.compile(
    r"\b(the|and|with|when|should|would|could|stored|store|keep|working|solution|"
    r"original|package|minimum|defines|processing|explicitly|before|after|"
    r"protected|darkness|oxidation|later|replace|guaranteed|reached|direct|sun|"
    r"air|access|unopened|opened|prepared|manufacturer|depending|once|use|used|"
    r"discard|recommended|about|rolls|sheets|developer|replenisher|concentrate|"
    r"powder|liquid|full[- ]strength|full|closed|container|without|lists|useful|"
    r"tank|capacity|chemistry|matrix|gallon|months?|days?|hours?|bottle|shelf|life|"
    r"dissolve|water|stir|cool|fresh|reuse|partially|exhausted|well[- ]closed|"
    r"make\s+up|ready[- ]to[- ]use|at\s+least|up\s+to|per\s+litre|per\s+liter)\b",
    re.I
)

def fp(con, table):
    h = hashlib.sha256()
    cols = [r[1] for r in con.execute(f'PRAGMA table_info({table})')]
    order = ','.join('"' + c.replace('"', '""') + '"' for c in cols)
    for row in con.execute(f'SELECT * FROM {table} ORDER BY {order}'):
        h.update(repr(tuple(row)).encode('utf-8'))
        h.update(b'\n')
    return h.hexdigest()

def clean(v):
    if v is None:
        return ''
    s = str(v).replace('\\r\\n', '\n').replace('\\n', '\n').replace('\\r', '\n')
    return '\n'.join(line.strip() for line in s.splitlines() if line.strip()).strip()

def has_english(v):
    s = clean(v)
    return bool(s and ENGLISH.search(s))

def duration_text(months, days, hours):
    parts = []
    if months:
        parts.append(f"{months} mese" if months == 1 else f"{months} mesi")
    if days:
        parts.append(f"{days} giorno" if days == 1 else f"{days} giorni")
    if hours:
        parts.append(f"{hours} ora" if hours == 1 else f"{hours} ore")
    return ', '.join(parts)

def italian_operational(kind, months, days, hours):
    d = duration_text(months, days, hours)
    if not d:
        return ''
    if kind == 'STOCK_PREPARATO':
        return f'Stock preparato in bottiglia piena e ben chiusa: {d}.'
    if kind == 'CONCENTRATO_APERTO':
        return f'Concentrato aperto in bottiglia piena e ben chiusa: {d}.'
    return f'Durata in bottiglia piena e ben chiusa: {d}.'

con = sqlite3.connect(DB)
cur = con.cursor()
before = {t: fp(con, t) for t in PROTECTED}

# D-76 acceptance case from the real-device screenshot. Do not translate
# individual words: replace the complete sourced fact with one complete Italian
# sentence while preserving the same numerical capacity.
cur.execute("""
    UPDATE developer_profiles
       SET capacity_it='Capacità indicata da Kodak: 4 rulli per litro di soluzione stock (16 rulli per gallone USA).'
     WHERE developer_norm='d 76'
""")

# Every calculable operational shelf life is rendered from its structured
# months/days/hours, so no legacy English source sentence can reach the UI.
regen = 0
for table, key in (('developer_profiles', 'developer_norm'), ('auxiliary_chemical_profiles', 'norm_name')):
    rows = cur.execute(f"""
        SELECT {key}, COALESCE(operational_life_kind,''),
               COALESCE(operational_life_months,0), COALESCE(operational_life_days,0),
               COALESCE(operational_life_hours,0), COALESCE(operational_life_it,'')
          FROM {table}
    """).fetchall()
    for k, kind, months, days, hours, old in rows:
        text = italian_operational(kind, months, days, hours)
        if text:
            cur.execute(f"""
                UPDATE {table}
                   SET operational_life_it=?,
                       operational_life_condition_it='bottiglia piena e ben chiusa'
                 WHERE {key}=?
            """, (text, k))
            regen += 1
        elif old and has_english(old):
            # Non-numeric guidance cannot be safely auto-translated. Better to
            # omit it than to show a hybrid sentence. Source metadata remains.
            cur.execute(f"UPDATE {table} SET operational_life_it='' WHERE {key}=?", (k,))

# Clean all other fields that are actually rendered in the technical card.
# Existing complete Italian values are kept. Residual English/hybrid prose is
# removed from display fields only; raw manufacturer data remains untouched.
cleared = {}
for table, key, fields in (
    ('developer_profiles', 'developer_norm', DEV_VISIBLE),
    ('auxiliary_chemical_profiles', 'norm_name', AUX_VISIBLE),
):
    cols = {r[1] for r in cur.execute(f'PRAGMA table_info({table})')}
    fields = tuple(f for f in fields if f in cols)
    rows = cur.execute(f"SELECT {key}," + ','.join(fields) + f" FROM {table}").fetchall()
    for row in rows:
        k = row[0]
        for field, value in zip(fields, row[1:]):
            value = clean(value)
            if not value:
                continue
            if has_english(value):
                cur.execute(f"UPDATE {table} SET {field}='' WHERE {key}=?", (k,))
                cleared[f'{table}.{field}'] = cleared.get(f'{table}.{field}', 0) + 1
            elif '\\n' in value or '\\r' in value:
                cur.execute(f"UPDATE {table} SET {field}=? WHERE {key}=?", (clean(value), k))

# Re-assert D-76 after the generic pass.
d76 = cur.execute("""
    SELECT capacity_it, operational_life_kind, operational_life_it,
           operational_life_months
      FROM developer_profiles WHERE developer_norm='d 76'
""").fetchone()
assert d76, 'D-76 profile missing'
assert d76[0] == 'Capacità indicata da Kodak: 4 rulli per litro di soluzione stock (16 rulli per gallone USA).'
assert d76[1] == 'STOCK_PREPARATO', d76
assert d76[3] == 6, d76
assert d76[2] == 'Stock preparato in bottiglia piena e ben chiusa: 6 mesi.', d76

# No displayed Italian field may still contain obvious English prose or a
# literal escaped newline.
offenders = []
for table, key, fields in (
    ('developer_profiles', 'developer_norm', DEV_VISIBLE),
    ('auxiliary_chemical_profiles', 'norm_name', AUX_VISIBLE),
):
    cols = {r[1] for r in cur.execute(f'PRAGMA table_info({table})')}
    fields = tuple(f for f in fields if f in cols)
    for row in cur.execute(f"SELECT {key}," + ','.join(fields) + f" FROM {table}"):
        k = row[0]
        for field, value in zip(fields, row[1:]):
            s = clean(value)
            if s and (has_english(s) or '\\n' in s or '\\r' in s):
                offenders.append((table, k, field, s))
if offenders:
    raise SystemExit('visible Italian audit failed: ' + repr(offenders[:20]))

con.commit()
after = {t: fp(con, t) for t in PROTECTED}
for t in PROTECTED:
    assert before[t] == after[t], f'protected MDC changed: {t}'

print('release_layer=v037_italian_visible_cleanup')
print(f'operational_structured_rows_regenerated_it={regen}')
print('d76_capacity_it=PASS')
print('d76_stock_duration_it=6_mesi')
print('visible_english_residue=0')
print('visible_literal_backslash_n=0')
for k in sorted(cleared):
    print(f'cleared_hybrid::{k}={cleared[k]}')
for t in PROTECTED:
    print(f'protected_{t}_unchanged_v037=PASS')
con.close()
