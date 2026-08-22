#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sqlite3, sys, unicodedata

DB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('combined/src/main/assets/mdc_full.sqlite')
if not DB.exists():
    raise SystemExit(f'missing database: {DB}')

PROTECTED = ('films', 'developers', 'times', 'developer_dilutions')

def table_fingerprint(con, table):
    h = hashlib.sha256()
    cols = [r[1] for r in con.execute(f'PRAGMA table_info({table})')]
    if not cols:
        raise SystemExit(f'protected table missing: {table}')
    order = ','.join('"'+c.replace('"','""')+'"' for c in cols)
    for row in con.execute(f'SELECT * FROM {table} ORDER BY {order}'):
        h.update(repr(tuple(row)).encode('utf-8'))
        h.update(b'\n')
    return h.hexdigest()

def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii','ignore').decode('ascii').lower()
    return ' '.join(re.sub(r'[^a-z0-9+]+', ' ', s).split())

def add_column(cur, table, definition):
    name = definition.split()[0]
    cols = {r[1] for r in cur.execute(f'PRAGMA table_info({table})')}
    if name not in cols:
        cur.execute(f'ALTER TABLE {table} ADD COLUMN {definition}')

# Exact translations for recurring manufacturer wording. Original text is retained
# in the existing columns; these are display translations only.
EXACT = {
    'liquid concentrate': 'concentrato liquido',
    'two-component powder': 'polvere in due componenti',
    'two-part powder': 'polvere in due componenti',
    'powder': 'polvere',
    'liquid': 'liquido',
    'one_shot': 'monouso',
    'one-shot': 'monouso',
    'reusable': 'riutilizzabile',
    'fresh_working_solution_recommended': 'soluzione di lavoro fresca consigliata',
    'stock_reusable_diluted_one_shot': 'stock riutilizzabile; diluizioni monouso',
    'reusable_with_time_compensation': 'riutilizzabile con compensazione del tempo',
    'one_shot_or_reuse': 'monouso oppure riutilizzabile secondo procedura del produttore',
    'reusable_or_one_shot_by_dilution': 'riutilizzabile o monouso secondo la diluizione',
    'reuse_depends_on_dilution': 'riutilizzo dipendente dalla diluizione',
}

