#!/usr/bin/env python3
import os,sqlite3,tempfile

OLD='''
CREATE TABLE personal_recipes(id INTEGER PRIMARY KEY,combo_key TEXT,film TEXT,format TEXT,nominal_iso INTEGER,exposed_iso INTEGER,developer TEXT,dilution TEXT,processor TEXT,method TEXT,original_temp REAL,original_seconds INTEGER,source_name TEXT,data_type TEXT,source_data TEXT,calculation TEXT,personal_temp REAL,personal_seconds INTEGER,note TEXT,favorite INTEGER,created_at INTEGER,updated_at INTEGER);
CREATE TABLE development_logs(id INTEGER PRIMARY KEY,created_at INTEGER,combo_key TEXT,film TEXT,format TEXT,nominal_iso INTEGER,exposed_iso INTEGER,developer TEXT,dilution TEXT,actual_temp REAL,processor TEXT,method TEXT,actual_seconds INTEGER,time_origin TEXT,source_seconds INTEGER,source_temp REAL,source_name TEXT,data_type TEXT,source_data TEXT,calculation TEXT,volume_ml REAL,product_ml REAL,water_ml REAL,product_known INTEGER,water_known INTEGER,rolls INTEGER,capacity_state TEXT,capacity_message TEXT,rating INTEGER,notes TEXT);
CREATE TABLE chemical_inventory(id INTEGER PRIMARY KEY,created_at INTEGER,updated_at INTEGER,source_type TEXT,source_product_key TEXT,manufacturer TEXT,name TEXT,category TEXT,physical_state TEXT,solution_type TEXT,initial_amount REAL,remaining_amount REAL,unit TEXT,purchase_date TEXT,open_date TEXT,prepared_date TEXT,expiry_date TEXT,notes TEXT,storage TEXT,personal_dilution TEXT,documented_dilutions TEXT,capacity_value REAL,capacity_unit TEXT,capacity_source TEXT,source_name TEXT,data_type TEXT,archived INTEGER);
CREATE TABLE chemical_usage(id INTEGER PRIMARY KEY,created_at INTEGER,chemical_id INTEGER,development_log_id INTEGER,product_name TEXT,developer TEXT,dilution TEXT,film TEXT,format TEXT,rolls INTEGER,quantity_used REAL,unit TEXT,remaining_after REAL,note TEXT);
CREATE TABLE personal_equipment(id INTEGER PRIMARY KEY,created_at INTEGER,updated_at INTEGER,category TEXT,source_type TEXT,source_model_key TEXT,manufacturer TEXT,model TEXT,personal_name TEXT,quantity_owned INTEGER,notes TEXT);
CREATE TABLE personal_tanks(equipment_id INTEGER PRIMARY KEY,system TEXT,tank_type TEXT,capacity_35 INTEGER,capacity_120 INTEGER,min_inversion_ml REAL,min_rotation_ml REAL,max_volume_ml REAL,cpe2_compatible INTEGER,lift_compatible INTEGER,technical_source TEXT,data_type TEXT);
PRAGMA user_version=2;
'''
NEW='''
CREATE TABLE IF NOT EXISTS assistant_sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,session_key TEXT NOT NULL UNIQUE,film TEXT NOT NULL DEFAULT '',format TEXT NOT NULL DEFAULT '',rolls INTEGER NOT NULL DEFAULT 0,cycle_index INTEGER NOT NULL DEFAULT 0,phase_index INTEGER NOT NULL DEFAULT 0,planned_seconds INTEGER,actual_seconds INTEGER,temperature REAL,tank_snapshot TEXT NOT NULL DEFAULT '',chemistry_snapshot TEXT NOT NULL DEFAULT '',state TEXT NOT NULL DEFAULT '',personal_phase_times TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS paper_chemistry_sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,active INTEGER NOT NULL DEFAULT 0,paper TEXT NOT NULL DEFAULT '',developer TEXT NOT NULL DEFAULT '',developer_dilution TEXT NOT NULL DEFAULT '',stop_product TEXT NOT NULL DEFAULT '',stop_dilution TEXT NOT NULL DEFAULT '',fixer TEXT NOT NULL DEFAULT '',fixer_dilution TEXT NOT NULL DEFAULT '',volume_ml REAL,capacity_state TEXT NOT NULL DEFAULT '',source_snapshot TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS technical_source_cache(id INTEGER PRIMARY KEY AUTOINCREMENT,catalog_version INTEGER NOT NULL,source_key TEXT NOT NULL UNIQUE,origin_type TEXT NOT NULL,title TEXT NOT NULL DEFAULT '',author TEXT NOT NULL DEFAULT '',reference TEXT NOT NULL DEFAULT '',url TEXT NOT NULL DEFAULT '',document_version TEXT NOT NULL DEFAULT '',adaptation_note TEXT NOT NULL DEFAULT '',payload TEXT NOT NULL DEFAULT '',updated_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS assistant_sessions_by_updated ON assistant_sessions(updated_at);
CREATE INDEX IF NOT EXISTS paper_sessions_by_date ON paper_chemistry_sessions(created_at);
CREATE INDEX IF NOT EXISTS technical_sources_by_catalog ON technical_source_cache(catalog_version,source_key);
PRAGMA user_version=3;
'''

