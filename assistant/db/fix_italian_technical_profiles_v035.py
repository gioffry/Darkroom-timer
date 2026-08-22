#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sqlite3, sys

DB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('combined/src/main/assets/mdc_full.sqlite')
if not DB.exists():
    raise SystemExit(f'missing database: {DB}')

PROTECTED = ('films', 'developers', 'times', 'developer_dilutions')
IT_FIELDS = (
    'physical_state_it','preparation_it','reuse_instructions_it','capacity_it',
    'shelf_life_unopened_it','shelf_life_opened_it','shelf_life_stock_it',
    'shelf_life_working_it','storage_notes_it','notes_it'
)

# Words which prove that a supposedly Italian technical sentence still contains
# normal English prose. Technical names such as stock, film, RC/FB and brand names
# are intentionally not rejected.
ENGLISH = re.compile(
    r'\b(the|and|with|when|should|used|stored|working solution|original package|minimum|'
    r'defines|processing|explicitly|before|allowed|number|has been|protected|darkness|'
    r'oxidation|later use|replace|guaranteed|reached|store|direct sun|air access|'
    r'unopened|opened concentrate|prepared|manufacturer states|depending on|additional|'
    r'once opened|completely|make up|cool place|well-closed|partially exhausted|'
    r'no more than|use once|discard|recommended|about|per litre|per liter|rolls|sheets|'
    r'developer|concentrate remains|full tightly|half full|bottle|solution is|solution should)\b',
    re.I
)

def fingerprint(con, table):
    h = hashlib.sha256()
    cols = [r[1] for r in con.execute(f'PRAGMA table_info({table})')]
    if not cols:
        raise SystemExit(f'protected table missing: {table}')
    order = ','.join('"'+c.replace('"','""')+'"' for c in cols)
    for row in con.execute(f'SELECT * FROM {table} ORDER BY {order}'):
        h.update(repr(tuple(row)).encode('utf-8'))
        h.update(b'\n')
    return h.hexdigest()

def clean(v):
    if v is None:
        return ''
    s = str(v).replace('\\r\\n','\n').replace('\\n','\n').replace('\\r','\n')
    return '\n'.join(line.strip() for line in s.splitlines() if line.strip()).strip()

def safe_it(v):
    s = clean(v)
    if not s or ENGLISH.search(s):
        return ''
    return s

PHYSICAL = {
    'available as powder concentrate or ready-to-use liquid':'disponibile come concentrato in polvere o liquido pronto all’uso',
    'dry powder concentrate':'concentrato in polvere secca',
    'highly concentrated liquid':'liquido ad alta concentrazione',
    'liquid concentrate':'concentrato liquido',
    'liquid developer concentrate':'rivelatore liquido concentrato',
    'one-part concentrate':'concentrato monocomponente',
    'one-part liquid concentrate':'concentrato liquido monocomponente',
    'powder':'polvere',
    'powder developer':'rivelatore in polvere',
    'powder developer; Kodak also supplied a liquid form':'rivelatore in polvere; Kodak ha commercializzato anche una versione liquida',
    'single-mix dry powder':'polvere secca a miscela unica',
    'three-part powder':'polvere in tre componenti',
    'three-part powder concentrate':'concentrato in polvere in tre componenti',
    'two-bath developer':'rivelatore a due bagni',
    'two-component liquid concentrate':'concentrato liquido in due componenti',
    'two-component powder':'polvere in due componenti',
    'two-part dry powder':'polvere secca in due componenti',
    'two-part liquid concentrate':'concentrato liquido in due componenti',
    'two-part liquid concentrate (Part A + Part B)':'concentrato liquido in due componenti (Parte A + Parte B)',
    'two-part liquid concentrate kit':'kit di concentrati liquidi in due componenti',
    'two-part liquid developer system':'sistema rivelatore liquido in due componenti',
    'two-part liquid developer/replenisher':'rivelatore/reintegratore liquido in due componenti',
    'two-part powder':'polvere in due componenti',
}

FOMA_STORAGE = ('Conservare la chimica originale e la soluzione di lavoro in luogo asciutto e ventilato, '
                'al riparo dal sole diretto, a 10–25 °C; limitare il contatto con l’aria delle soluzioni di lavoro.')