PHRASES = [
    ('Dissolve the smaller bag and then the larger bag in', 'Sciogliere prima la busta piccola e poi quella grande in'),
    ('Dissolve the bigger bag and then the smaller bag in', 'Sciogliere prima la busta grande e poi quella piccola in'),
    ('Dissolve Part A in about three-quarters of final volume of water at about', 'Sciogliere la Parte A in circa tre quarti del volume finale di acqua a circa'),
    ('add Part B while stirring', 'aggiungere la Parte B mescolando'),
    ('then make up to final volume', 'quindi portare al volume finale'),
    ('after complete dissolution make up to 1 litre', 'dopo completa dissoluzione portare a 1 litro'),
    ('make up to 1 litre', 'portare a 1 litro'),
    ('and cool to about', 'e raffreddare a circa'),
    ('Dilute concentrate with water', 'Diluire il concentrato con acqua'),
    ('manufacturer range', 'intervallo indicato dal produttore'),
    ('Working solutions', 'Le soluzioni di lavoro'),
    ('Working solution', 'Soluzione di lavoro'),
    ('working solution', 'soluzione di lavoro'),
    ('ready-to-use developer', 'rivelatore pronto all’uso'),
    ('Use once and discard', 'Usare una sola volta e smaltire'),
    ('use once and discard', 'usare una sola volta e smaltire'),
    ('should be used once and discarded', 'devono essere usate una sola volta e poi smaltite'),
    ('should not be reused', 'non devono essere riutilizzate'),
    ('reuse and replenishment are not recommended', 'riutilizzo e reintegro non sono raccomandati'),
    ('may be reused with development-time compensation', 'può essere riutilizzato compensando il tempo di sviluppo'),
    ('with development-time compensation', 'con compensazione del tempo di sviluppo'),
    ('increase development time by', 'aumentare il tempo di sviluppo del'),
    ('for each additional', 'per ogni ulteriore'),
    ('depending on exhaustion', 'in funzione dell’esaurimento'),
    ('depending on dilution', 'in funzione della diluizione'),
    ('depending on', 'in funzione di'),
    ('Unopened powder', 'Polvere non aperta'),
    ('Unopened concentrate', 'Concentrato non aperto'),
    ('Full unopened concentrate', 'Concentrato integro non aperto'),
    ('Once opened', 'Dopo l’apertura'),
    ('Concentrate', 'Concentrato'),
    ('concentrate', 'concentrato'),
    ('Stock:', 'Stock:'),
    ('stock:', 'stock:'),
    ('full tightly capped bottles', 'bottiglie piene ben chiuse'),
    ('half-full tightly capped bottles', 'bottiglie riempite a metà e ben chiuse'),
    ('full tightly capped', 'contenitore pieno e ben chiuso'),
    ('half full', 'contenitore a metà'),
    ('full capped', 'contenitore pieno e chiuso'),
    ('deep tank with floating lid', 'vasca profonda con coperchio galleggiante'),
    ('deep tank without floating lid', 'vasca profonda senza coperchio galleggiante'),
    ('in cool, dry conditions', 'in luogo fresco e asciutto'),
    ('in a cool place', 'in luogo fresco'),
    ('in a well-closed bottle', 'in una bottiglia ben chiusa'),
    ('per litre', 'per litro'),
    ('per liter', 'per litro'),
    ('1 litre', '1 litro'),
    ('1 liter', '1 litro'),
    ('litres', 'litri'),
    ('liters', 'litri'),
    ('litre', 'litro'),
    ('liter', 'litro'),
    ('rolls of 135-36 or 120', 'rulli 135-36 o 120'),
    ('rolls of 135-36', 'rulli 135-36'),
    ('rolls', 'rulli'),
    ('roll', 'rullo'),
    ('films', 'pellicole'),
    ('film', 'pellicola'),
    ('sheets', 'fogli'),
    ('sheet', 'foglio'),
    ('square metres', 'metri quadrati'),
    ('square metre', 'metro quadrato'),
    ('months', 'mesi'),
    ('month', 'mese'),
    ('years', 'anni'),
    ('year', 'anno'),
    ('hours', 'ore'),
    ('hour', 'ora'),
    ('days', 'giorni'),
    ('day', 'giorno'),
    ('at least', 'almeno'),
    ('no more than', 'non oltre'),
    ('about', 'circa'),
    ('when reused', 'quando riutilizzato'),
    ('with reuse techniques', 'con tecniche di riutilizzo'),
    ('one-shot', 'monouso'),
    ('one shot', 'monouso'),
    ('reused', 'riutilizzato'),
    ('reuse', 'riutilizzo'),
    ('replenishment', 'reintegro'),
    ('capacity', 'capacità'),
    ('discarded', 'smaltita'),
    ('discard', 'smaltire'),
    ('water', 'acqua'),
    ('while stirring', 'mescolando'),
    ('complete dissolution', 'completa dissoluzione'),
    ('final volume', 'volume finale'),
    ('package', 'confezione'),
    ('bottle', 'bottiglia'),
    ('solution', 'soluzione'),
    ('unused', 'non utilizzata'),
    ('partially exhausted', 'parzialmente esaurita'),
    ('indefinite', 'durata non limitata dichiarata'),
    ('stored', 'conservato'),
    ('tightly capped', 'ben chiuso'),
]

def italianize(value):
    if value is None: return ''
    src = str(value).strip()
    if not src: return ''
    low = src.lower()
    if low in EXACT: return EXACT[low]
    out = src
    for a, b in PHRASES:
        out = re.sub(re.escape(a), b, out, flags=re.I)
    out = re.sub(r'(?<=\d)\s*C\b', ' °C', out)
    out = re.sub(r'\bto\b', 'a', out, flags=re.I)
    out = re.sub(r'\band\b', 'e', out, flags=re.I)
    out = re.sub(r'\bor\b', 'o', out, flags=re.I)
    out = re.sub(r'\bfrom\b', 'da', out, flags=re.I)
    out = re.sub(r'\bfor\b', 'per', out, flags=re.I)
    out = re.sub(r'\bof\b', 'di', out, flags=re.I)
    out = re.sub(r'\bwith\b', 'con', out, flags=re.I)
    out = re.sub(r'\bin\b', 'in', out, flags=re.I)
    out = re.sub(r'\s+', ' ', out).strip()
    return out

