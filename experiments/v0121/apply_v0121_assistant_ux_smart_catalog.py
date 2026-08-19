#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,shutil,sys

work=Path(sys.argv[1]); project=work/'project'; app=project/'app'; java=app/'src/main/java/it/darkroom/timer'
main=java/'MainActivity.java'; newdev=java/'assistant/development/NewDevelopmentActivity.java'; planner=java/'assistant/equipment/TankPlanner.java'; backup=java/'assistant/system/BackupEngine.java'; manifest=app/'src/main/AndroidManifest.xml'; gradle=app/'build.gradle'; build=work/'build_darkroom.py'; here=Path(__file__).parent

def rd(p):return Path(p).read_text(encoding='utf-8')
def wr(p,s):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(s,encoding='utf-8')
def rep(p,old,new,label,count=1):
    s=rd(p);n=s.count(old)
    if n<count:raise SystemExit(f'v0.12.1 {label}: atteso >= {count}, trovato {n}')
    wr(p,s.replace(old,new,count));print('v0.12.1 OK',label,flush=True)
def rrep(p,pat,new,label,count=1,flags=re.S):
    s=rd(p);out,n=re.subn(pat,new,s,count=count,flags=flags)
    if n!=count:raise SystemExit(f'v0.12.1 {label}: regex {n}, attesa {count}')
    wr(p,out);print('v0.12.1 OK',label,flush=True)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# Protect the exact materialized v0.12.0 base before any v0.12.1 changes.
for p,needle in [(manifest,'android:versionName="0.12.0"'),(manifest,'android:versionCode="57"'),(main,'private static final String APP_VERSION = "0.12.0";'),(backup,'public static final String APP_VERSION="0.12.0";')]:
    if needle not in rd(p):raise SystemExit('BASE v0.12.0 non riconosciuta: '+needle)
if 'testFromPrint' in rd(main) or 'NUOVO PROVINO DA QUESTA STAMPA' in rd(main):raise SystemExit('BASE v0.12.0 regressa: STAMPA->PROVINO presente')
protected={p.name:sha(p) for p in java.glob('*.java') if p.name!='MainActivity.java'}
main_before=rd(main)

# Version only in build/manifest/Timer footer. Package and Timer behavior stay intact.
rep(build,'VERSION_NAME = "0.12.0"','VERSION_NAME = "0.12.1"','build VERSION_NAME')
rep(build,'VERSION_CODE = "57"','VERSION_CODE = "58"','build VERSION_CODE')
s=rd(build).replace('[Darkroom v0.12.0]','[Darkroom v0.12.1]').replace('versionCode 57','versionCode 58').replace('0.12.0','0.12.1')
# v0.12.0 builder also contains a raw-regex preflight with a literal 57; update it only in the v0.12.1 working copy.
s=s.replace(r'versionCode\s+57\b',r'versionCode\s+58\b')
wr(build,s)
rep(gradle,"versionCode 57\n        versionName '0.12.0'","versionCode 58\n        versionName '0.12.1'",'Gradle version')
rep(manifest,'android:versionCode="57"\n    android:versionName="0.12.0"','android:versionCode="58"\n    android:versionName="0.12.1"','manifest version')
rep(main,'private static final String APP_VERSION = "0.12.0";','private static final String APP_VERSION = "0.12.1";','Timer footer version')

# Copy the reusable UX/search implementations. Nothing in the Timer package is overwritten.
src=here/'src'
for p in src.rglob('*.java'):
    rel=p.relative_to(src);dst=app/'src/main/java'/rel;wr(dst,rd(p));print('v0.12.1 source',rel,flush=True)
raw=app/'src/main/res/raw/catalog_v2.json';wr(raw,rd(here/'catalog-v2.json'));print('v0.12.1 OK bundled catalog v2',flush=True)

# Backup metadata follows app/catalog version; DB format remains v3 because no personal-table change is required.
backup=java/'assistant/system/BackupEngine.java'
rep(backup,'public static final int CATALOG_VERSION=1;','public static final int CATALOG_VERSION=2;','backup catalog version')
rep(backup,'public static final String APP_VERSION="0.12.0";','public static final String APP_VERSION="0.12.1";','backup app version')
rep(backup,'public static final int VERSION_CODE=57;','public static final int VERSION_CODE=58;','backup versionCode')

# Manifest: dedicated search and owned-tank picker activities.
anchor='''        <activity\n            android:name=".assistant.system.DataManagementActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />'''
addition=anchor+'''\n\n        <activity\n            android:name=".assistant.search.SmartSearchActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n\n        <activity\n            android:name=".assistant.equipment.OwnedTankPickerActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />'''
rep(manifest,anchor,addition,'manifest Smart Search activities')

