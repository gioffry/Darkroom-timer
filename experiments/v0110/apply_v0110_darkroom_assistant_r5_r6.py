#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

work=Path(sys.argv[1]); project=work/'project'; java=project/'app/src/main/java/it/darkroom/timer'
main=java/'MainActivity.java'; build=work/'build_darkroom.py'; gradle=project/'app/build.gradle'; manifest=project/'app/src/main/AndroidManifest.xml'
assistant=java/'assistant/AssistantActivity.java'; newdev=java/'assistant/development/NewDevelopmentActivity.java'; result=java/'assistant/development/DevelopmentResultActivity.java'; log=java/'assistant/log/DevelopmentLogActivity.java'; here=Path(__file__).parent

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(s,encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rep(p,o,n,label,c=1):
    s=rd(p); k=s.count(o)
    if k<c: raise SystemExit(f'v0.11.0 {label}: atteso >= {c}, trovato {k}')
    wr(p,s.replace(o,n,c)); print('v0.11.0 OK',label,flush=True)
def replace_between(p,start,end,new,label):
    s=rd(p); a=s.find(start)
    if a<0: raise SystemExit(f'v0.11.0 {label}: start non trovato')
    b=s.find(end,a)
    if b<0: raise SystemExit(f'v0.11.0 {label}: end non trovato')
    wr(p,s[:a]+new+s[b:]); print('v0.11.0 OK',label,flush=True)

# Exact v0.10.10 Timer baseline guard.
timer_before={p.name:sha(p) for p in java.glob('*.java') if p.name!='MainActivity.java'}; main_before=rd(main)
for n in ['NUOVO PROVINO DA QUESTA STAMPA','ⓘ  COME FUNZIONA','Le due esposizioni NON sono indipendenti','testFromPrint']:
    if n not in main_before: raise SystemExit('v0.11.0 baseline Timer mancante: '+n)
split=rd(java/'SplitGradePlan.java')
for n in ['public int softYellow = 60;','public int hardMagenta = 180;','softYellow + "Y / 0M','0Y / " + hardMagenta + "M']:
    if n not in split: raise SystemExit('v0.11.0 baseline Split Grade mancante: '+n)

# Version 0.11.0 / 56.
for p,o,n,label in [
 (build,'VERSION_NAME = "0.10.10"','VERSION_NAME = "0.11.0"','build name'),
 (build,'VERSION_CODE = "55"','VERSION_CODE = "56"','build code'),
 (build,'[Darkroom v0.10.10]','[Darkroom v0.11.0]','build tag'),
 (build,r'versionCode\s+55\b',r'versionCode\s+56\b','preflight code'),
 (build,r'0\.10\.10',r'0\.11\.0','preflight name'),
 (build,'versionCode 55 / versionName 0.10.10','versionCode 56 / versionName 0.11.0','preflight message'),
 (build,'Preflight v0.10.10 OK','Preflight v0.11.0 OK','preflight log'),
 (gradle,"versionCode 55\n        versionName '0.10.10'","versionCode 56\n        versionName '0.11.0'",'gradle'),
 (manifest,'android:versionCode="55"\n    android:versionName="0.10.10"','android:versionCode="56"\n    android:versionName="0.11.0"','manifest'),
 (main,'private static final String APP_VERSION = "0.10.10";','private static final String APP_VERSION = "0.11.0";','Timer UI')]: rep(p,o,n,label)

# R5/R6 data layer and complete screens.
for dst,src in [
 (java/'assistant/data/AssistantDataSchema.java','AssistantDataSchema.java'),
 (java/'assistant/data/AssistantDatabase.java','AssistantDatabase.java'),
 (java/'assistant/chemistry/inventory/MyChemistryActivity.java','MyChemistryActivity.java'),
 (java/'assistant/equipment/MyEquipmentActivity.java','MyEquipmentActivity.java'),
 (java/'assistant/equipment/TankPlanner.java','TankPlanner.java'),
 (java/'assistant/log/DevelopmentLogActivity.java','DevelopmentLogActivity.java')]: wr(dst,rd(here/src))

activity='''        <activity\n            android:name=".assistant.log.DevelopmentLogActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n'''
rep(manifest,activity,activity+'''\n        <activity\n            android:name=".assistant.chemistry.inventory.MyChemistryActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n\n        <activity\n            android:name=".assistant.equipment.MyEquipmentActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n''','manifest R5/R6')

rep(assistant,'import it.darkroom.timer.assistant.log.DevelopmentLogActivity;\n','import it.darkroom.timer.assistant.log.DevelopmentLogActivity;\nimport it.darkroom.timer.assistant.chemistry.inventory.MyChemistryActivity;\nimport it.darkroom.timer.assistant.equipment.MyEquipmentActivity;\n','Assistant imports')
rep(assistant,'        addPlaceholder(root, "LA MIA CHIMICA");\n','''        Button myChemistry = entry("LA MIA CHIMICA", "Inventario, residui, capacità e utilizzi", true);\n        myChemistry.setOnClickListener(v -> startActivity(new Intent(this, MyChemistryActivity.class)));\n        root.addView(myChemistry, margin(lp(-1, dp(78)), 0, 0, 0, 9));\n''','menu chimica')
rep(assistant,'        addPlaceholder(root, "LA MIA ATTREZZATURA");\n','''        Button myEquipment = entry("LA MIA ATTREZZATURA", "Tank personali e scelta intelligente", true);\n        myEquipment.setOnClickListener(v -> startActivity(new Intent(this, MyEquipmentActivity.class)));\n        root.addView(myEquipment, margin(lp(-1, dp(78)), 0, 0, 0, 9));\n''','menu attrezzatura')

# R6 tank selection, without blocking the historical manual-volume path.
rep(newdev,'    private EditText exposedIsoField, temperatureField, volumeField, rollsField;\n','''    private EditText exposedIsoField, temperatureField, volumeField, rollsField;\n    private TextView tankChoice;\n    private long selectedTankId=0;\n    private String selectedTankPlan="";\n''','tank fields')
rep(newdev,'        TextView eyebrow=text("DARKROOM ASSISTANT · 3/9",12,accent,true);','        TextView eyebrow=text("DARKROOM ASSISTANT · 6/9",12,accent,true);','badge 6/9')
old_note='''        TextView volumeNote=text("Inserimento manuale in Release 3 · la tank automatica arriverà in Release 6",11,muted,false);\n        volumeNote.setPadding(dp(4),dp(5),dp(4),dp(2)); root.addView(volumeNote);\n\n        label(root,"TEMPERATURA REALE");\n'''
new_note='''        TextView volumeNote=text("Volume manuale disponibile anche senza attrezzatura configurata",11,muted,false);\n        volumeNote.setPadding(dp(4),dp(5),dp(4),dp(2)); root.addView(volumeNote);\n\n        label(root,"TANK");\n        tankChoice=text("Nessuna tank selezionata · volume manuale",12,muted,true);\n        tankChoice.setPadding(dp(4),dp(4),dp(4),dp(6)); root.addView(tankChoice);\n        LinearLayout tankActions=new LinearLayout(this); tankActions.setOrientation(LinearLayout.HORIZONTAL);\n        Button chooseTank=smallChoice("SCEGLI TANK"); chooseTank.setOnClickListener(v->chooseTankManual());\n        Button bestTank=smallChoice("TANK MIGLIORE"); bestTank.setOnClickListener(v->chooseTankBest());\n        tankActions.addView(chooseTank,lp(0,dp(52),1)); tankActions.addView(bestTank,lp(0,dp(52),1)); root.addView(tankActions);\n\n        label(root,"TEMPERATURA REALE");\n'''
rep(newdev,old_note,new_note,'tank UI')
helper='''    private void chooseTankManual() {\n        it.darkroom.timer.assistant.data.AssistantDatabase db=new it.darkroom.timer.assistant.data.AssistantDatabase(this);\n        java.util.List<it.darkroom.timer.assistant.data.AssistantDatabase.TankItem> tanks=db.listTanks(); db.close();\n        if(tanks.isEmpty()){ toast("Nessuna tank personale configurata. Puoi continuare con il volume manuale."); return; }\n        String[] labels=new String[tanks.size()]; for(int i=0;i<tanks.size();i++) labels[i]=tanks.get(i).displayName();\n        new android.app.AlertDialog.Builder(this).setTitle("SCEGLI TANK").setItems(labels,(d,which)->{\n            it.darkroom.timer.assistant.data.AssistantDatabase.TankItem t=tanks.get(which); selectedTankId=t.id; selectedTankPlan="Scelta manuale · "+t.displayName(); tankChoice.setText(selectedTankPlan);\n        }).show();\n    }\n\n    private void chooseTankBest() {\n        int rolls=parseInt(rollsField.getText().toString(),-1); double volume=parseDouble(volumeField.getText().toString());\n        if(rolls<=0||Double.isNaN(volume)||volume<=0){ toast("Inserisci prima numero rulli e volume."); return; }\n        it.darkroom.timer.assistant.data.AssistantDatabase db=new it.darkroom.timer.assistant.data.AssistantDatabase(this);\n        java.util.List<it.darkroom.timer.assistant.data.AssistantDatabase.TankItem> tanks=db.listTanks();\n        it.darkroom.timer.assistant.data.AssistantDatabase.ChemicalItem inv=db.findChemicalForDeveloper(developerField.getText().toString());\n        it.darkroom.timer.assistant.equipment.TankPlanner.Plan p=it.darkroom.timer.assistant.equipment.TankPlanner.chooseBest(tanks,selectedFormat,rolls,volume,developerField.getText().toString(),dilutionField.getText().toString(),inv); db.close();\n        if(!p.ok){ selectedTankId=0; selectedTankPlan=p.problem; tankChoice.setText(p.problem); new android.app.AlertDialog.Builder(this).setTitle("TANK MIGLIORE").setMessage(p.problem).setPositiveButton("OK",null).show(); return; }\n        selectedTankId=p.tank.id; selectedTankPlan=p.summary(); tankChoice.setText(p.tank.displayName()+" · "+p.cycles+(p.cycles==1?" ciclo":" cicli"));\n        new android.app.AlertDialog.Builder(this).setTitle("TANK MIGLIORE").setMessage(p.summary()).setPositiveButton("USA QUESTA",null).show();\n    }\n\n'''
rep(newdev,'    private void calculate() {\n',helper+'    private void calculate() {\n','tank logic')
rep(newdev,'        i.putExtra("alternatives",r.alternatives); i.putExtra("rolls",rolls); i.putExtra("volumeMl",volume);\n','''        i.putExtra("alternatives",r.alternatives); i.putExtra("rolls",rolls); i.putExtra("volumeMl",volume);\n        i.putExtra("selectedTankId",selectedTankId); i.putExtra("tankPlanSummary",selectedTankPlan);\n''','tank extras')

# R4 immediate refresh of personal/preferred recipe state.
new_choose='''    private void chooseActiveTime(){AssistantDatabase.SourceSnapshot s=snapshot();preferred=db.findPreferred(s.comboKey());latestPersonal=db.findLatest(s.comboKey());int repeat=e.getInt("repeatTimeSeconds",0);if(repeat>0){activeSeconds=repeat;activeOrigin=e.getString("repeatOrigin","RICETTA DAL LOG");return;}if(preferred!=null&&AssistantDatabase.sameTemperature(preferred.personalTemp,s.originalTemp)){activeSeconds=preferred.personalSeconds;activeOrigin="RICETTA PREFERITA";}else if(latestPersonal!=null&&AssistantDatabase.sameTemperature(latestPersonal.personalTemp,s.originalTemp)){activeSeconds=latestPersonal.personalSeconds;activeOrigin="MIA RICETTA";}else{activeSeconds=s.originalSeconds;activeOrigin=s.dataType.contains("ADATTATO")?"ADATTATO / CALCOLATO":"FONTE";}}'''
replace_between(result,'    private void chooseActiveTime(){','\n\n    private void buildUi()',new_choose,'chooseActiveTime R4 fix')
rep(result,'db.saveRecipe(snapshot(),sec,tc,note.getText().toString(),fav.isChecked());toast("Ricetta personale salvata");chooseActiveTime();','db.saveRecipe(snapshot(),sec,tc,note.getText().toString(),fav.isChecked());toast("Ricetta personale salvata");e.putInt("repeatTimeSeconds",0);chooseActiveTime();buildUi();','immediate recipe refresh')

# R4 semantic UNKNOWN + R5 explicit usage confirmation.
old_save='l.productMl=c.dilutionKnown?c.productMl:0;l.waterMl=c.dilutionKnown?c.waterMl:0;l.rolls=e.getInt("rolls",1);l.capacityState=c.capacityState;l.capacityMessage=c.capacityMessage;l.rating=rating.getSelectedItemPosition()+1;l.notes=notes.getText().toString();db.saveLog(l);toast("Sviluppo salvato nel Log");'
new_save='l.productMl=c.dilutionKnown?c.productMl:0;l.waterMl=c.dilutionKnown?c.waterMl:0;l.productKnown=c.dilutionKnown;l.waterKnown=c.dilutionKnown;l.rolls=e.getInt("rolls",1);l.capacityState=c.capacityState;l.capacityMessage=c.capacityMessage;l.rating=rating.getSelectedItemPosition()+1;l.notes=notes.getText().toString();long logId=db.saveLog(l);toast("Sviluppo salvato nel Log");maybeRegisterChemicalUsage(logId,l,c);'
rep(result,old_save,new_save,'UNKNOWN flags + usage proposal')
usage='''    private void maybeRegisterChemicalUsage(long logId, AssistantDatabase.LogEntry l, ChemistryCalculator.Result c){\n        AssistantDatabase.ChemicalItem item=db.findChemicalForDeveloper(l.source.developer); if(item==null)return;\n        boolean ml="ml".equalsIgnoreCase(item.unit); boolean liters="litri".equalsIgnoreCase(item.unit)||"l".equalsIgnoreCase(item.unit);\n        if(c.dilutionKnown&&(ml||liters)){\n            final double used=liters?c.productMl/1000.0:c.productMl; final double after=Math.max(0,item.remainingAmount-used);\n            String msg="Prodotto: "+item.name+"\\nQuantità utilizzata: "+fmtAmount(used)+" "+item.unit+"\\nResidua prima: "+fmtAmount(item.remainingAmount)+" "+item.unit+"\\nResidua dopo: "+fmtAmount(after)+" "+item.unit+"\\n\\nLa sottrazione avverrà solo confermando.";\n            new AlertDialog.Builder(this).setTitle("REGISTRA UTILIZZO CHIMICA").setMessage(msg).setPositiveButton("CONFERMA",(d,w)->{db.registerChemicalUsage(item.id,logId,used,item.unit,l,"");toast("Utilizzo chimica registrato");}).setNegativeButton("NON REGISTRARE",null).show();\n        }else{\n            LinearLayout box=formBox(); EditText q=field("Quantità realmente utilizzata · "+item.unit); q.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL); box.addView(q);\n            String reason=c.dilutionKnown?"L'unità dell'inventario non è convertibile automaticamente.":"Quantità prodotto non determinata: la diluizione non è documentata.";\n            new AlertDialog.Builder(this).setTitle("REGISTRA UTILIZZO CHIMICA").setMessage(reason+" Inserisci la quantità realmente usata oppure annulla: nulla verrà sottratto automaticamente.").setView(box).setPositiveButton("REGISTRA",(d,w)->{double used=parseDouble(q.getText().toString());if(Double.isNaN(used)||used<0){toast("Quantità non valida");return;}db.registerChemicalUsage(item.id,logId,used,item.unit,l,"Quantità inserita manualmente");toast("Utilizzo chimica registrato");}).setNegativeButton("NON REGISTRARE",null).show();\n        }\n    }\n    private static String fmtAmount(double v){return Math.abs(v-Math.rint(v))<0.05?String.format(Locale.ITALY,"%.0f",v):String.format(Locale.ITALY,"%.2f",v);}\n\n'''
rep(result,'    private void renderPrepare(LinearLayout box,double volume){',usage+'    private void renderPrepare(LinearLayout box,double volume){','usage dialog')
prepare_anchor='        LinearLayout prepare=new LinearLayout(this);prepare.setOrientation(LinearLayout.VERTICAL);prepare.setPadding(dp(14),dp(12),dp(14),dp(12));prepare.setBackground(roundRect(card,10,1,accent));root.addView(prepare);renderPrepare(prepare,e.getDouble("volumeMl",0));\n'
rep(result,prepare_anchor,prepare_anchor+'''        String tankPlan=e.getString("tankPlanSummary",""); if(tankPlan!=null&&!tankPlan.trim().isEmpty()){LinearLayout tankBox=new LinearLayout(this);tankBox.setOrientation(LinearLayout.VERTICAL);tankBox.setPadding(dp(14),dp(12),dp(14),dp(12));tankBox.setBackground(roundRect(card,10,1,border));tankBox.addView(text("TANK / PIANO CICLI",12,accent,true));tankBox.addView(text(tankPlan,12,primary,false));root.addView(tankBox,margin(-1,-2,0,8,0,0));}\n''','tank result summary')

# Absolute Timer guard after all Assistant work.
timer_after={p.name:sha(p) for p in java.glob('*.java') if p.name!='MainActivity.java'}
if timer_before!=timer_after:
    bad=[n for n in sorted(set(timer_before)|set(timer_after)) if timer_before.get(n)!=timer_after.get(n)]
    raise SystemExit('v0.11.0 GUARDRAIL TIMER: '+', '.join(bad))
if rd(main)!=main_before.replace('private static final String APP_VERSION = "0.10.10";','private static final String APP_VERSION = "0.11.0";',1): raise SystemExit('v0.11.0 MainActivity modificato oltre versione')

checks={
 build:['VERSION_NAME = "0.11.0"','VERSION_CODE = "56"'],
 gradle:["versionCode 56","versionName '0.11.0'"],
 manifest:['android:versionCode="56"','android:versionName="0.11.0"','.assistant.chemistry.inventory.MyChemistryActivity','.assistant.equipment.MyEquipmentActivity'],
 main:['NUOVO PROVINO DA QUESTA STAMPA','ⓘ  COME FUNZIONA','testFromPrint'],
 java/'SplitGradePlan.java':['public int softYellow = 60;','public int hardMagenta = 180;'],
 java/'assistant/data/AssistantDataSchema.java':['VERSION = 2','chemical_inventory','chemical_usage','personal_equipment','personal_tanks','product_known','water_known'],
 java/'assistant/data/AssistantDatabase.java':['ALTER TABLE development_logs ADD COLUMN product_known','registerChemicalUsage','listTanks','findChemicalForDeveloper'],
 java/'assistant/chemistry/inventory/MyChemistryActivity.java':['AGGIUNGI ALLA MIA CHIMICA','PRODOTTO PERSONALE / DATI INSERITI DALL\'UTENTE','DILUIZIONE PERSONALE','CAPACITÀ NON DOCUMENTATA','STORICO UTILIZZI CHIMICA'],
 java/'assistant/equipment/MyEquipmentActivity.java':['JOBO 2520','minRotationMl=270','capacity35=2','capacity120=2','DATI INSERITI DALL\'UTENTE'],
 java/'assistant/equipment/TankPlanner.java':['CPE2_MAX_ML','chooseBest','cycles','chimica insufficiente','minor volume valido'],
 newdev:['DARKROOM ASSISTANT · 6/9','SCEGLI TANK','TANK MIGLIORE','chooseTankBest','selectedTankId','tankPlanSummary'],
 result:['MIA RICETTA','e.putInt("repeatTimeSeconds",0);chooseActiveTime();buildUi();','productKnown=c.dilutionKnown','REGISTRA UTILIZZO CHIMICA','nulla verrà sottratto automaticamente','TANK / PIANO CICLI'],
 log:['Quantità prodotto: non determinata','Quantità acqua: non determinata','RIPETI','CONFRONTA SVILUPPI']}
for p,needles in checks.items():
    t=rd(p)
    for n in needles:
        if n not in t: raise SystemExit(f'v0.11.0 check fallito {n} in {p}')
for p in [java/'assistant/data/AssistantDataSchema.java',java/'assistant/data/AssistantDatabase.java']:
    if 'DROP TABLE' in rd(p): raise SystemExit('v0.11.0 DROP TABLE vietato')
cat=rd(java/'assistant/development/DevelopmentCatalog.java'); chem=rd(java/'assistant/chemistry/ChemistryCalculator.java')
for n in ['JOBO CPE2','rotazione continua','DATO DIRETTO','DATO ADATTATO / CALCOLATO','tempAdjusted * 0.85']:
    if n not in cat: raise SystemExit('v0.11.0 regressione R2: '+n)
for n in ['CPE2_MAX_ML = 600.0','4000 ml working solution → 12 perforated or roll films','CAPACITY_UNKNOWN','Rapporto di diluizione non ancora disponibile dalla fonte']:
    if n not in chem: raise SystemExit('v0.11.0 regressione R3: '+n)
print('v0.11.0 DARKROOM ASSISTANT R5+R6 — VERIFICHE SORGENTE OK',flush=True)