# High-confidence Italian overrides for the products the user is most likely to encounter.
OVERRIDES = {
    'fomadon lqn': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato con acqua. Intervallo indicato da FOMA: da 1+10 a 1+14.',
        'capacity_it':'Confezione da 250 ml: circa 12 rulli 135-36 o 120, oppure fino a 30 fogli 13×18 cm.',
    },
    'fomadon lqr': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato con acqua. Intervallo indicato da FOMA: da 1+10 a 1+14.',
        'capacity_it':'Confezione da 250 ml: circa 12 rulli 135-36 o 120, oppure fino a 30 fogli 13×18 cm.',
    },
    'fomadon r09': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato con acqua secondo la diluizione scelta.',
        'capacity_it':'Confezione da 250 ml: circa 25 rulli 135-36 o 120, oppure fino a 62 fogli 13×18 cm.',
    },
    'fomadon p': {
        'physical_state_it':'polvere in due componenti',
        'preparation_it':'Sciogliere prima la busta piccola e poi quella grande in 700 ml di acqua a 40 °C; dopo completa dissoluzione portare il volume a 1 litro.',
        'capacity_it':'1 litro di soluzione di lavoro: circa 10 rulli 135-36 o 120, oppure fino a 25 fogli 13×18 cm.',
    },
    'fomadon excel': {
        'physical_state_it':'polvere in due componenti',
        'preparation_it':'Sciogliere prima la busta piccola e poi quella grande in 700 ml di acqua a 20–30 °C; dopo completa dissoluzione portare il volume a 1 litro.',
        'capacity_it':'1 litro di soluzione di lavoro: circa 12 rulli 135-36 o 120, oppure fino a 30 fogli 13×18 cm.',
    },
    'foma universal': {
        'physical_state_it':'polvere in due componenti',
        'preparation_it':'Sciogliere prima la busta piccola e poi quella grande in 800 ml di acqua calda a 50–70 °C; quindi portare il volume a 1 litro.',
        'capacity_it':'FOMA indica fino a 12 rulli 135-36 o 120 per litro di rivelatore pronto all’uso.',
    },
    'id 11': {
        'physical_state_it':'polvere in due componenti',
        'preparation_it':'Sciogliere la Parte A in circa tre quarti del volume finale di acqua a circa 40 °C; aggiungere la Parte B mescolando, portare al volume finale e raffreddare a circa 20 °C.',
        'reuse_instructions_it':'La soluzione stock può essere riutilizzata compensando il tempo di sviluppo. Le diluizioni 1+1 e 1+3 sono monouso e non devono essere riutilizzate.',
        'capacity_it':'Stock: circa 10 rulli 135-36 o 120 per litro quando riutilizzato con compensazione del tempo.',
        'shelf_life_unopened_it':'Polvere non aperta: durata non limitata dichiarata se conservata al fresco e all’asciutto tra 4 e 20 °C.',
        'shelf_life_stock_it':'Stock: 6 mesi in bottiglia piena e ben chiusa; 1 mese a metà bottiglia; 4 mesi in vasca profonda con coperchio galleggiante; 1 mese senza coperchio galleggiante.',
        'shelf_life_working_it':'Diluizioni 1+1 o 1+3: non oltre 24 ore; usare come monouso.',
    },
}

