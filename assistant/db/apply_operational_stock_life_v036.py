#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sqlite3,sys

DB=Path(sys.argv[1]) if len(sys.argv)>1 else Path('combined/src/main/assets/mdc_full.sqlite')
if not DB.exists(): raise SystemExit(f'missing database: {DB}')
con=sqlite3.connect(DB); cur=con.cursor()
PROTECTED=('films','developers','times','developer_dilutions')

def fp(table):
    h=hashlib.sha256(); cols=[r[1] for r in cur.execute(f'PRAGMA table_info({table})')]
    order=','.join('"'+c.replace('"','""')+'"' for c in cols)
    for row in cur.execute(f'SELECT * FROM {table} ORDER BY {order}'):
        h.update(repr(tuple(row)).encode('utf-8')); h.update(b'\n')
    return h.hexdigest()
before={t:fp(t) for t in PROTECTED}

def addcol(table, definition):
    name=definition.split()[0]
    cols={r[1] for r in cur.execute(f'PRAGMA table_info({table})')}
    if name not in cols: cur.execute(f'ALTER TABLE {table} ADD COLUMN {definition}')

for table in ('developer_profiles','auxiliary_chemical_profiles'):
    for d in (
        'operational_life_kind TEXT',
        'operational_life_it TEXT',
        'operational_life_months INTEGER',
        'operational_life_days INTEGER',
        'operational_life_hours INTEGER',
        'operational_life_condition_it TEXT',
        'operational_source_kind TEXT',
        'operational_source_title TEXT',
        'operational_source_url TEXT'):
        addcol(table,d)
    cur.execute(f'''UPDATE {table} SET operational_life_kind=NULL,operational_life_it=NULL,
        operational_life_months=NULL,operational_life_days=NULL,operational_life_hours=NULL,
        operational_life_condition_it=NULL,operational_source_kind=NULL,
        operational_source_title=NULL,operational_source_url=NULL''')

FULL='bottiglia piena e ben chiusa, con minimo volume d’aria'

def source_for(devnorm):
    r=cur.execute("""SELECT source_title,source_url FROM developer_profile_sources
                     WHERE developer_norm=? AND source_kind='MANUFACTURER'
                     ORDER BY checked_at DESC LIMIT 1""",(devnorm,)).fetchone()
    return (r[0] or 'Documentazione del produttore',r[1] or '') if r else ('Documentazione tecnica','')

def num(text):
    if not text: return (None,None,None)
    s=text.lower()
    # For full-bottle multi-condition texts, the first stated duration is the
    # full-bottle value in the curated Italian profile data.
    m=re.search(r'(\d+(?:[.,]\d+)?)\s*(anni|anno|mesi|mese|settimane|settimana|giorni|giorno|ore|ora)',s)
    if not m: return (None,None,None)
    v=float(m.group(1).replace(',','.')); unit=m.group(2)
    if unit.startswith('ann'): return (int(round(v*12)),None,None)
    if unit.startswith('mes'): return (int(round(v)),None,None)
    if unit.startswith('sett'): return (None,int(round(v*7)),None)
    if unit.startswith('gior'): return (None,int(round(v)),None)
    if unit.startswith('or'): return (None,None,int(round(v)))
    return (None,None,None)

def put_dev(dn,kind,text,months=None,days=None,hours=None,source_kind='MANUFACTURER',title=None,url=None):
    if not text: return
    if months is None and days is None and hours is None:
        months,days,hours=num(text)
    if title is None:
        title,url0=source_for(dn); url=url if url is not None else url0
    cur.execute('''UPDATE developer_profiles SET operational_life_kind=?,operational_life_it=?,
        operational_life_months=?,operational_life_days=?,operational_life_hours=?,
        operational_life_condition_it=?,operational_source_kind=?,operational_source_title=?,operational_source_url=?
        WHERE developer_norm=?''',(kind,text,months,days,hours,FULL,source_kind,title,url or '',dn))

def put_aux(n,kind,text,months=None,days=None,hours=None,source_kind='MANUFACTURER',title='',url=''):
    if months is None and days is None and hours is None:
        months,days,hours=num(text)
    cur.execute('''UPDATE auxiliary_chemical_profiles SET operational_life_kind=?,operational_life_it=?,
        operational_life_months=?,operational_life_days=?,operational_life_hours=?,
        operational_life_condition_it=?,operational_source_kind=?,operational_source_title=?,operational_source_url=?
        WHERE norm_name=?''',(kind,text,months,days,hours,FULL,source_kind,title,url,n))