def count(db,t):return db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
fd,path=tempfile.mkstemp(prefix='darkroom-v0110-',suffix='.db');os.close(fd)
try:
    db=sqlite3.connect(path);db.executescript(OLD)
    db.execute("INSERT INTO personal_recipes VALUES(1,'combo','Fomapan 100','120',100,100,'FOMA Universal','1+3','JOBO CPE2','rotazione continua',20,255,'Foma','DATO ADATTATO / CALCOLATO','manuale 5:00','JOBO -15%',21,230,'R4 recipe',1,1,2)")
    db.execute("INSERT INTO development_logs VALUES(1,3,'combo','Fomapan 100','120',100,100,'FOMA Universal','1+3',21,'JOBO CPE2','rotazione continua',230,'MIA RICETTA',255,20,'Foma','CALCOLO','5:00','-15%',340,85,255,1,1,1,'VERIFIED','ok',5,'R4 log')")
    db.execute("INSERT INTO chemical_inventory VALUES(1,4,5,'USER','','Foma','FOMA Universal','RIVELATORE','polvere','stock',1000,915,'ml','','','','','R5','','','','0','','','Utente','DATO PERSONALE',0)")
    db.execute("INSERT INTO chemical_usage VALUES(1,6,1,1,'FOMA Universal','FOMA Universal','1+3','Fomapan 100','120',1,85,'ml',915,'R5 usage')")
    db.execute("INSERT INTO personal_equipment VALUES(1,7,8,'TANK','CATALOG','jobo2520','JOBO','2520','Tank 2520',1,'R6')")
    db.execute("INSERT INTO personal_tanks VALUES(1,'2500','modulare',2,2,0,270,600,1,1,'JOBO','DATO DOCUMENTATO')")
    db.commit();old_tables=['personal_recipes','development_logs','chemical_inventory','chemical_usage','personal_equipment','personal_tanks'];before={t:count(db,t) for t in old_tables};assert db.execute('PRAGMA user_version').fetchone()[0]==2
    db.executescript(NEW);db.commit();assert db.execute('PRAGMA user_version').fetchone()[0]==3;assert {t:count(db,t) for t in old_tables}==before
    db.execute("INSERT INTO assistant_sessions(created_at,updated_at,session_key,film,planned_seconds,temperature,state) VALUES(9,10,'s1','Fomapan 100',230,21,'PAUSED')")
    db.execute("INSERT INTO paper_chemistry_sessions(created_at,active,paper,developer,developer_dilution,volume_ml,capacity_state) VALUES(11,1,'Fomaspeed Variant 311','Paper dev','1+9',1000,'')")
    db.execute("INSERT INTO technical_source_cache(catalog_version,source_key,origin_type,title,updated_at) VALUES(1,'src1','FONTE UFFICIALE','Documentazione produttore',12)");db.commit();db.close()
    db=sqlite3.connect(path);assert db.execute('PRAGMA user_version').fetchone()[0]==3;assert {t:count(db,t) for t in old_tables}==before;assert count(db,'assistant_sessions')==1;assert count(db,'paper_chemistry_sessions')==1;assert count(db,'technical_source_cache')==1;assert db.execute("SELECT note FROM personal_recipes WHERE id=1").fetchone()[0]=='R4 recipe';assert db.execute("SELECT note FROM chemical_usage WHERE id=1").fetchone()[0]=='R5 usage';assert db.execute("SELECT technical_source FROM personal_tanks WHERE equipment_id=1").fetchone()[0]=='JOBO';db.close()
    print('SQLite v0.11 schema 2 -> v0.12 schema 3: R4/R5/R6 preserved; R7/R8/R9 persisted: OK')
finally:
    try:os.remove(path)
    except OSError:pass