# New Development: keep all technical calculations, replace only selection UX/canonicalization.
newdev=java/'assistant/development/NewDevelopmentActivity.java'
rep(newdev,'    private String selectedFormat = "120";','    private String selectedFormat = "120";\n    private static final int PICK_FILM_CATALOG=7211, PICK_DEVELOPER_CATALOG=7212, PICK_OWNED_TANK=7213;','New Development request codes')
film_old='''        filmField=autoField("Cerca o seleziona pellicola");\n        filmField.setAdapter(adapter(DevelopmentCatalog.filmNames()));\n        root.addView(filmField, lp(-1,dp(52)));\n        filmField.setOnClickListener(v -> filmField.showDropDown());\n        filmField.setOnFocusChangeListener((v,has) -> { if(has) filmField.showDropDown(); });\n        filmField.setOnItemClickListener((p,v,pos,id) -> onFilmChanged());'''
film_new='''        filmField=autoField("Cerca pellicola · es. hp5, tri x, foma 2");\n        root.addView(filmField, lp(-1,dp(52)));\n        it.darkroom.timer.assistant.search.SmartSearchBinder.attach(this,filmField,"FILM",item -> onFilmChanged());\n        Button filmCatalog=smallChoice("CERCA CATALOGO");\n        filmCatalog.setOnClickListener(v -> openSmartCatalog(PICK_FILM_CATALOG,"CERCA PELLICOLA","FILM",filmField.getText().toString()));\n        root.addView(filmCatalog,margin(lp(-1,dp(46)),0,5,0,0));'''
rep(newdev,film_old,film_new,'Smart Search pellicola')
dev_old='''        developerField=autoField("Scelta indipendente dalla marca");\n        developerField.setAdapter(adapter(DevelopmentCatalog.developerNames())); root.addView(developerField,lp(-1,dp(52)));\n        developerField.setOnClickListener(v -> developerField.showDropDown());\n        developerField.setOnFocusChangeListener((v,has) -> { if(has) developerField.showDropDown(); });\n        developerField.setOnItemClickListener((p,v,pos,id) -> refreshDilutions());'''
dev_new='''        developerField=autoField("Cerca rivelatore · es. d76, foma un");\n        root.addView(developerField,lp(-1,dp(52)));\n        it.darkroom.timer.assistant.search.SmartSearchBinder.attach(this,developerField,"FILM_DEVELOPER",item -> refreshDilutions());\n        Button developerCatalog=smallChoice("CERCA CATALOGO");\n        developerCatalog.setOnClickListener(v -> openSmartCatalog(PICK_DEVELOPER_CATALOG,"CERCA RIVELATORE","FILM_DEVELOPER",developerField.getText().toString()));\n        root.addView(developerCatalog,margin(lp(-1,dp(46)),0,5,0,0));'''
rep(newdev,dev_old,dev_new,'Smart Search rivelatore')
rep(newdev,'DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(filmField.getText().toString());','String canonical=it.darkroom.timer.assistant.search.SmartSearchBinder.canonical(this,filmField.getText().toString(),"FILM");\n        DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(canonical);','canonical film selection',1)
rep(newdev,'String[] values=DevelopmentCatalog.availableDilutions(filmField.getText().toString(),ei,developerField.getText().toString());','String filmName=it.darkroom.timer.assistant.search.SmartSearchBinder.canonical(this,filmField.getText().toString(),"FILM");\n        String developerName=it.darkroom.timer.assistant.search.SmartSearchBinder.canonical(this,developerField.getText().toString(),"FILM_DEVELOPER");\n        String[] values=DevelopmentCatalog.availableDilutions(filmName,ei,developerName);','canonical dilution lookup')
# The second DevelopmentCatalog.findFilm occurrence is calculate().
rep(newdev,'DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(filmField.getText().toString());','String canonicalFilm=it.darkroom.timer.assistant.search.SmartSearchBinder.canonical(this,filmField.getText().toString(),"FILM");\n        String canonicalDeveloper=it.darkroom.timer.assistant.search.SmartSearchBinder.canonical(this,developerField.getText().toString(),"FILM_DEVELOPER");\n        DevelopmentCatalog.Film film=DevelopmentCatalog.findFilm(canonicalFilm);','canonical calculate inputs',1)
rep(newdev,'developerField.getText().toString(),dilutionField.getText().toString(),temp);','canonicalDeveloper,dilutionField.getText().toString(),temp);','calculate canonical developer')