AUX = [
    {
        'norm_name':'fomatol lqn','name':'FOMATOL LQN','manufacturer':'FOMA BOHEMIA',
        'product_type_it':'Rivelatore carta','physical_state_it':'concentrato liquido',
        'preparation_it':'Per lavorazione manuale diluire 1+7: 1 parte di concentrato + 7 parti di acqua. Per lavorazione automatica FOMA indica 1+4.',
        'capacity_it':'A 1+7, 1 litro di soluzione di lavoro tratta circa 1,5 m² di carta FB oppure 3,0 m² di carta RC.',
        'shelf_life_unopened_it':'24 mesi nella confezione originale.',
        'shelf_life_working_it':'2 giorni per la soluzione di lavoro 1+7, nelle condizioni di conservazione indicate da FOMA e limitando l’ossidazione.',
        'storage_notes_it':'Conservare la chimica nella confezione originale, in luogo asciutto e ben ventilato, a 10–25 °C, umidità relativa non oltre 65%, al riparo da sole diretto e sbalzi di temperatura.',
        'notes_it':'Rivelatore fenidone-idrochinone a tono neutro per carte fotografiche B/N; adatto a lavorazione manuale e automatica.',
        'source_title':'FOMA B&W Photo Materials and Developing Information / FOMATOL LQN','source_url':'https://www.foma.cz/en/catalogue_bw_photo_materials_and_developing_information','source_date':'2020/2023'
    },
    {
        'norm_name':'adox adostop eco','name':'ADOX Adostop ECO','manufacturer':'ADOX Fotowerke GmbH',
        'product_type_it':'Bagno di arresto','physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire 1+19. Esempio per 1 litro: 50 ml di concentrato e acqua fino a 1.000 ml.',
        'capacity_it':'Oltre 3 m² per litro di soluzione di lavoro.',
        'shelf_life_unopened_it':'24 mesi dalla data di produzione per il concentrato.',
        'shelf_life_working_it':'ADOX raccomanda 1–2 settimane per la soluzione di lavoro.',
        'storage_notes_it':'Conservare ben chiuso secondo le indicazioni riportate sulla confezione e nella scheda di sicurezza.',
        'notes_it':'A base di acido citrico. L’indicatore cambia dal giallo verso verde/blu quando il bagno è esaurito; può essere riutilizzato finché l’indicatore non segnala esaurimento.',
        'source_title':'ADOX ADOSTOP ECO','source_url':'https://www.adox.de/adostop-eco-2/','source_date':'corrente'
    },
    {
        'norm_name':'fomafix','name':'FOMAFIX','manufacturer':'FOMA BOHEMIA',
        'product_type_it':'Fissaggio rapido film/carta','physical_state_it':'concentrato liquido',
        'preparation_it':'Per lavorazione manuale: 1+5 (1 parte di concentrato + 5 parti di acqua). Per lavorazione automatica: 1+4.',
        'capacity_it':'A 1+5, 1 litro di soluzione di lavoro fissa circa 17 rulli 135-36 o 120; per carta circa 2 m² FB oppure 4 m² RC.',
        'shelf_life_unopened_it':'24 mesi nella confezione originale.',
        'shelf_life_working_it':'Circa 6 mesi per la soluzione di lavoro 1+5 secondo il manuale FOMA.',
        'storage_notes_it':'Conservare nella confezione originale, in luogo asciutto e ben ventilato, a 10–25 °C, umidità relativa non oltre 65%, al riparo da sole diretto e sbalzi di temperatura.',
        'notes_it':'Fissaggio rapido a base di tiosolfato d’ammonio per film e carte B/N.',
        'source_title':'FOMA FOMAFIX / B&W Photo Materials and Developing Information','source_url':'https://www.foma.cz/en/fomafix','source_date':'2023'
    },
    {
        'norm_name':'fotonal','name':'FOTONAL','manufacturer':'FOMA BOHEMIA',
        'product_type_it':'Imbibente / agente bagnante','physical_state_it':'concentrato liquido',
        'preparation_it':'Preparare la soluzione aggiungendo 5 ml di concentrato a 1 litro di acqua. Per pellicole FOMA ortocromatiche il produttore indica 10–20 ml per litro.',
        'capacity_it':'Non è espressa come numero di rulli nella pagina prodotto ufficiale.',
        'shelf_life_unopened_it':'',
        'shelf_life_working_it':'',
        'storage_notes_it':'Usare come ultimo bagno prima dell’asciugatura e conservare il concentrato secondo le indicazioni della confezione.',
        'notes_it':'Favorisce il drenaggio uniforme dell’acqua, accelera l’asciugatura e riduce la formazione di macchie.',
        'source_title':'FOMA FOTONAL','source_url':'https://www.foma.cz/en/catalogue-fotonal-detail-293','source_date':'corrente'
    },
]

con = sqlite3.connect(DB)
cur = con.cursor()
before = {t: table_fingerprint(con, t) for t in PROTECTED}

for definition in (
    'physical_state_it TEXT','preparation_it TEXT','reuse_instructions_it TEXT','capacity_it TEXT',
    'shelf_life_unopened_it TEXT','shelf_life_opened_it TEXT','shelf_life_stock_it TEXT',
    'shelf_life_working_it TEXT','storage_notes_it TEXT','notes_it TEXT',
    'source_language TEXT','translation_status TEXT'):
    add_column(cur, 'developer_profiles', definition)

rows = cur.execute('''SELECT developer_norm,physical_state,preparation,reuse_instructions,capacity_text,
    shelf_life_unopened,shelf_life_opened,shelf_life_stock,shelf_life_working,storage_notes,exhaustion_notes
    FROM developer_profiles''').fetchall()
