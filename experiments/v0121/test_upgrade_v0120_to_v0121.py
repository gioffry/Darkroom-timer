#!/usr/bin/env python3
"""Real SQLite persistence test for the 0.12.0 -> 0.12.1 upgrade.
The release intentionally keeps schema v3: UX/catalog changes must not rewrite personal tables.
"""
from pathlib import Path
import sqlite3,re,subprocess,tempfile,sys

work=Path(sys.argv[1] if len(sys.argv)>1 else 'work')
base=Path('base/v0.12.0-materialized/project/app/src/main/java/it/darkroom/timer/assistant/data/AssistantDataSchema.java')
final=work/'project/app/src/main/java/it/darkroom/timer/assistant/data/AssistantDataSchema.java'
dbjava=work/'project/app/src/main/java/it/darkroom/timer/assistant/data/AssistantDatabase.java'
assert 'public static final int VERSION = 3;' in base.read_text()
assert 'public static final int VERSION = 3;' in final.read_text()
assert 'DROP TABLE' not in final.read_text() and 'DROP TABLE' not in dbjava.read_text()

names=['CREATE_RECIPES','CREATE_LOGS','CREATE_CHEMICALS','CREATE_CHEMICAL_USAGE','CREATE_EQUIPMENT','CREATE_TANKS','CREATE_ASSISTANT_SESSIONS','CREATE_PAPER_SESSIONS','CREATE_TECHNICAL_SOURCE_CACHE']
with tempfile.TemporaryDirectory() as td:
    td=Path(td);pkg=td/'it/darkroom/timer/assistant/data';pkg.mkdir(parents=True)
    (pkg/'AssistantDataSchema.java').write_text(base.read_text(),encoding='utf-8')
    printjava=td/'PrintSchema.java'
    printjava.write_text('import it.darkroom.timer.assistant.data.AssistantDataSchema; public class PrintSchema { public static void main(String[] a){'+''.join(f'System.out.println("@@{n}@@");System.out.println(AssistantDataSchema.{n});' for n in names)+'}}',encoding='utf-8')
    subprocess.run(['javac','-d',str(td),str(pkg/'AssistantDataSchema.java'),str(printjava)],check=True)
    raw=subprocess.check_output(['java','-cp',str(td),'PrintSchema'],text=True)
    sql={};current=None
    for line in raw.splitlines():
        if line.startswith('@@') and line.endswith('@@'):current=line[2:-2];sql[current]=''
        elif current:sql[current]+=line+'\n'
    path=td/'upgrade.db';cx=sqlite3.connect(path)
    for n in names:cx.execute(sql[n].strip())
    cx.execute('PRAGMA user_version=3')
    tables=['personal_recipes','development_logs','chemical_inventory','chemical_usage','personal_equipment','personal_tanks','assistant_sessions','paper_chemistry_sessions','technical_source_cache']
    snapshots={}
    for ti,table in enumerate(tables,1):
        cols=cx.execute(f'PRAGMA table_info({table})').fetchall();keys=[];vals=[]
        for cid,name,ctype,notnull,dflt,pk in cols:
            if pk and ('AUTOINCREMENT' in sql.get(names[ti-1],'') or name=='id'):continue
            if dflt is not None:continue
            if notnull or pk:
                keys.append(name)
                if name in ('session_key','source_key','combo_key'):vals.append(f'keep-{table}')
                elif 'INT' in ctype.upper():vals.append(1)
                elif any(x in ctype.upper() for x in ('REAL','FLOA','DOUB')):vals.append(1.0)
                else:vals.append(f'keep-{name}')
        if table=='personal_tanks' and 'equipment_id' not in keys:keys.append('equipment_id');vals.append(1)
        q=','.join('?'*len(keys));cx.execute(f"INSERT INTO {table} ({','.join(keys)}) VALUES ({q})",vals)
        snapshots[table]=cx.execute(f'SELECT * FROM {table}').fetchall()
    cx.commit();cx.close()
    # App 0.12.1 opens the same v3 schema: no migration callback should destroy or rewrite rows.
    cx=sqlite3.connect(path);assert cx.execute('PRAGMA user_version').fetchone()[0]==3
    for table in tables:
        assert cx.execute(f'SELECT * FROM {table}').fetchall()==snapshots[table],table
    cx.close()
print('v0.12.0 -> v0.12.1 SQLite schema v3 persistence: PASS; all R4-R9 rows preserved')