rrep(newdev,r'    private void chooseTankManual\(\) \{.*?\n    \}\n\n    private void chooseTankBest\(\)', '''    private void chooseTankManual() {\n        startActivityForResult(new Intent(this,it.darkroom.timer.assistant.equipment.OwnedTankPickerActivity.class),PICK_OWNED_TANK);\n    }\n\n    private void chooseTankBest()''','modern owned-tank picker')
rep(newdev,'if(!p.ok){ selectedTankId=0; selectedTankPlan=p.problem; tankChoice.setText(p.problem); new android.app.AlertDialog.Builder(this).setTitle("TANK MIGLIORE").setMessage(p.problem).setPositiveButton("OK",null).show(); return; }','if(!p.ok){ selectedTankId=0; selectedTankPlan=p.problem; tankChoice.setText(p.problem); toast(p.problem); return; }','tank best failure inline')
rep(newdev,'new android.app.AlertDialog.Builder(this).setTitle("TANK MIGLIORE").setMessage(p.summary()).setPositiveButton("USA QUESTA",null).show();','toast("Tank migliore: "+p.tank.displayName());','tank best success inline')

insert='''    private void openSmartCatalog(int request,String title,String categories,String query){\n        Intent i=new Intent(this,it.darkroom.timer.assistant.search.SmartSearchActivity.class);\n        i.putExtra(it.darkroom.timer.assistant.search.SmartSearchActivity.EXTRA_TITLE,title);\n        i.putExtra(it.darkroom.timer.assistant.search.SmartSearchActivity.EXTRA_HINT,"Inizia a scrivere…");\n        i.putExtra(it.darkroom.timer.assistant.search.SmartSearchActivity.EXTRA_CATEGORIES,categories);\n        i.putExtra(it.darkroom.timer.assistant.search.SmartSearchActivity.EXTRA_QUERY,query);\n        i.putExtra(it.darkroom.timer.assistant.search.SmartSearchActivity.EXTRA_ALLOW_MANUAL,false);\n        startActivityForResult(i,request);\n    }\n\n    @Override protected void onActivityResult(int request,int result,Intent data){\n        super.onActivityResult(request,result,data);if(result!=RESULT_OK||data==null)return;\n        if(request==PICK_FILM_CATALOG){String name=data.getStringExtra(it.darkroom.timer.assistant.search.SmartSearchActivity.RESULT_NAME);if(name!=null){filmField.setText(name,false);onFilmChanged();}}\n        else if(request==PICK_DEVELOPER_CATALOG){String name=data.getStringExtra(it.darkroom.timer.assistant.search.SmartSearchActivity.RESULT_NAME);if(name!=null){developerField.setText(name,false);refreshDilutions();}}\n        else if(request==PICK_OWNED_TANK){selectedTankId=data.getLongExtra(it.darkroom.timer.assistant.equipment.OwnedTankPickerActivity.RESULT_ID,0);String name=data.getStringExtra(it.darkroom.timer.assistant.equipment.OwnedTankPickerActivity.RESULT_NAME);selectedTankPlan="Scelta manuale · "+(name==null?"tank":name);tankChoice.setText(selectedTankPlan);}\n    }\n\n'''
rep(newdev,'    private void calculate() {',insert+'    private void calculate() {','New Development picker results')

# Unknown compatibility is not the same thing as incompatibility. Only confirmed CPE2 tanks are auto-selected.
rep(planner,'if(!t.cpe2Compatible){append(rejected,t.displayName()+": non compatibile con JOBO CPE2");continue;}','if(!t.cpe2Compatible){append(rejected,t.displayName()+": compatibilità JOBO CPE2 non documentata / non confermata; esclusa dalla scelta automatica");continue;}','TankPlanner UNKNOWN compatibility semantics')

# Regression guards: root Timer classes unchanged except APP_VERSION display in MainActivity.
for name,h in protected.items():
    p=java/name
    if sha(p)!=h:raise SystemExit('v0.12.1 Timer regression: '+name+' changed')
expected=main_before.replace('private static final String APP_VERSION = "0.12.0";','private static final String APP_VERSION = "0.12.1";',1)
if rd(main)!=expected:raise SystemExit('v0.12.1 MainActivity changed beyond version bump')
if 'package="it.darkroom.timer"' not in rd(manifest):raise SystemExit('package changed')
if 'public static final int VERSION = 3;' not in rd(java/'assistant/data/AssistantDataSchema.java'):raise SystemExit('DB schema unexpectedly changed')
print('v0.12.1 TRANSFORM OK — Timer protected; Assistant UX/Smart Catalog applied',flush=True)
