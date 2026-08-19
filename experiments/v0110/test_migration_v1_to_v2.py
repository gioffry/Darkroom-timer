#!/usr/bin/env python3
import sqlite3, tempfile, os

fd,path=tempfile.mkstemp(prefix='darkroom-v1-',suffix='.db'); os.close(fd)
try:
    db=sqlite3.connect(path)
    # Minimal exact v1-compatible columns used by R4 persistence.
    db.executescript('''
    PRAGMA user_version=1;
    CREATE TABLE personal_recipes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,combo_key TEXT NOT NULL,film TEXT NOT NULL,format TEXT NOT NULL,
      nominal_iso INTEGER NOT NULL,exposed_iso INTEGER NOT NULL,developer TEXT NOT NULL,dilution TEXT NOT NULL,
      processor TEXT NOT NULL,method TEXT NOT NULL,original_temp REAL NOT NULL,original_seconds INTEGER NOT NULL,
      source_name TEXT NOT NULL,data_type TEXT NOT NULL,source_data TEXT NOT NULL,calculation TEXT NOT NULL,
      personal_temp REAL NOT NULL,personal_seconds INTEGER NOT NULL,note TEXT NOT NULL DEFAULT '',favorite INTEGER NOT NULL DEFAULT 0,
      created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);
    CREATE TABLE development_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,combo_key TEXT NOT NULL,film TEXT NOT NULL,format TEXT NOT NULL,
      nominal_iso INTEGER NOT NULL,exposed_iso INTEGER NOT NULL,developer TEXT NOT NULL,dilution TEXT NOT NULL,actual_temp REAL NOT NULL,
      processor TEXT NOT NULL,method TEXT NOT NULL,actual_seconds INTEGER NOT NULL,time_origin TEXT NOT NULL,source_seconds INTEGER NOT NULL,
      source_temp REAL NOT NULL,source_name TEXT NOT NULL,data_type TEXT NOT NULL,source_data TEXT NOT NULL,calculation TEXT NOT NULL,
      volume_ml REAL NOT NULL DEFAULT 0,product_ml REAL NOT NULL DEFAULT 0,water_ml REAL NOT NULL DEFAULT 0,rolls INTEGER NOT NULL DEFAULT 1,
      capacity_state TEXT NOT NULL DEFAULT '',capacity_message TEXT NOT NULL DEFAULT '',rating INTEGER NOT NULL DEFAULT 0,notes TEXT NOT NULL DEFAULT '');
    ''')
    common=('foma100|120|100|foma universal|1+3|jobo cpe2|rotazione continua','Fomapan 100','120',100,100,'FOMA Universal','1+3','JOBO CPE2','rotazione continua')
    db.execute('INSERT INTO personal_recipes(combo_key,film,format,nominal_iso,exposed_iso,developer,dilution,processor,method,original_temp,original_seconds,source_name,data_type,source_data,calculation,personal_temp,personal_seconds,note,favorite,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',common+(20.0,255,'source','DATO DIRETTO','x','x',20.0,250,'mia',1,1,1))
    # Known old log: 85+255. Unknown old log: historical R4 sentinel 0+0.
    base=(1,common[0],common[1],common[2],100,100,common[5],common[6],20.0,'JOBO CPE2','rotazione continua',250,'FONTE',255,20.0,'source','DATO DIRETTO','x','x',340.0)
    db.execute('INSERT INTO development_logs(created_at,combo_key,film,format,nominal_iso,exposed_iso,developer,dilution,actual_temp,processor,method,actual_seconds,time_origin,source_seconds,source_temp,source_name,data_type,source_data,calculation,volume_ml,product_ml,water_ml,rolls,capacity_state,capacity_message,rating,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',base+(85.0,255.0,1,'VERIFIED','ok',5,'known'))
    db.execute('INSERT INTO development_logs(created_at,combo_key,film,format,nominal_iso,exposed_iso,developer,dilution,actual_temp,processor,method,actual_seconds,time_origin,source_seconds,source_temp,source_name,data_type,source_data,calculation,volume_ml,product_ml,water_ml,rolls,capacity_state,capacity_message,rating,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',base+(0.0,0.0,1,'UNKNOWN','unknown',3,'unknown'))
    db.commit()

    # v2 migration mirrors AssistantDatabase.onUpgrade. No DROP, no destructive rebuild.
    db.executescript('''
    ALTER TABLE development_logs ADD COLUMN product_known INTEGER NOT NULL DEFAULT 0;
    ALTER TABLE development_logs ADD COLUMN water_known INTEGER NOT NULL DEFAULT 0;
    UPDATE development_logs SET product_known=1,water_known=1 WHERE product_ml>0 OR water_ml>0;
    CREATE TABLE IF NOT EXISTS chemical_inventory (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,source_type TEXT NOT NULL,source_product_key TEXT NOT NULL DEFAULT '',manufacturer TEXT NOT NULL DEFAULT '',name TEXT NOT NULL,category TEXT NOT NULL,physical_state TEXT NOT NULL,solution_type TEXT NOT NULL,initial_amount REAL NOT NULL DEFAULT 0,remaining_amount REAL NOT NULL DEFAULT 0,unit TEXT NOT NULL,purchase_date TEXT NOT NULL DEFAULT '',open_date TEXT NOT NULL DEFAULT '',prepared_date TEXT NOT NULL DEFAULT '',expiry_date TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '',storage TEXT NOT NULL DEFAULT '',personal_dilution TEXT NOT NULL DEFAULT '',documented_dilutions TEXT NOT NULL DEFAULT '',capacity_value REAL NOT NULL DEFAULT 0,capacity_unit TEXT NOT NULL DEFAULT '',capacity_source TEXT NOT NULL DEFAULT '',source_name TEXT NOT NULL DEFAULT '',data_type TEXT NOT NULL DEFAULT '',archived INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS chemical_usage (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,chemical_id INTEGER NOT NULL,development_log_id INTEGER NOT NULL DEFAULT 0,product_name TEXT NOT NULL,developer TEXT NOT NULL DEFAULT '',dilution TEXT NOT NULL DEFAULT '',film TEXT NOT NULL DEFAULT '',format TEXT NOT NULL DEFAULT '',rolls INTEGER NOT NULL DEFAULT 0,quantity_used REAL NOT NULL,unit TEXT NOT NULL,remaining_after REAL NOT NULL,note TEXT NOT NULL DEFAULT '');
    CREATE TABLE IF NOT EXISTS personal_equipment (id INTEGER PRIMARY KEY AUTOINCREMENT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,category TEXT NOT NULL,source_type TEXT NOT NULL,source_model_key TEXT NOT NULL DEFAULT '',manufacturer TEXT NOT NULL DEFAULT '',model TEXT NOT NULL,personal_name TEXT NOT NULL DEFAULT '',quantity_owned INTEGER NOT NULL DEFAULT 1,notes TEXT NOT NULL DEFAULT '');
    CREATE TABLE IF NOT EXISTS personal_tanks (equipment_id INTEGER PRIMARY KEY,system TEXT NOT NULL DEFAULT '',tank_type TEXT NOT NULL DEFAULT '',capacity_35 INTEGER NOT NULL DEFAULT 0,capacity_120 INTEGER NOT NULL DEFAULT 0,min_inversion_ml REAL NOT NULL DEFAULT 0,min_rotation_ml REAL NOT NULL DEFAULT 0,max_volume_ml REAL NOT NULL DEFAULT 0,cpe2_compatible INTEGER NOT NULL DEFAULT 0,lift_compatible INTEGER NOT NULL DEFAULT 0,technical_source TEXT NOT NULL DEFAULT '',data_type TEXT NOT NULL DEFAULT '');
    PRAGMA user_version=2;
    ''')

    assert db.execute('SELECT personal_seconds,note,favorite FROM personal_recipes').fetchone()==(250,'mia',1)
    logs=db.execute('SELECT product_ml,water_ml,product_known,water_known,notes FROM development_logs ORDER BY id').fetchall()
    assert logs[0]==(85.0,255.0,1,1,'known')
    assert logs[1]==(0.0,0.0,0,0,'unknown'), logs[1]
    names={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for n in ('personal_recipes','development_logs','chemical_inventory','chemical_usage','personal_equipment','personal_tanks'): assert n in names

    db.execute("INSERT INTO chemical_inventory(created_at,updated_at,source_type,name,category,physical_state,solution_type,initial_amount,remaining_amount,unit) VALUES (1,1,'USER','Test','altro','liquido','concentrato',100,80,'ml')")
    chem_id=db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.execute("INSERT INTO chemical_usage(created_at,chemical_id,development_log_id,product_name,quantity_used,unit,remaining_after) VALUES (2,?,1,'Test',20,'ml',60)",(chem_id,))
    db.execute("INSERT INTO personal_equipment(created_at,updated_at,category,source_type,manufacturer,model) VALUES (1,1,'TANK','USER','X','Y')")
    eq=db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.execute("INSERT INTO personal_tanks(equipment_id,capacity_35,min_rotation_ml,cpe2_compatible) VALUES (?,2,270,1)",(eq,))
    db.commit(); db.close()

    db=sqlite3.connect(path)
    assert db.execute('SELECT remaining_amount FROM chemical_inventory WHERE id=?',(chem_id,)).fetchone()[0]==80
    assert db.execute('SELECT quantity_used,remaining_after FROM chemical_usage WHERE chemical_id=?',(chem_id,)).fetchone()==(20.0,60.0)
    assert db.execute('SELECT capacity_35,min_rotation_ml FROM personal_tanks WHERE equipment_id=?',(eq,)).fetchone()==(2,270.0)
    assert db.execute('PRAGMA user_version').fetchone()[0]==2
    print('v0.11.0 SQLite migration v1 -> v2: OK; R4 data preserved, UNKNOWN remains semantic UNKNOWN, R5/R6 persistence OK')
finally:
    try: os.unlink(path)
    except FileNotFoundError: pass