# 1) Liquid concentrates: an explicit manufacturer "opened" value is the
# operational value. Italian v0.3.5 text puts the full-bottle case first.
for dn,state,opened in cur.execute("SELECT developer_norm,COALESCE(physical_state_it,''),COALESCE(shelf_life_opened_it,'') FROM developer_profiles").fetchall():
    st=state.lower()
    if opened and ('liquid' in st or 'liquido' in st or 'concentrat' in st or 'concentrato' in st):
        put_dev(dn,'CONCENTRATO_APERTO',opened)

# 2) Powder products / explicitly mixed stock: use stock shelf life. The user
# stores this prepared stock in a full bottle.
for dn,state,stock in cur.execute("SELECT developer_norm,COALESCE(physical_state_it,''),COALESCE(shelf_life_stock_it,'') FROM developer_profiles").fetchall():
    st=state.lower()
    if stock and ('polvere' in st or 'powder' in st or dn in ('d 76','dektol','microdol x','xtol','xt 3','diafine','acu 1','mzb')):
        put_dev(dn,'STOCK_PREPARATO',stock)

# 3) Products whose manufacturer calls the undiluted prepared stock a
# "working solution". These are NOT 1+X baths: this is the solution prepared
# from the powder and stored before any further dilution/use.
PREPARED={
 'fomadon excel':('Soluzione stock preparata: 12 mesi in bottiglia piena e ben chiusa.',12,None,None),
 'fomadon p':('Soluzione stock preparata: 2 mesi in bottiglia piena e ben chiusa.',2,None,None),
 'foma retro special':('Soluzione stock preparata non utilizzata: 12 mesi in bottiglia piena e ben chiusa e al fresco.',12,None,None),
 'foma universal':('Soluzione stock preparata: 6 ore nelle condizioni di conservazione indicate da FOMA.',None,None,6),
 'silberra aphenol':('Soluzione preparata non utilizzata: 4 mesi in bottiglia piena e ben chiusa.',4,None,None),
 'silberra micro f':('Soluzione preparata: 1 mese in bottiglia piena e ben chiusa.',1,None,None),
 'silberra s 76':('Soluzione preparata non utilizzata: fino a 6 mesi in bottiglia piena e ben chiusa.',6,None,None),
}
for dn,(txt,mo,da,hr) in PREPARED.items(): put_dev(dn,'STOCK_PREPARATO',txt,mo,da,hr)

# 4) Explicit operational full-bottle research overrides. These never alter MDC.
put_dev('fomadon r09','CONCENTRATO_APERTO',
        'Concentrato aperto: almeno 6 mesi se il tappo è ben chiuso.',6,
        source_kind='MANUFACTURER',
        title='FOMA BOHEMIA — FOMADON R09 datasheet',
        url='https://www.freestylephoto.com/pdf/product_pdfs/formulary/Fomadon_R09_Datasheet_%281_to_25_or_1_to_50_Dilution%29.pdf')
put_dev('fomadon lqn','CONCENTRATO_APERTO',
        'Concentrato aperto: 6 mesi come riferimento in bottiglia piena, ben chiusa e protetta da luce e calore.',6,
        source_kind='TECHNICAL_RETAILER',
        title='Onestopphoto — FOMADON LQN storage guidance',
        url='https://onestopphoto.in/product/fomadon-lqn-250ml/')
# LQR source says "several months" rather than a precise guarantee: retain a
# textual operational value but do not invent a calculated date.
put_dev('fomadon lqr','CONCENTRATO_APERTO',
        'Concentrato aperto: diversi mesi se conservato al fresco, al buio e ben chiuso. La fonte consultata non fornisce un numero unico.',
        None,None,None,source_kind='TECHNICAL_RETAILER',
        title='Onestopphoto — FOMADON LQR storage guidance',
        url='https://onestopphoto.in/product/fomadon-lqr-250ml/')
put_dev('sprint standard','CONCENTRATO_APERTO',
        'Concentrato aperto senza aria: 6 mesi.',6,
        source_kind='TECHNICAL_GUIDE',
        title='SPRINT STANDARD technical storage guidance',
        url='https://www.sprintsystems.com/home/p/standard-bampw-film-developer')