FOMA_REUSE = ('FOMA dichiara una capacità di trattamento per la soluzione di lavoro. Se lo sviluppo viene '
              'interrotto prima di raggiungere tale capacità, conservare la soluzione al buio e protetta '
              'dall’ossidazione per un uso successivo; sostituirla quando si raggiunge la durata o la capacità garantita.')
ILFORD_POWDER_PREP = ('Sciogliere la Parte A in circa tre quarti del volume finale di acqua a circa 40 °C; '
                      'aggiungere la Parte B mescolando, portare al volume finale e raffreddare a circa 20 °C.')
ILFORD_POWDER_REUSE = ('La soluzione stock può essere riutilizzata compensando il tempo di sviluppo. '
                       'Le diluizioni 1+1 e 1+3 sono monouso e non devono essere riutilizzate.')
ILFORD_POWDER_OPENED = ('Una volta aperta la confezione di polvere, preparare immediatamente la soluzione stock.')
ILFORD_POWDER_STOCK = ('Stock: 6 mesi in bottiglia piena e ben chiusa; 1 mese a metà bottiglia; '
                       '4 mesi in vasca profonda con coperchio galleggiante; 1 mese senza coperchio galleggiante.')
ILFORD_POWDER_WORKING = ('Diluizioni 1+1 o 1+3: non oltre 24 ore; usare come monouso.')
ILFORD_POWDER_UNOPENED = ('Polvere non aperta: durata non limitata dichiarata se conservata al fresco e all’asciutto tra 4 e 20 °C.')