for row in rows:
    dn = row[0]
    vals = {
        'physical_state_it': italianize(row[1]),
        'preparation_it': italianize(row[2]),
        'reuse_instructions_it': italianize(row[3]),
        'capacity_it': italianize(row[4]),
        'shelf_life_unopened_it': italianize(row[5]),
        'shelf_life_opened_it': italianize(row[6]),
        'shelf_life_stock_it': italianize(row[7]),
        'shelf_life_working_it': italianize(row[8]),
        'storage_notes_it': italianize(row[9]),
        'notes_it': italianize(row[10]),
    }
    vals.update(OVERRIDES.get(dn, {}))
    src_lang = 'en' if any(str(x or '').strip() for x in row[1:]) else ''
    cur.execute('''UPDATE developer_profiles SET
        physical_state_it=?,preparation_it=?,reuse_instructions_it=?,capacity_it=?,
        shelf_life_unopened_it=?,shelf_life_opened_it=?,shelf_life_stock_it=?,shelf_life_working_it=?,
        storage_notes_it=?,notes_it=?,source_language=?,translation_status=?
        WHERE developer_norm=?''', (
        vals['physical_state_it'], vals['preparation_it'], vals['reuse_instructions_it'], vals['capacity_it'],
        vals['shelf_life_unopened_it'], vals['shelf_life_opened_it'], vals['shelf_life_stock_it'], vals['shelf_life_working_it'],
        vals['storage_notes_it'], vals['notes_it'], src_lang, 'IT_RULES_V034' if src_lang else '', dn))

cur.executescript('''
CREATE TABLE IF NOT EXISTS auxiliary_chemical_profiles(
  norm_name TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  manufacturer TEXT,
  product_type_it TEXT,
  physical_state_it TEXT,
  preparation_it TEXT,
  capacity_it TEXT,
  shelf_life_unopened_it TEXT,
  shelf_life_opened_it TEXT,
  shelf_life_stock_it TEXT,
  shelf_life_working_it TEXT,
  storage_notes_it TEXT,
  notes_it TEXT,
  source_title TEXT,
  source_url TEXT,
  source_date TEXT,
  verified INTEGER NOT NULL DEFAULT 1
);
''')
for r in AUX:
    cols = list(r.keys()) + ['verified']
    vals = [r[k] for k in r.keys()] + [1]
    ph = ','.join('?' for _ in cols)
    cur.execute(f"INSERT OR REPLACE INTO auxiliary_chemical_profiles({','.join(cols)}) VALUES({ph})", vals)

cur.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('technical_it_schema','v034')")
cur.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('technical_it_policy','MDC_TABLES_IMMUTABLE; ORIGINAL_TECH_FIELDS_PRESERVED; IT_DISPLAY_COLUMNS_SEPARATE')")
con.commit()

after = {t: table_fingerprint(con, t) for t in PROTECTED}
for t in PROTECTED:
    if before[t] != after[t]:
        raise SystemExit(f'ANTI-CONFLICT FAILURE: protected MDC table changed: {t}')

it_profiles = cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(preparation_it,physical_state_it,capacity_it,shelf_life_working_it,shelf_life_stock_it,shelf_life_opened_it,shelf_life_unopened_it,'')<>''").fetchone()[0]
aux_count = cur.execute('SELECT COUNT(*) FROM auxiliary_chemical_profiles').fetchone()[0]
quick = cur.execute('PRAGMA quick_check').fetchone()[0]
for required in ('fomatol lqn','adox adostop eco','fomafix','fotonal'):
    if cur.execute('SELECT COUNT(*) FROM auxiliary_chemical_profiles WHERE norm_name=? AND verified=1',(required,)).fetchone()[0] != 1:
        raise SystemExit('missing verified auxiliary profile: '+required)
excel = cur.execute("SELECT preparation_it,capacity_it FROM developer_profiles WHERE developer_norm='fomadon excel'").fetchone()
id11 = cur.execute("SELECT preparation_it,shelf_life_stock_it,shelf_life_working_it FROM developer_profiles WHERE developer_norm='id 11'").fetchone()
if not excel or not all(str(x or '').strip() for x in excel): raise SystemExit('FOMADON Excel Italian profile incomplete')
if not id11 or not all(str(x or '').strip() for x in id11): raise SystemExit('ID-11 Italian profile incomplete')
if quick != 'ok': raise SystemExit('sqlite quick_check failed')
con.close()

print('technical_it_schema=v034')
print(f'developer_profiles_with_it={it_profiles}')
print(f'auxiliary_chemical_profiles={aux_count}')
for t in PROTECTED: print(f'protected_{t}_unchanged=PASS')
print('sqlite_quick_check=ok')
