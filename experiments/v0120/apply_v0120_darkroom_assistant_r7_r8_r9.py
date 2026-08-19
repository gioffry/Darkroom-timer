#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys

work=Path(sys.argv[1]); project=work/'project'; java=project/'app/src/main/java/it/darkroom/timer'
main=java/'MainActivity.java'; split=java/'SplitGradePlan.java'; logentry=java/'LogEntry.java'; logstore=java/'LogStore.java'
build=work/'build_darkroom.py'; gradle=project/'app/build.gradle'; manifest=project/'app/src/main/AndroidManifest.xml'
assistant=java/'assistant/AssistantActivity.java'; newdev=java/'assistant/development/NewDevelopmentActivity.java'; result=java/'assistant/development/DevelopmentResultActivity.java'; database=java/'assistant/data/AssistantDatabase.java'; schema=java/'assistant/data/AssistantDataSchema.java'; here=Path(__file__).parent

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(s,encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rep(p,o,n,label,c=1):
    s=rd(p);k=s.count(o)
    if k<c:raise SystemExit(f'v0.12.0 {label}: atteso >= {c}, trovato {k}')
    wr(p,s.replace(o,n,c));print('v0.12.0 OK',label,flush=True)
def rrep(p,pattern,replacement,label,c=1,flags=re.S):
    s=rd(p);out,n=re.subn(pattern,replacement,s,count=c,flags=flags)
    if n!=c:raise SystemExit(f'v0.12.0 {label}: regex trovata {n}, attesa {c}')
    wr(p,out);print('v0.12.0 OK',label,flush=True)

def must(p,*needles):
    t=rd(p)
    for n in needles:
        if n not in t:raise SystemExit(f'v0.12.0 baseline mancante {n} in {p}')

# -----------------------------------------------------------------------------
# PROTECT THE REAL v0.11.0 MATERIALIZED BASE.
# -----------------------------------------------------------------------------
must(main,'private static final String APP_VERSION = "0.11.0";','NUOVO PROVINO DA QUESTA STAMPA','testFromPrint','showPrintCorrectionEditor','maybeShowTestResultChooser')
must(split,'public int softYellow = 60;','public int hardMagenta = 180;','softYellow + "Y / 0M','0Y / " + hardMagenta + "M')
must(schema,'public static final int VERSION = 2;')
if 'package="it.darkroom.timer"' not in rd(manifest):raise SystemExit('v0.12.0 package base alterato')
protected_before={p.relative_to(java).as_posix():sha(p) for p in java.rglob('*.java') if not p.relative_to(java).as_posix().startswith('assistant/') and p.name not in {'MainActivity.java','SplitGradePlan.java','LogEntry.java','LogStore.java'}}

# -----------------------------------------------------------------------------
# VERSION 0.12.0 / 57. Package remains it.darkroom.timer.
# -----------------------------------------------------------------------------
for p,o,n,label in [
 (build,'VERSION_NAME = "0.11.0"','VERSION_NAME = "0.12.0"','build name'),
 (build,'VERSION_CODE = "56"','VERSION_CODE = "57"','build code'),
 (build,'[Darkroom v0.11.0]','[Darkroom v0.12.0]','build tag'),
 (build,r'versionCode\s+56\b',r'versionCode\s+57\b','preflight code'),
 (build,r'0\.11\.0',r'0\.12\.0','preflight name'),
 (build,'versionCode 56 / versionName 0.11.0','versionCode 57 / versionName 0.12.0','preflight message'),
 (build,'Preflight v0.11.0 OK','Preflight v0.12.0 OK','preflight log'),
 (gradle,"versionCode 56\n        versionName '0.11.0'","versionCode 57\n        versionName '0.12.0'",'gradle'),
 (manifest,'android:versionCode="56"\n    android:versionName="0.11.0"','android:versionCode="57"\n    android:versionName="0.12.0"','manifest'),
 (main,'private static final String APP_VERSION = "0.11.0";','private static final String APP_VERSION = "0.12.0";','Timer UI')]:rep(p,o,n,label)

# -----------------------------------------------------------------------------
# TIMER: completely REMOVE STAMPA -> PROVINO, restore standard PROVINO behavior.
# -----------------------------------------------------------------------------
for needle,label in [
 ('    private TextView testMigrationSummary;\n','campo testMigrationSummary'),
 ('    private boolean testFromPrint = false;\n','flag testFromPrint'),
 ('        testFromPrint = p.getBoolean("testFromPrint", false);\n','load testFromPrint')]:rep(main,needle,'',label)

old_listener='''        testModeButton.setOnClickListener(v -> {\n            testFromPrint = false;\n            getSharedPreferences("ui", MODE_PRIVATE).edit().putBoolean("testFromPrint", false).apply();\n            setMode(MODE_TEST);\n            updateTimingUi();\n        });'''
rep(main,old_listener,'        testModeButton.setOnClickListener(v -> setMode(MODE_TEST));','tab PROVINO standard')

back_button='''\n        Button backToTest = compactButton("NUOVO PROVINO DA QUESTA STAMPA");\n        backToTest.setTextColor(BLUE);\n        backToTest.setOnClickListener(v -> returnPrintToTest());\n        box.addView(backToTest, margin(lp(-1, dp(50)), 0, 10, 0, 0));'''
rep(main,back_button,'','rimozione pulsante STAMPA -> PROVINO')

migration_ui='''\n        testMigrationSummary = text("", 12, BLUE, true);\n        testMigrationSummary.setGravity(Gravity.CENTER);\n        testMigrationSummary.setPadding(dp(8), dp(10), dp(8), dp(4));\n        testMigrationSummary.setVisibility(View.GONE);\n        outer.addView(testMigrationSummary, lp(-1, -2));'''
rep(main,migration_ui,'','rimozione banner provino derivato')

rrep(main,r'    private void returnPrintToTest\(\) \{.*?(?=    private void setMode\(int newMode\) \{)','', 'rimozione metodi migrazione stampa-provino')
# All remaining banner sync calls belonged exclusively to the removed migration.
s=rd(main); count=s.count('        updateTestMigrationUi();\n'); s=s.replace('        updateTestMigrationUi();\n','');wr(main,s);print('v0.12.0 OK rimossi sync migrazione',count,flush=True)

rrep(main,r'    private int\[\] currentTestStripTargets\(\) \{.*?\n    \}', '    private int[] currentTestStripTargets() {\n        return TimingMath.cumulativeSeries(timingMethod, testWidthMs, testCount);\n    }', 'progressione PROVINO standard')
rrep(main,r'    private String cumulativeTimes\(\) \{.*?\n    \}', '    private String cumulativeTimes() {\n        return "TEMPI CUMULATIVI  " + TimingMath.seriesLabel(currentTestStripTargets());\n    }', 'label PROVINO standard')
rrep(main,r'    private String testPromptDescription\(\) \{.*?\n    \}', '    private String testPromptDescription() {\n        return TimingMath.isFStop(timingMethod) ? "Tempo prima striscia" : "Incremento del provino";\n    }', 'prompt PROVINO standard')
rrep(main,r'    private String testStepDescription\(\) \{.*?\n    \}', '    private String testStepDescription() {\n        return TimingMath.isFStop(timingMethod) ? "Progressione cumulativa • passo ¼ stop" : "Ogni esposizione ha lo stesso tempo";\n    }', 'passo PROVINO standard')
rep(main,'TimingMath.quarterStop(testWidthMs, direction, 500, testFromPrint ? 36_000_000 : 30_000)','TimingMath.quarterStop(testWidthMs, direction, 500, 30_000)','clamp f-stop PROVINO standard')
rep(main,'snap(ms, 500, testFromPrint ? 36_000_000 : 30_000)','snap(ms, 500, 30_000)','clamp secondi PROVINO standard')

# Split Grade visual defaults/manual editing stay unchanged. Only natural dynamic TTS changes.
rep(split,'public String softPrompt() { return "Imposta " + softYellow + "Y / 0M. Poi premi il pulsante."; }','public String softPrompt() { return "Azzera il magenta e imposta giallo " + softYellow + ". Poi premi il pulsante."; }','TTS morbido naturale dinamico')
rep(split,'public String hardPrompt() { return "Imposta 0Y / " + hardMagenta + "M. Poi premi il pulsante."; }','public String hardPrompt() { return "Azzera il giallo e imposta magenta " + hardMagenta + ". Poi premi il pulsante."; }','TTS duro naturale dinamico')

# Non-invasive paper chemistry consultation inside STAMPA. Never gates exposure.
print_anchor='''        updatePrintSequenceUi();\n        return box;'''
paper_print='''        Button chemistrySession = compactButton("CHIMICA SESSIONE · " + it.darkroom.timer.assistant.paper.PaperChemistryStore.shortStatus(this));\n        chemistrySession.setOnClickListener(v -> showAppConfirmDialog(\n                "CHIMICA SESSIONE",\n                it.darkroom.timer.assistant.paper.PaperChemistryStore.summary(this),\n                "CONFIGURA", () -> startActivity(new Intent(this, it.darkroom.timer.assistant.paper.PaperChemistryActivity.class)), "CHIUDI"));\n        box.addView(chemistrySession, margin(lp(-1, dp(48)), 0, 8, 0, 0));\n        updatePrintSequenceUi();\n        return box;'''
rep(main,print_anchor,paper_print,'CHIMICA SESSIONE in STAMPA')

# Snapshot paper chemistry is appended to print Log; old rows remain readable.
rep(logentry,'    public String recipeState = "";\n','    public String recipeState = "";\n    /** Immutable snapshot of the optional active paper-chemistry session. */\n    public String paperChemistrySnapshot = "";\n','Log snapshot chimica carta')
rep(logstore,'                    e.recipeState = f.length >= 24 ? dec(f[23]) : "";','                    e.recipeState = f.length >= 24 ? dec(f[23]) : "";\n                    e.paperChemistrySnapshot = f.length >= 25 ? dec(f[24]) : "";','parse snapshot chimica carta')
rep(logstore,'                    .append(enc(e.recipeState));','                    .append(enc(e.recipeState)).append(\'\\t\')\n                    .append(enc(e.paperChemistrySnapshot));','write snapshot chimica carta')
rep(main,'            e.recipeState = p.getString("lastRecipeState", "");','            e.recipeState = p.getString("lastRecipeState", "");\n            e.paperChemistrySnapshot = it.darkroom.timer.assistant.paper.PaperChemistryStore.activeSnapshot(this);','capture snapshot chimica carta')

# -----------------------------------------------------------------------------
# R7/R8/R9 source files and additive SQLite v2 -> v3 migration.
# -----------------------------------------------------------------------------
for dst,src in [
 (java/'assistant/operational/OperationalAssistantActivity.java','OperationalAssistantActivity.java'),
 (java/'assistant/paper/PaperChemistryStore.java','PaperChemistryStore.java'),
 (java/'assistant/paper/PaperChemistryActivity.java','PaperChemistryActivity.java'),
 (java/'assistant/system/BackupEngine.java','BackupEngine.java'),
 (java/'assistant/system/CatalogManager.java','CatalogManager.java'),
 (java/'assistant/system/DataManagementActivity.java','DataManagementActivity.java'),
 (java/'assistant/system/DataProvenance.java','DataProvenance.java'),
 (schema,'AssistantDataSchema.java')]:wr(dst,rd(here/src))

create_r789='''    private static void createR7R8R9(SQLiteDatabase db){\n        db.execSQL(AssistantDataSchema.CREATE_ASSISTANT_SESSIONS);\n        db.execSQL(AssistantDataSchema.CREATE_PAPER_SESSIONS);\n        db.execSQL(AssistantDataSchema.CREATE_TECHNICAL_SOURCE_CACHE);\n        db.execSQL(AssistantDataSchema.CREATE_SESSION_INDEX);\n        db.execSQL(AssistantDataSchema.CREATE_PAPER_SESSION_INDEX);\n        db.execSQL(AssistantDataSchema.CREATE_SOURCE_CACHE_INDEX);\n    }\n'''
rep(database,'        createR5R6(db); db.execSQL(AssistantDataSchema.CREATE_FAVORITE_INDEX);','        createR5R6(db); createR7R8R9(db); db.execSQL(AssistantDataSchema.CREATE_FAVORITE_INDEX);','onCreate schema v3')
rep(database,'    @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){',create_r789+'    @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){','helper create R7/R8/R9')
old_upgrade='''            createR5R6(db);\n        }\n    }'''
new_upgrade='''            createR5R6(db);\n        }\n        if(oldVersion<3){\n            createR7R8R9(db);\n        }\n    }'''
rep(database,old_upgrade,new_upgrade,'migrazione SQLite v2 -> v3')

# Activities: no new launcher and no mandatory navigation before STAMPA.
manifest_anchor='''        <activity\n            android:name=".assistant.equipment.MyEquipmentActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />'''
manifest_new=manifest_anchor+'''\n\n        <activity\n            android:name=".assistant.operational.OperationalAssistantActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n\n        <activity\n            android:name=".assistant.paper.PaperChemistryActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n\n        <activity\n            android:name=".assistant.system.DataManagementActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />'''
rep(manifest,manifest_anchor,manifest_new,'manifest R7/R8/R9')

# Assistant menu completes 9/9.
menu='''        Button paperChemistry = entry("CHIMICA CARTA", "Sessione opzionale, preparazione e inventario", true);\n        paperChemistry.setOnClickListener(v -> startActivity(new Intent(this, it.darkroom.timer.assistant.paper.PaperChemistryActivity.class)));\n        root.addView(paperChemistry, margin(lp(-1, dp(78)), 0, 0, 0, 9));\n\n        Button dataSystem = entry("FONTI · OFFLINE · BACKUP", "Catalogo dati, provenienza, aggiornamenti e ripristino", true);\n        dataSystem.setOnClickListener(v -> startActivity(new Intent(this, it.darkroom.timer.assistant.system.DataManagementActivity.class)));\n        root.addView(dataSystem, margin(lp(-1, dp(78)), 0, 0, 0, 9));\n\n        TextView completeBadge = text("DARKROOM ASSISTANT 9/9 COMPLETATO", 12, accent, true);\n        completeBadge.setGravity(Gravity.CENTER);\n        completeBadge.setPadding(dp(4), dp(8), dp(4), dp(10));\n        root.addView(completeBadge, lp(-1, -2));\n\n'''
rep(assistant,'        Button back = new Button(this);',menu+'        Button back = new Button(this);','menu Assistant 9/9')
rep(newdev,'TextView eyebrow=text("DARKROOM ASSISTANT · 6/9",12,accent,true);','TextView eyebrow=text("DARKROOM ASSISTANT · 9/9",12,accent,true);','badge Nuovo sviluppo 9/9')

# Result -> real operational runner. It receives a snapshot of the already selected plan.
rep(result,'import android.app.AlertDialog;\n','import android.app.AlertDialog;\nimport android.content.Intent;\n','Intent Assistente operativo')
launch='''        Button startOperational=button("AVVIA SVILUPPO");\n        startOperational.setOnClickListener(v->{Intent i=new Intent(this,it.darkroom.timer.assistant.operational.OperationalAssistantActivity.class);i.putExtras(e);i.putExtra("plannedSeconds",activeSeconds);i.putExtra("timeOrigin",activeOrigin);startActivity(i);});\n        root.addView(startOperational,margin(-1,dp(58),0,dp(12),0,0));\n        Button saveRecipe=button("SALVA COME MIA RICETTA");'''
rep(result,'        Button saveRecipe=button("SALVA COME MIA RICETTA");',launch,'AVVIA SVILUPPO R7')
rep(result,'source.addView(text("Tipo dato: "+e.getString("dataType",""),12,accent,true));','source.addView(text("Tipo dato: "+e.getString("dataType",""),12,accent,true));source.addView(text(it.darkroom.timer.assistant.system.DataProvenance.detail(e.getString("dataType",""),e.getString("source",""),e.getString("sourceData",""),e.getString("calculation","")),11,muted,false));','provenienza R9 nel risultato')

# -----------------------------------------------------------------------------
# ACCEPTANCE / REGRESSION GUARDS.
# -----------------------------------------------------------------------------
protected_after={p.relative_to(java).as_posix():sha(p) for p in java.rglob('*.java') if not p.relative_to(java).as_posix().startswith('assistant/') and p.name not in {'MainActivity.java','SplitGradePlan.java','LogEntry.java','LogStore.java'}}
if protected_before!=protected_after:
    bad=[n for n in sorted(set(protected_before)|set(protected_after)) if protected_before.get(n)!=protected_after.get(n)]
    raise SystemExit('v0.12.0 GUARDRAIL Timer non autorizzato: '+', '.join(bad))

mt=rd(main);sp=rd(split);mf=rd(manifest);dbt=rd(database);sct=rd(schema)
for forbidden in ['testFromPrint','NUOVO PROVINO DA QUESTA STAMPA','returnPrintToTest','testMigrationSummary','PROVINO DA SPLIT GRADE','TEMPI DAL PUNTO DI STAMPA']:
    if forbidden in mt:raise SystemExit('v0.12.0 STAMPA->PROVINO non rimosso: '+forbidden)
for n in ['maybeShowTestResultChooser','setMode(MODE_PRINT);','showPrintCorrectionEditor','DODGE','BURN','currentTestStripTargets','TimingMath.cumulativeSeries']:
    if n not in mt:raise SystemExit('v0.12.0 regressione PROVINO/STAMPA: '+n)
for n in ['public int softYellow = 60;','public int hardMagenta = 180;','softYellow + "Y / 0M','0Y / " + hardMagenta + "M','"Azzera il magenta e imposta giallo " + softYellow','"Azzera il giallo e imposta magenta " + hardMagenta']:
    if n not in sp:raise SystemExit('v0.12.0 Split Grade fallito: '+n)
if 'Azzera il magenta e imposta giallo 60' in sp or 'Azzera il giallo e imposta magenta 180' in sp:raise SystemExit('v0.12.0 TTS Split Grade hardcoded')
if mf.count('android.intent.action.MAIN')!=1 or mf.count('android.intent.category.LAUNCHER')!=1:raise SystemExit('v0.12.0 launcher non univoco')
if 'package="it.darkroom.timer"' not in mf:raise SystemExit('v0.12.0 package modificato')
if 'DROP TABLE' in dbt or 'DROP TABLE' in sct:raise SystemExit('v0.12.0 migrazione distruttiva vietata')
for n in ['VERSION = 3','assistant_sessions','paper_chemistry_sessions','technical_source_cache']:
    if n not in sct:raise SystemExit('v0.12.0 schema v3 mancante: '+n)
for n in ['createR7R8R9','if(oldVersion<3)']:
    if n not in dbt:raise SystemExit('v0.12.0 migration v3 mancante: '+n)
for path,needles in {
 java/'assistant/operational/OperationalAssistantActivity.java':['CONTROLLO PRE-SVILUPPO','BLOCCANTE','TEMPO NON DOCUMENTATO','CICLO ','CountDownTimer','SALVA SVILUPPO NEL LOG','REGISTRA UTILIZZO CHIMICA'],
 java/'assistant/paper/PaperChemistryActivity.java':['SESSIONE DI STAMPA','CALCOLA PREPARAZIONE','DATI DOCUMENTATI','DATI PERSONALI','Nessun tempo di esposizione STAMPA'],
 java/'assistant/system/DataManagementActivity.java':['CONTROLLA AGGIORNAMENTI DATI','BACKUP DATI','RIPRISTINA BACKUP','UNISCI','SOSTITUISCI DATI PERSONALI','MODALITÀ OFFLINE'],
 java/'assistant/system/BackupEngine.java':['FORMAT_VERSION=1','CATALOG_VERSION=1','beginTransaction','CONFLICT_IGNORE','payloadSha256'],
 java/'assistant/system/DataProvenance.java':['FONTE UFFICIALE','FONTE SECONDARIA','DATO INTERNO VERIFICATO','CALCOLO','ADATTAMENTO','DATO PERSONALE','NON DOCUMENTATO']}.items():
    t=rd(path)
    for n in needles:
        if n not in t:raise SystemExit(f'v0.12.0 verifica {n} in {path}')
if 'SonoffArmService' in rd(java/'assistant/operational/OperationalAssistantActivity.java'):raise SystemExit('v0.12.0 timer sviluppo collegato a SONOFF')
for n in ['VERSION_NAME = "0.12.0"','VERSION_CODE = "57"']:
    if n not in rd(build):raise SystemExit('v0.12.0 build metadata fallita '+n)
for n in ["versionCode 57","versionName '0.12.0'"]:
    if n not in rd(gradle):raise SystemExit('v0.12.0 Gradle metadata fallita '+n)
for n in ['android:versionCode="57"','android:versionName="0.12.0"']:
    if n not in mf:raise SystemExit('v0.12.0 manifest metadata fallita '+n)
print('v0.12.0 DARKROOM ASSISTANT 9/9 + TIMER — VERIFICHE SORGENTE OK',flush=True)