# High-confidence full translations. These replace the v0.3.4 word-by-word output.
# Values not covered here are kept only if they already pass the strict Italian check.
OVERRIDES = {
    'fomadon lqn': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato con acqua. Intervallo indicato da FOMA: da 1+10 a 1+14.',
        'reuse_instructions_it':FOMA_REUSE,
        'capacity_it':'Confezione da 250 ml: circa 12 rulli 135-36 o 120, oppure fino a 30 fogli 13×18 cm.',
        'shelf_life_unopened_it':'Confezione originale: almeno 12 mesi nelle condizioni di conservazione indicate da FOMA.',
        'shelf_life_working_it':'Soluzione di lavoro 1+10 o 1+14: 2–3 ore.',
        'storage_notes_it':FOMA_STORAGE,
    },
    'fomadon lqr': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato con acqua. Intervallo indicato da FOMA: da 1+10 a 1+14.',
        'reuse_instructions_it':FOMA_REUSE,
        'capacity_it':'Confezione da 250 ml: circa 12 rulli 135-36 o 120, oppure fino a 30 fogli 13×18 cm.',
        'shelf_life_unopened_it':'Confezione originale: almeno 12 mesi nelle condizioni di conservazione indicate da FOMA.',
        'shelf_life_working_it':'Soluzione di lavoro 1+10 o 1+14: 2–3 ore.',
        'storage_notes_it':FOMA_STORAGE,
    },
    'fomadon p': {
        'physical_state_it':'polvere in due componenti',
        'preparation_it':'Sciogliere prima la busta piccola e poi quella grande in 700 ml di acqua a 40 °C; dopo completa dissoluzione portare il volume a 1 litro.',
        'reuse_instructions_it':FOMA_REUSE,
        'capacity_it':'1 litro di soluzione di lavoro: circa 10 rulli 135-36 o 120, oppure fino a 25 fogli 13×18 cm.',
        'shelf_life_unopened_it':'Confezione originale: almeno 24 mesi nelle condizioni di conservazione indicate da FOMA.',
        'shelf_life_working_it':'Soluzione di lavoro preparata: 2 mesi.',
        'storage_notes_it':FOMA_STORAGE,
    },
    'fomadon excel': {
        'physical_state_it':'polvere in due componenti',
        'preparation_it':'Sciogliere prima la busta piccola e poi quella grande in 700 ml di acqua a 20–30 °C; dopo completa dissoluzione portare il volume a 1 litro.',
        'reuse_instructions_it':FOMA_REUSE,
        'capacity_it':'1 litro di soluzione di lavoro: circa 12 rulli 135-36 o 120, oppure fino a 30 fogli 13×18 cm.',
        'shelf_life_unopened_it':'Confezione originale: almeno 24 mesi nelle condizioni di conservazione indicate da FOMA.',
        'shelf_life_working_it':'Soluzione di lavoro preparata: 12 mesi.',
        'storage_notes_it':FOMA_STORAGE,
    },
    'fomadon r09': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato con acqua secondo la diluizione scelta.',
        'reuse_instructions_it':'FOMA indica R09 come rivelatore monouso: preparare la diluizione immediatamente prima dell’uso e smaltirla dopo lo sviluppo.',
        'capacity_it':'Confezione da 250 ml: circa 25 rulli 135-36 o 120, oppure fino a 62 fogli 13×18 cm.',
        'shelf_life_unopened_it':'Confezione originale: almeno 24 mesi nelle condizioni di conservazione indicate da FOMA.',
        'shelf_life_opened_it':'Concentrato: utilizzabile per almeno 6 mesi dopo l’apertura se il tappo a vite viene richiuso bene.',
        'shelf_life_working_it':'Soluzione di lavoro: 1+25 per 3–4 giorni; 1+50 per 8–10 ore.',
        'storage_notes_it':FOMA_STORAGE,
    },
    'foma universal': {
        'physical_state_it':'polvere in due componenti',
        'preparation_it':'Sciogliere prima la busta piccola e poi quella grande in 800 ml di acqua calda a 50–70 °C; quindi portare il volume a 1 litro.',
        'reuse_instructions_it':'FOMA dichiara una capacità di trattamento per i bagni di lavoro destinati alla pellicola. Se il trattamento viene interrotto prima di raggiungere la capacità, conservare il bagno al buio limitando il contatto con l’aria e riutilizzarlo solo entro la durata garantita.',
        'capacity_it':'FOMA indica fino a 12 rulli 135-36 o 120 per litro di rivelatore pronto all’uso.',
        'shelf_life_unopened_it':'Confezione originale: almeno 24 mesi nelle condizioni di conservazione indicate da FOMA.',
        'shelf_life_working_it':'Soluzione di lavoro preparata: 6 ore.',
        'storage_notes_it':FOMA_STORAGE,
    },
    'foma retro special': {
        'physical_state_it':'polvere in due componenti',
        'preparation_it':'Sciogliere prima la busta piccola e poi quella grande in 700 ml di acqua a 40 °C; portare il volume a 1 litro.',
        'reuse_instructions_it':'Dopo 0,8 m² di pellicola trattata (circa 16 rulli), aumentare il tempo di sviluppo del 10% per ogni ulteriore 0,1 m².',
        'capacity_it':'1 litro di soluzione di lavoro: 1,3 m² di pellicola, circa 25 rulli 135-36 o 120.',
        'shelf_life_unopened_it':'Confezione originale: almeno 24 mesi nelle condizioni di conservazione indicate da FOMA.',
        'shelf_life_working_it':'Soluzione di lavoro non utilizzata: 1 anno al fresco in bottiglia ben chiusa. Soluzione parzialmente esaurita: 3–6 mesi in funzione dell’esaurimento.',
        'storage_notes_it':FOMA_STORAGE,
    },
    'id 11': {
        'physical_state_it':'polvere in due componenti','preparation_it':ILFORD_POWDER_PREP,
        'reuse_instructions_it':ILFORD_POWDER_REUSE,
        'capacity_it':'Stock: circa 10 rulli 135-36 o 120 per litro, con compensazione del tempo di sviluppo in caso di riutilizzo.',
        'shelf_life_unopened_it':ILFORD_POWDER_UNOPENED,'shelf_life_opened_it':ILFORD_POWDER_OPENED,
        'shelf_life_stock_it':ILFORD_POWDER_STOCK,'shelf_life_working_it':ILFORD_POWDER_WORKING,
    },
    'microphen': {
        'physical_state_it':'polvere in due componenti','preparation_it':ILFORD_POWDER_PREP,
        'reuse_instructions_it':ILFORD_POWDER_REUSE,
        'capacity_it':'Stock: circa 10 rulli 135-36 o 120 per litro, con compensazione del tempo di sviluppo in caso di riutilizzo.',
        'shelf_life_unopened_it':ILFORD_POWDER_UNOPENED,'shelf_life_opened_it':ILFORD_POWDER_OPENED,
        'shelf_life_stock_it':ILFORD_POWDER_STOCK,'shelf_life_working_it':ILFORD_POWDER_WORKING,
    },
    'perceptol': {
        'physical_state_it':'polvere in due componenti','preparation_it':ILFORD_POWDER_PREP,
        'reuse_instructions_it':ILFORD_POWDER_REUSE,
        'capacity_it':'Stock: circa 4 rulli 135-36 o 120 per litro, con compensazione del tempo di sviluppo in caso di riutilizzo.',
        'shelf_life_unopened_it':ILFORD_POWDER_UNOPENED,'shelf_life_opened_it':ILFORD_POWDER_OPENED,
        'shelf_life_stock_it':ILFORD_POWDER_STOCK,'shelf_life_working_it':ILFORD_POWDER_WORKING,
    },
    'ilfosol 3': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato alla diluizione di lavoro scelta, normalmente 1+9 o 1+14, immediatamente prima dell’uso.',
        'reuse_instructions_it':'Le soluzioni 1+9 e 1+14 sono monouso: utilizzarle una sola volta e smaltirle; riutilizzo e reintegro non sono raccomandati.',
        'capacity_it':'500 ml di concentrato: circa 16 rulli a 1+9 oppure 24 rulli a 1+14.',
        'shelf_life_unopened_it':'Concentrato non aperto: circa 18 mesi.',
        'shelf_life_opened_it':'Concentrato: 24 mesi in bottiglia piena e ben chiusa; 4 mesi a metà bottiglia, a 4–20 °C.',
        'shelf_life_working_it':'Soluzione di lavoro: non oltre 24 ore.',
    },
    'ilfotec dd x': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato 1+4 con acqua per l’uso standard.',
        'capacity_it':'A 1+4: circa 16 rulli 135-36 in monouso per bottiglia da 1 litro; fino a 50 rulli 135-36 o 120 con le procedure di riutilizzo previste dal produttore.',
        'shelf_life_opened_it':'Concentrato: 24 mesi in bottiglia piena e ben chiusa; 4 mesi a metà bottiglia, a 4–20 °C.',
    },
    'ilfotec hc': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Preparare prima la soluzione stock diluendo il concentrato, poi diluire ulteriormente lo stock per l’uso. ILFORD documenta, tra le altre, le diluizioni 1+11, 1+15, 1+31 e 1+47.',
        'reuse_instructions_it':'ILFORD specifica che ILFOTEC HC non deve essere usato come reintegratore; utilizzarlo secondo la diluizione prevista dal processo scelto.',
        'capacity_it':'La capacità dipende dalla diluizione: per 1 litro di concentrato, a 1+15 circa 160 trattamenti monouso o 800 con riutilizzo; a 1+31 circa 160 monouso o 1600 con riutilizzo.',
        'shelf_life_unopened_it':'Concentrato integro non aperto a 5–20 °C: durata non limitata dichiarata.',
        'shelf_life_opened_it':'Dopo l’apertura, ILFORD indica di utilizzare tutto il concentrato per preparare le soluzioni stock.',
        'shelf_life_stock_it':'Stock: 6 mesi in contenitore pieno e ben chiuso; 2 mesi a metà contenitore, a 5–20 °C.',
    },
    'ilfotec lc29': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato con acqua immediatamente prima dell’uso. ILFORD documenta le diluizioni 1+9, 1+19 e 1+29.',
        'reuse_instructions_it':'Il rivelatore diluito può essere usato in monouso o riutilizzato nella stessa sessione di lavoro. Il riutilizzo è previsto a 1+9 e 1+19; non è raccomandato a 1+29.',
        'capacity_it':'Bottiglia da 500 ml: a 1+9 circa 16 rulli in monouso o 50 con riutilizzo; a 1+19 circa 32 o 50; a 1+29 circa 50 in monouso e riutilizzo non raccomandato.',
        'shelf_life_opened_it':'Concentrato: 24 mesi in bottiglia piena e ben chiusa; 4 mesi a metà bottiglia, a 4–20 °C.',
        'storage_notes_it':'Conservare nei contenitori originali, al fresco e all’asciutto, a 4–20 °C.',
    },
    'ilford multigrade': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire 1+9 per l’uso standard oppure 1+14 per maggiore controllo/economia. Per 1 litro a 1+9 usare 100 ml di concentrato e 900 ml di acqua.',
        'reuse_instructions_it':'ILFORD indica buone caratteristiche di conservazione e la possibilità di riutilizzo; smaltire il bagno quando si raggiunge il limite di capacità o di conservabilità.',
        'capacity_it':'Una bottiglia da 1 litro usata a 1+9 tratta circa 1000 stampe RC 8×10 pollici oppure 500 stampe FB 8×10 pollici.',
        'shelf_life_unopened_it':'Concentrato integro non aperto, conservato a 5–20 °C: 2 anni.',
        'shelf_life_opened_it':'Concentrato aperto: usare entro 6 mesi e tenere ben chiuso.',
        'shelf_life_working_it':'Soluzione di lavoro: non oltre una giornata in bacinella aperta; circa 24 ore in bottiglia ben chiusa.',
    },
    'pq universal': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Per carta diluire 1+9. Per le pellicole tecniche o in lastra supportate, ILFORD documenta anche 1+9 o 1+19 secondo l’applicazione.',
        'reuse_instructions_it':'ILFORD indica buone caratteristiche di conservazione e la possibilità di riutilizzo; smaltire il bagno quando si raggiunge il limite di capacità o di conservabilità.',
        'capacity_it':'Una bottiglia da 1 litro a 1+9 tratta circa 700 stampe RC 8×10 pollici, 450 stampe FB 8×10 pollici oppure 100 pellicole in lastra 8×10 pollici.',
        'shelf_life_unopened_it':'Concentrato integro non aperto, conservato a 5–20 °C: 2 anni.',
        'shelf_life_opened_it':'Concentrato aperto: usare entro 6 mesi e tenere ben chiuso.',
        'shelf_life_working_it':'Soluzione di lavoro: non oltre una giornata in bacinella aperta; circa 24 ore in bottiglia ben chiusa.',
    },
    'rodinal': {
        'physical_state_it':'concentrato liquido',
        'preparation_it':'Diluire il concentrato con acqua alla diluizione di lavoro desiderata. ADOX documenta diluizioni da 1+25 fino a 1+500.',
        'reuse_instructions_it':'Usare una sola volta e smaltire; ADOX indica che Rodinal non deve essere riutilizzato.',
        'capacity_it':'Usare almeno 5 ml di concentrato per ogni pellicola 135 o 120. Con tank da 250 ml, una bottiglia da 100 ml sviluppa circa 10 pellicole a 1+25 o circa 20 a 1+50.',
        'shelf_life_unopened_it':'ADOX indica almeno altri 12 mesi per il prodotto nuovo nella confezione originale non aperta, se conservato al fresco e al buio; Rodinal è noto per l’elevata stabilità nel tempo.',
        'storage_notes_it':'Conservare al fresco, all’asciutto e al buio. Dopo l’apertura limitare l’aria nella bottiglia con gas protettivo, contenitore comprimibile adatto o biglie di vetro; l’imbrunimento da solo non indica necessariamente inattività.',
    },
}

