#!/usr/bin/env python3
import sqlite3,tempfile,os

OLD_SCHEMA='''
CREATE TABLE personal_recipes (id INTEGER PRIMARY KEY AUTOINCREMENT,combo_key TEXT NOT NULL,film TEXT NOT NULL,format TEXT NOT NULL,nominal_iso INTEGER NOT NULL,exposed_iso INTEGER NOT NULL,developer TEXT NOT NULL,dilution TEXT NOT NULL,processor TEXT NOT NULL,method TEXT NOT NULL,original_temp REAL NOT NULL,original_seconds INTEGER NOT NULL,source_name TEXT NOT NULL,data_type TEXT NOT NULL,source_data TEXT NOT NULL,calculation TEXT NOT NULL,personal_temp REAL NOT NULL,personal_seconds INTEGER NOT NULL,note TEXT NOT NULL DEFAULT '',favorite INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);
CREATE TABLE development_logs (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,combo_key TEXT NOT NULL,film TEXT NOT NULL,format TEXT NOT NULL,nominal_iso INTEGER NOT NULL,exposed_iso INTEGER NOT NULL,developer TEXT NOT NULL,dilution TEXT NOT NULL,actual_temp REAL NOT NULL,processor TEXT NOT NULL,method TEXT NOT NULL,actual_seconds INTEGER NOT NULL,time_origin TEXT NOT NULL,source_seconds INTEGER NOT NULL,source_temp REAL NOT NULL,source_name TEXT NOT NULL,data_type TEXT NOT NULL,source_data TEXT NOT NULL,calculation TEXT NOT NULL,volume_ml REAL NOT NULL DEFAULT 0,product_ml REAL NOT NULL DEFAULT 0,water_ml REAL NOT NULL DEFAULT 0,product_known INTEGER NOT NULL DEFAULT 0,water_known INTEGER NOT NULL DEFAULT 0,rolls INTEGER NOT NULL DEFAULT 1,capacity_state TEXT NOT NULL DEFAULT '',capacity_message TEXT NOT NULL DEFAULT '',rating INTEGER NOT NULL DEFAULT 0,notes TEXT NOT NULL DEFAULT '');
CREATE TABLE chemical_inventory (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,source_type TEXT NOT NULL,source_product_key TEXT NOT NULL DEFAULT '',manufacturer TEXT NOT NULL DEFAULT '',name TEXT NOT NULL,category TEXT NOT NULL,physical_state TEXT NOT NULL,solution_type TEXT NOT NULL,initial_amount REAL NOT NULL DEFAULT 0,remaining_amount REAL NOT NULL DEFAULT 0,unit TEXT NOT NULL,purchase_date TEXT NOT NULL DEFAULT '',open_date TEXT NOT NULL DEFAULT '',prepared_date TEXT NOT NULL DEFAULT '',expiry_date TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '',storage TEXT NOT NULL DEFAULT '',personal_dilution TEXT NOT NULL DEFAULT '',documented_dilutions TEXT NOT NULL DEFAULT '',capacity_value REAL NOT NULL DEFAULT 0,capacity_unit TEXT NOT NULL DEFAULT '',capacity_source TEXT NOT NULL DEFAULT '',source_name TEXT NOT NULL DEFAULT '',data_type TEXT NOT NULL DEFAULT '',archived INTEGER NOT NULL DEFAULT 0);
CREATE TABLE chemical_usage (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,chemical_id INTEGER NOT NULL,development_log_id INTEGER NOT NULL DEFAULT 0,product_name TEXT NOT NULL,developer TEXT NOT NULL DEFAULT '',dilution TEXT NOT NULL DEFAULT '',film TEXT NOT NULL DEFAULT '',format TEXT NOT NULL DEFAULT '',rolls INTEGER NOT NULL DEFAULT 0,quantity_used REAL NOT NULL,unit TEXT NOT NULL,remaining_after REAL NOT NULL,note TEXT NOT NULL DEFAULT '');
CREATE TABLE personal_equipment (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,category TEXT NOT NULL,source_type TEXT NOT NULL,source_model_key TEXT NOT NULL DEFAULT '',manufacturer TEXT NOT NULL DEFAULT '',model TEXT NOT NULL,personal_name TEXT NOT NULL DEFAULT '',quantity_owned INTEGER NOT NULL DEFAULT 1,notes TEXT NOT NULL DEFAULT '');
CREATE TABLE personal_tanks (equipment_id INTEGER PRIMARY KEY,system TEXT NOT NULL DEFAULT '',tank_type TEXT NOT NULL DEFAULT '',capacity_35 INTEGER NOT NULL DEFAULT 0,capacity_120 INTEGER NOT NULL DEFAULT 0,min_inversion_ml REAL NOT NULL DEFAULT 0,min_rotation_ml REAL NOT NULL DEFAULT 0,max_volume_ml REAL NOT NULL DEFAULT 0,cpe2_compatible INTEGER NOT NULL DEFAULT 0,lift_compatible INTEGER NOT NULL DEFAULT 0,technical_source TEXT NOT NULL DEFAULT '',data_type TEXT NOT NULL DEFAULT '');
PRAGMA user_version=2;
'''

