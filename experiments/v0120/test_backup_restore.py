#!/usr/bin/env python3
import hashlib,json,sqlite3,tempfile,os,copy

FORMAT=1

def checksum(payload):return hashlib.sha256(json.dumps(payload,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def make_backup(payload):return {'backupFormatVersion':FORMAT,'appVersion':'0.12.0','versionCode':57,'databaseSchemaVersion':3,'catalogVersion':1,'createdAt':123,'payload':payload,'payloadSha256':checksum(payload)}
def validate(root):
    if root.get('backupFormatVersion')!=FORMAT:return False
    if not 1<=root.get('databaseSchemaVersion',-1)<=3:return False
    return root.get('payloadSha256')==checksum(root.get('payload',{}))

payload={'tables':{'personal_recipes':[{'id':1,'name':'R4'}],'chemical_inventory':[{'id':1,'name':'R5'}],'personal_equipment':[{'id':1,'model':'R6'}],'assistant_sessions':[{'id':1,'state':'PAUSED'}],'paper_chemistry_sessions':[{'id':1,'paper':'Fomaspeed Variant 311'}]},'preferences':{'ui':{'splitSoftYellow':50,'splitHardMagenta':160},'assistant_settings':{'voice':True}}}
root=make_backup(payload)
assert validate(root)
corrupt=copy.deepcopy(root);corrupt['payload']['tables']['personal_recipes'][0]['name']='tampered';assert not validate(corrupt),'corrupted payload accepted'
wrong=copy.deepcopy(root);wrong['backupFormatVersion']=99;assert not validate(wrong),'unsupported format accepted'

fd,path=tempfile.mkstemp(prefix='darkroom_backup_',suffix='.db');os.close(fd)
try:
    db=sqlite3.connect(path)
    db.executescript('''CREATE TABLE personal_recipes(id INTEGER PRIMARY KEY,name TEXT UNIQUE);CREATE TABLE chemical_inventory(id INTEGER PRIMARY KEY,name TEXT UNIQUE);CREATE TABLE personal_equipment(id INTEGER PRIMARY KEY,model TEXT UNIQUE);CREATE TABLE assistant_sessions(id INTEGER PRIMARY KEY,state TEXT);CREATE TABLE paper_chemistry_sessions(id INTEGER PRIMARY KEY,paper TEXT);''')
    db.execute("INSERT INTO personal_recipes VALUES(2,'existing')");db.commit()
    # MERGE: existing row survives; new non-conflicting rows are added.
    db.execute('BEGIN')
    for table,rows in payload['tables'].items():
        for row in rows:
            cols=list(row);q=','.join('?' for _ in cols);db.execute(f"INSERT OR IGNORE INTO {table}({','.join(cols)}) VALUES({q})",[row[k] for k in cols])
    db.commit()
    assert db.execute('SELECT COUNT(*) FROM personal_recipes').fetchone()[0]==2
    assert db.execute("SELECT COUNT(*) FROM paper_chemistry_sessions WHERE paper='Fomaspeed Variant 311'").fetchone()[0]==1

    # Simulate an atomic REPLACE failure: DELETE + bad INSERT must roll back together.
    before=list(db.execute('SELECT id,name FROM personal_recipes ORDER BY id'))
    try:
        db.execute('BEGIN');db.execute('DELETE FROM personal_recipes');db.execute("INSERT INTO personal_recipes VALUES(3,'new')");db.execute("INSERT INTO personal_recipes VALUES(4,'new')");db.commit()
        raise AssertionError('duplicate should have failed')
    except sqlite3.IntegrityError:
        db.rollback()
    after=list(db.execute('SELECT id,name FROM personal_recipes ORDER BY id'));assert before==after,(before,after)
    db.close()
    print('Backup format/checksum/corruption rejection + MERGE + transactional REPLACE rollback: OK')
finally:
    try:os.remove(path)
    except OSError:pass