con = sqlite3.connect(DB)
cur = con.cursor()
before = {t:fingerprint(con,t) for t in PROTECTED}

# First remove all pseudo-translations left by v0.3.4. We never fall back to
# mixed English/Italian text in an Italian field.
rows = cur.execute('SELECT developer_norm,'+','.join(IT_FIELDS)+' FROM developer_profiles').fetchall()
for row in rows:
    dn = row[0]
    values = dict(zip(IT_FIELDS,row[1:]))
    raw_state = cur.execute('SELECT physical_state FROM developer_profiles WHERE developer_norm=?',(dn,)).fetchone()[0]
    if raw_state and raw_state in PHYSICAL:
        values['physical_state_it'] = PHYSICAL[raw_state]
    for f in IT_FIELDS:
        values[f] = safe_it(values.get(f))
    for f,v in OVERRIDES.get(dn,{}).items():
        values[f] = clean(v)
    cur.execute('UPDATE developer_profiles SET '+','.join(f'{f}=?' for f in IT_FIELDS)+', translation_status=? WHERE developer_norm=?',
                [values[f] for f in IT_FIELDS] + ['v035_strict_it', dn])

# Auxiliary rows were authored directly in Italian in v0.3.4. Normalize escape
# sequences and reject accidental English prose there as well, while preserving
# manufacturer names and source metadata.
aux_cols = [r[1] for r in cur.execute('PRAGMA table_info(auxiliary_chemical_profiles)')]
aux_it = [c for c in aux_cols if c.endswith('_it')]
if aux_it:
    for row in cur.execute('SELECT norm_name,'+','.join(aux_it)+' FROM auxiliary_chemical_profiles').fetchall():
        n=row[0]; vals=[]
        for v in row[1:]:
            vv=safe_it(v)
            vals.append(vv)
        cur.execute('UPDATE auxiliary_chemical_profiles SET '+','.join(f'{c}=?' for c in aux_it)+' WHERE norm_name=?', vals+[n])