NEW_SCHEMA='''
CREATE TABLE IF NOT EXISTS assistant_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,session_key TEXT NOT NULL UNIQUE,film TEXT NOT NULL DEFAULT '',format TEXT NOT NULL DEFAULT '',rolls INTEGER NOT NULL DEFAULT 0,cycle_index INTEGER NOT NULL DEFAULT 0,phase_index INTEGER NOT NULL DEFAULT 0,planned_seconds INTEGER,actual_seconds INTEGER,temperature REAL,tank_snapshot TEXT NOT NULL DEFAULT '',chemistry_snapshot TEXT NOT NULL DEFAULT '',state TEXT NOT NULL DEFAULT '',personal_phase_times TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS paper_chemistry_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,active INTEGER NOT NULL DEFAULT 0,paper TEXT NOT NULL DEFAULT '',developer TEXT NOT NULL DEFAULT '',developer_dilution TEXT NOT NULL DEFAULT '',stop_product TEXT NOT NULL DEFAULT '',stop_dilution TEXT NOT NULL DEFAULT '',fixer TEXT NOT NULL DEFAULT '',fixer_dilution TEXT NOT NULL DEFAULT '',volume_ml REAL,capacity_state TEXT NOT NULL DEFAULT '',source_snapshot TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS technical_source_cache (id INTEGER PRIMARY KEY AUTOINCREMENT,catalog_version INTEGER NOT NULL,source_key TEXT NOT NULL UNIQUE,origin_type TEXT NOT NULL,title TEXT NOT NULL DEFAULT '',author TEXT NOT NULL DEFAULT '',reference TEXT NOT NULL DEFAULT '',url TEXT NOT NULL DEFAULT '',document_version TEXT NOT NULL DEFAULT '',adaptation_note TEXT NOT NULL DEFAULT '',payload TEXT NOT NULL DEFAULT '',updated_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS assistant_sessions_by_updated ON assistant_sessions(updated_at);
CREATE INDEX IF NOT EXISTS paper_sessions_by_date ON paper_chemistry_sessions(created_at);
CREATE INDEX IF NOT EXISTS technical_sources_by_catalog ON technical_source_cache(catalog_version,source_key);
PRAGMA user_version=3;
'''

def scalar(db,q,args=()):return db.execute(q,args).fetchone()[0]