put_dev('rollei supergrain','CONCENTRATO_APERTO',
        'Concentrato aperto con aria esclusa: circa 6 mesi o più.',6,
        source_kind='TECHNICAL_DATASHEET',
        title='ROLLEI SUPERGRAIN technical data',
        url='https://www.rolleianalog.com/products/rollei-supergrain/?lang=en')
put_dev('tanol','CONCENTRATO_APERTO',
        'Concentrato A: almeno 12 mesi; concentrato B: durata non limitata dichiarata.',12,
        source_kind='MANUFACTURER',title='Moersch Tanol',url='https://www.moersch-photochemie.de/en/product/tanol/')

# Auxiliary chemistry most visible in the user's inventory.
put_aux('fomatol lqn','CONCENTRATO_APERTO',
        'Concentrato aperto: oltre 6 mesi se conservato senza aria; per il calcolo l’app usa 6 mesi come riferimento prudenziale.',6,
        source_kind='TECHNICAL_RETAILER',
        title='Fotocarrete — FOMATOL LQN FAQ',
        url='https://fotocarrete.com/comprar/revelador-papel-foma-fomatol-lqn-250ml/')
# ADOX publishes production shelf life but explicitly explains that opened
# developer life depends on oxygen. Do not convert the 24-month production life
# into a false after-opening countdown.
put_aux('adox adostop eco','CONCENTRATO_APERTO',
        'Concentrato aperto: conservare nella bottiglia originale piena e accuratamente richiusa. Il produttore non pubblica un intervallo univoco calcolabile dalla data di apertura.',
        source_kind='MANUFACTURER',
        title='ADOX ADOSTOP ECO / Developers & Storage',
        url='https://www.adox.de/developers-storage/')
# FOMA does not state an opened-concentrate countdown for these two in the
# current general catalogue; preserve the distinction rather than reusing 1+X.
put_aux('fomafix','CONCENTRATO_APERTO',
        'Concentrato aperto: conservare in bottiglia piena e ben chiusa. La documentazione FOMA disponibile non indica un numero separato dalla durata della soluzione 1+5.',
        source_kind='MANUFACTURER',title='FOMA B&W Photo Materials',url='https://www.foma.cz/en/catalogue_bw_photo_materials_and_developing_information')
put_aux('fotonal','CONCENTRATO_APERTO',
        'Concentrato aperto: conservare in bottiglia piena e ben chiusa. La documentazione FOMA disponibile non indica un intervallo numerico separato dopo l’apertura.',
        source_kind='MANUFACTURER',title='FOMA processing chemistry',url='https://www.foma.cz/en/catalogue_bw_photo_materials_and_developing_information')

con.commit()

# Acceptance: operational data must never touch MDC combination tables.
after={t:fp(t) for t in PROTECTED}
for t in PROTECTED:
    if before[t]!=after[t]: raise SystemExit(f'protected MDC changed: {t}')

# Critical products.
excel=cur.execute("SELECT operational_life_kind,operational_life_months,operational_life_it FROM developer_profiles WHERE developer_norm='fomadon excel'").fetchone()
assert excel and excel[0]=='STOCK_PREPARATO' and excel[1]==12 and '12 mesi' in excel[2]
lqn=cur.execute("SELECT operational_life_kind,operational_life_months,operational_life_it FROM auxiliary_chemical_profiles WHERE norm_name='fomatol lqn'").fetchone()
assert lqn and lqn[0]=='CONCENTRATO_APERTO' and lqn[1]==6 and '6 mesi' in lqn[2]

count=cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(operational_life_it,'')<>''").fetchone()[0]
calc=cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE operational_life_months IS NOT NULL OR operational_life_days IS NOT NULL OR operational_life_hours IS NOT NULL").fetchone()[0]
aux=cur.execute("SELECT COUNT(*) FROM auxiliary_chemical_profiles WHERE COALESCE(operational_life_it,'')<>''").fetchone()[0]
print('operational_rule=FULL_BOTTLE_ONLY')
print('working_1plusX_used_for_expiry=NO')
print(f'developer_operational_profiles={count}')
print(f'developer_operational_profiles_calculable={calc}')
print(f'auxiliary_operational_profiles={aux}')
print('fomadon_excel_stock_full_bottle=12_months')
print('fomatol_lqn_opened_full_bottle_reference=6_months')
for t in PROTECTED: print(f'protected_{t}_unchanged_operational=PASS')
con.close()