con.commit()
after = {t:fingerprint(con,t) for t in PROTECTED}
for t in PROTECTED:
    if before[t] != after[t]:
        raise SystemExit(f'PROTECTED MDC TABLE CHANGED: {t}')

profiles = cur.execute('SELECT COUNT(*) FROM developer_profiles').fetchone()[0]
sourced = cur.execute("SELECT COUNT(DISTINCT developer_norm) FROM developer_profile_sources WHERE source_kind='MANUFACTURER'").fetchone()[0]
prep_it = cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(preparation_it,'')<>''").fetchone()[0]
any_it = cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(physical_state_it,preparation_it,reuse_instructions_it,capacity_it,shelf_life_unopened_it,shelf_life_opened_it,shelf_life_stock_it,shelf_life_working_it,storage_notes_it,notes_it,'')<>''").fetchone()[0]

# Acceptance samples from the user's screenshots.
excel = cur.execute("SELECT preparation_it,reuse_instructions_it,capacity_it,shelf_life_unopened_it,shelf_life_working_it,storage_notes_it FROM developer_profiles WHERE developer_norm='fomadon excel'").fetchone()
assert excel and all(excel), excel
assert not any(ENGLISH.search(v or '') for v in excel), excel
assert '24 mesi' in excel[3] and '12 mesi' in excel[4]
aux = cur.execute("SELECT preparation_it,shelf_life_unopened_it,shelf_life_working_it,storage_notes_it,notes_it FROM auxiliary_chemical_profiles WHERE norm_name='fomatol lqn'").fetchone()
assert aux and all(aux), aux
assert '24 mesi' in aux[1] and '2 giorni' in aux[2]
assert not any('\\n' in (v or '') for v in excel+aux)

# No remaining Italian display value may contain obvious English prose.
for f in IT_FIELDS:
    for dn,v in cur.execute(f"SELECT developer_norm,{f} FROM developer_profiles WHERE COALESCE({f},'')<>''"):
        if ENGLISH.search(v or ''):
            raise SystemExit(f'English residue in {dn}.{f}: {v}')

quick=cur.execute('PRAGMA quick_check').fetchone()[0]
assert quick=='ok'
print('technical_it_schema=v035_strict')
print(f'developer_profiles_total={profiles}')
print(f'developer_profiles_manufacturer_sourced={sourced}')
print(f'developer_profiles_with_clean_italian={any_it}')
print(f'developer_profiles_with_clean_italian_preparation={prep_it}')
print('fomadon_excel_duration_and_language=PASS')
print('fomatol_lqn_duration_and_language=PASS')
print('literal_backslash_n_in_acceptance_samples=0')
for t in PROTECTED:
    print(f'protected_{t}_unchanged=PASS')
print('sqlite_quick_check=ok')
con.close()