fd,path=tempfile.mkstemp(prefix='darkroom_v0110_',suffix='.db');os.close(fd)
try:
    db=sqlite3.connect(path);db.executescript(OLD_SCHEMA)
    # Representative persisted R4, R5 and R6 data from the actual v0.11 schema.
    db.execute("INSERT INTO personal_recipes(combo_key,film,format,nominal_iso,exposed_iso,developer,dilution,processor,method,original_temp,original_seconds,source_name,data_type,source_data,calculation,personal_temp,personal_seconds,note,favorite,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('foma|120|100|foma universal|1+3|jobo cpe2|rotazione continua','Fomapan 100','120',100,100,'FOMA Universal','1+3','JOBO CPE2','rotazione continua',20,255,'Foma','DATO ADATTATO / CALCOLATO','manuale 5:00','JOBO -15%',21,230,'ricetta R4',1,1,2))
    db.execute("INSERT INTO development_logs(created_at,combo_key,film,format,nominal_iso,exposed_iso,developer,dilution,actual_temp,processor,method,actual_seconds,time_origin,source_seconds,source_temp,source_name,data_type,source_data,calculation,volume_ml,product_ml,water_ml,product_known,water_known,rolls,capacity_state,capacity_message,rating,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(3,'k','Fomapan 100','120',100,100,'FOMA Universal','1+3',21,'JOBO CPE2','rotazione continua',230,'MIA RICETTA',255,20,'Foma','CALCOLO','5:00','-15%',340,85,255,1,1,1,'VERIFIED','ok',5,'log R4'))
    db.execute("INSERT INTO chemical_inventory(created_at,updated_at,source_type,manufacturer,name,category,physical_state,solution_type,initial_amount,remaining_amount,unit,notes,personal_dilution,source_name,data_type) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(4,5,'USER','Foma','FOMA Universal','RIVELATORE','polvere','stock',1000,915,'ml','R5','','Utente','DATO PERSONALE'))
    chem_id=db.execute('SELECT id FROM chemical_inventory').fetchone()[0]
    db.execute("INSERT INTO chemical_usage(created_at,chemical_id,development_log_id,product_name,developer,dilution,film,format,rolls,quantity_used,unit,remaining_after,note) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(6,chem_id,1,'FOMA Universal','FOMA Universal','1+3','Fomapan 100','120',1,85,'ml',915,'R5 usage'))
    db.execute("INSERT INTO personal_equipment(created_at,updated_at,category,source_type,source_model_key,manufacturer,model,personal_name,quantity_owned,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",(7,8,'TANK','CATALOG','jobo2520','JOBO','2520','Tank 2520',1,'R6'))
    tank_id=db.execute('SELECT id FROM personal_equipment').fetchone()[0]
    db.execute("INSERT INTO personal_tanks(equipment_id,system,tank_type,capacity_35,capacity_120,min_rotation_ml,max_volume_ml,cpe2_compatible,lift_compatible,technical_source,data_type) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(tank_id,'2500','modulare',2,2,270,600,1,1,'JOBO','DATO DOCUMENTATO'))
    db.commit()
    before={t:scalar(db,f'SELECT COUNT(*) FROM {t}') for t in ['personal_recipes','development_logs','chemical_inventory','chemical_usage','personal_equipment','personal_tanks']}
    assert scalar(db,'PRAGMA user_version')==2

    # Exact v0.12 migration is additive: no old table is recreated or deleted.
    db.executescript(NEW_SCHEMA);db.commit()
    assert scalar(db,'PRAGMA user_version')==3
    after={t:scalar(db,f'SELECT COUNT(*) FROM {t}') for t in before}
    assert before==after,(before,after)
    assert scalar(db,"SELECT COUNT(*) FROM personal_recipes WHERE note='ricetta R4'")==1
    assert scalar(db,"SELECT COUNT(*) FROM chemical_usage WHERE note='R5 usage'")==1
    assert scalar(db,"SELECT COUNT(*) FROM personal_tanks WHERE technical_source='JOBO'")==1
    for t in ['assistant_sessions','paper_chemistry_sessions','technical_source_cache']:assert scalar(db,"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",(t,))==1
    db.execute("INSERT INTO assistant_sessions(created_at,updated_at,session_key,film,planned_seconds,temperature,state) VALUES(?,?,?,?,?,?,?)",(9,10,'session-1','Fomapan 100',230,21.0,'PAUSED'))
    db.execute("INSERT INTO paper_chemistry_sessions(created_at,active,paper,developer,developer_dilution,volume_ml,capacity_state) VALUES(?,?,?,?,?,?,?)",(11,1,'Fomaspeed Variant 311','Paper dev','1+9',1000,None))
    db.execute("INSERT INTO technical_source_cache(catalog_version,source_key,origin_type,title,updated_at) VALUES(?,?,?,?,?)",(1,'source-1','FONTE UFFICIALE','Documentazione produttore',12));db.commit();db.close()

    # Reopen to prove persistence after migration and new R7/R8/R9 structures.
    db=sqlite3.connect(path);assert scalar(db,'PRAGMA user_version')==3
    assert {t:scalar(db,f'SELECT COUNT(*) FROM {t}') for t in before}==before
    assert scalar(db,"SELECT COUNT(*) FROM assistant_sessions WHERE state='PAUSED'")==1
    assert scalar(db,"SELECT COUNT(*) FROM paper_chemistry_sessions WHERE paper='Fomaspeed Variant 311'")==1
    assert scalar(db,"SELECT COUNT(*) FROM technical_source_cache WHERE origin_type='FONTE UFFICIALE'")==1
    db.close();print('SQLite migration v0.11 schema 2 -> v0.12 schema 3: R4/R5/R6 preserved; R7/R8/R9 persisted: OK')
finally:
    try:os.remove(path)
    except OSError:pass
