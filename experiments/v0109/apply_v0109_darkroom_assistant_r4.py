#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

work=Path(sys.argv[1]); project=work/'project'; java=project/'app/src/main/java/it/darkroom/timer'
main=java/'MainActivity.java'; build=work/'build_darkroom.py'; gradle=project/'app/build.gradle'; manifest=project/'app/src/main/AndroidManifest.xml'
home=java/'home/HomeActivity.java'; assistant=java/'assistant/AssistantActivity.java'; dev=java/'assistant/development'; catalog=dev/'DevelopmentCatalog.java'; newdev=dev/'NewDevelopmentActivity.java'; result=dev/'DevelopmentResultActivity.java'; chem=java/'assistant/chemistry/ChemistryCalculator.java'; prepare=java/'assistant/chemistry/PrepareChemistryActivity.java'; here=Path(__file__).parent

def rd(p): return Path(p).read_text(encoding='utf-8')
def wr(p,s): Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(s,encoding='utf-8')
def rep(p,o,n,label,c=1):
    s=rd(p); k=s.count(o)
    if k<c: raise SystemExit(f'v0.10.9 {label}: atteso >= {c}, trovato {k}')
    wr(p,s.replace(o,n,c)); print('v0.10.9 OK',label,flush=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

timer_before={p.name:sha(p) for p in java.glob('*.java') if p.name!='MainActivity.java'}; main_before=rd(main); home_before=sha(home); cat_before=sha(catalog); chem_before=sha(chem); prepare_before=sha(prepare)

# version 0.10.9 / 54
rep(build,'VERSION_NAME = "0.10.8"','VERSION_NAME = "0.10.9"','version name build')
rep(build,'VERSION_CODE = "53"','VERSION_CODE = "54"','version code build')
rep(build,'[Darkroom v0.10.8]','[Darkroom v0.10.9]','build log tag')
rep(build,r'versionCode\s+53\b',r'versionCode\s+54\b','preflight code regex')
rep(build,r'0\.10\.8',r'0\.10\.9','preflight name regex')
rep(build,'versionCode 53 / versionName 0.10.8','versionCode 54 / versionName 0.10.9','preflight message')
rep(build,'Preflight v0.10.8 OK','Preflight v0.10.9 OK','preflight log')
rep(gradle,"versionCode 53\n        versionName '0.10.8'","versionCode 54\n        versionName '0.10.9'",'gradle version')
rep(manifest,'android:versionCode="53"\n    android:versionName="0.10.8"','android:versionCode="54"\n    android:versionName="0.10.9"','manifest version')
rep(main,'private static final String APP_VERSION = "0.10.8";','private static final String APP_VERSION = "0.10.9";','Timer UI version')

# Replace oversized R3 HOME button with standard Android-style top app bar back arrow.
old_nav='''        Button homeButton = compactButton("← HOME");\n        homeButton.setTextSize(13);\n        homeButton.setGravity(Gravity.CENTER);\n        homeButton.setOnClickListener(v -> finish());\n        root.addView(homeButton, margin(lp(dp(94), dp(38)), 0, 0, 0, 4));\n\n        TextView title = text("Darkroom Timer", 27, TEXT_PRIMARY, true);\n        title.setGravity(Gravity.CENTER);\n        root.addView(title, lp(-1, dp(48)));\n'''
new_nav='''        LinearLayout topBar = new LinearLayout(this);\n        topBar.setOrientation(LinearLayout.HORIZONTAL);\n        topBar.setGravity(Gravity.CENTER_VERTICAL);\n        Button homeButton = new Button(this);\n        homeButton.setText("←");\n        homeButton.setAllCaps(false);\n        homeButton.setTextSize(25);\n        homeButton.setTextColor(TEXT_PRIMARY);\n        homeButton.setPadding(0, 0, 0, 0);\n        homeButton.setMinWidth(0);\n        homeButton.setMinimumWidth(0);\n        homeButton.setMinHeight(0);\n        homeButton.setMinimumHeight(0);\n        homeButton.setBackgroundColor(Color.TRANSPARENT);\n        homeButton.setContentDescription("Torna alla Home");\n        homeButton.setOnClickListener(v -> finish());\n        topBar.addView(homeButton, lp(dp(48), dp(48)));\n        TextView title = text("Darkroom Timer", 27, TEXT_PRIMARY, true);\n        title.setGravity(Gravity.CENTER);\n        topBar.addView(title, lp(0, dp(48), 1f));\n        View navSpacer = new View(this);\n        topBar.addView(navSpacer, lp(dp(48), dp(48)));\n        root.addView(topBar, lp(-1, dp(48)));\n'''
rep(main,old_nav,new_nav,'navigazione standard freccia HOME')
expected=main_before.replace('private static final String APP_VERSION = "0.10.8";','private static final String APP_VERSION = "0.10.9";',1).replace(old_nav,new_nav,1)
if rd(main)!=expected: raise SystemExit('v0.10.9 GUARDRAIL MainActivity: modifiche non autorizzate')

# New Assistant activities and versioned local data layer.
anchor='''        <activity\n            android:name=".assistant.development.DevelopmentResultActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n'''
blocks=anchor+'''\n        <activity\n            android:name=".assistant.recipes.MyRecipesActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n\n        <activity\n            android:name=".assistant.log.DevelopmentLogActivity"\n            android:screenOrientation="portrait"\n            android:exported="false" />\n'''
rep(manifest,anchor,blocks,'manifest Ricette + Log')
wr(java/'assistant/data/AssistantDataSchema.java',rd(here/'AssistantDataSchema.java')); wr(java/'assistant/data/AssistantDatabase.java',rd(here/'AssistantDatabase.java')); wr(java/'assistant/recipes/MyRecipesActivity.java',rd(here/'MyRecipesActivity.java')); wr(java/'assistant/log/DevelopmentLogActivity.java',rd(here/'DevelopmentLogActivity.java')); wr(result,rd(here/'DevelopmentResultActivity.java'))

# Assistant menu: activate My Recipes and Development Log.
rep(assistant,'import it.darkroom.timer.assistant.chemistry.PrepareChemistryActivity;\n','import it.darkroom.timer.assistant.chemistry.PrepareChemistryActivity;\nimport it.darkroom.timer.assistant.recipes.MyRecipesActivity;\nimport it.darkroom.timer.assistant.log.DevelopmentLogActivity;\n','Assistant imports R4')
rep(assistant,'        addPlaceholder(root, "LE MIE RICETTE");\n','''        Button myRecipes = entry("LE MIE RICETTE", "Tempi personali, preferite e originale fonte", true);\n        myRecipes.setOnClickListener(v -> startActivity(new Intent(this, MyRecipesActivity.class)));\n        root.addView(myRecipes, margin(lp(-1, dp(78)), 0, 0, 0, 9));\n''','Le mie ricette operative')
rep(assistant,'        addPlaceholder(root, "LOG SVILUPPI");\n','''        Button developmentLog = entry("LOG SVILUPPI", "Storico, valutazioni, confronto e ripeti", true);\n        developmentLog.setOnClickListener(v -> startActivity(new Intent(this, DevelopmentLogActivity.class)));\n        root.addView(developmentLog, margin(lp(-1, dp(78)), 0, 0, 0, 9));\n''','Log sviluppi operativo')

# Repeat from log: prefill fields, preserve historical time explicitly, recalculate source without overwriting history.
processor_anchor='''        processor.setPadding(0,dp(5),0,dp(18)); root.addView(processor);\n\n        label(root,"PELLICOLA");\n'''
rep(newdev,processor_anchor,'''        processor.setPadding(0,dp(5),0,dp(18)); root.addView(processor);\n        if(getIntent().getIntExtra("repeatTimeSeconds",0)>0){\n            TextView repeat=text("RICETTA DAL LOG · tempo storico "+DevelopmentCatalog.formatTime(getIntent().getIntExtra("repeatTimeSeconds",0)),12,accent,true);\n            repeat.setGravity(Gravity.CENTER); repeat.setPadding(0,0,0,dp(10)); root.addView(repeat);\n        }\n\n        label(root,"PELLICOLA");\n''','banner ricetta dal Log')
rep(newdev,'        setContentView(scroll);\n    }\n\n    private void onFilmChanged() {','        setContentView(scroll);\n        applyPrefill();\n    }\n\n    private void applyPrefill() {\n        Intent src=getIntent(); if(!src.hasExtra("prefillFilm")) return;\n        filmField.setText(src.getStringExtra("prefillFilm"),false); onFilmChanged();\n        selectFormat(src.getStringExtra("prefillFormat") == null ? "120" : src.getStringExtra("prefillFormat"));\n        exposedIsoField.setText(Integer.toString(src.getIntExtra("prefillExposedIso",DevelopmentCatalog.findFilm(filmField.getText().toString()).nominalIso)));\n        developerField.setText(src.getStringExtra("prefillDeveloper"),false); refreshDilutions();\n        dilutionField.setText(src.getStringExtra("prefillDilution"),false);\n        temperatureField.setText(String.format(java.util.Locale.ITALY,"%.1f",src.getDoubleExtra("prefillTemperature",20.0)));\n        rollsField.setText(Integer.toString(src.getIntExtra("prefillRolls",1)));\n        volumeField.setText(ChemistryNumber.format(src.getDoubleExtra("prefillVolume",340.0)));\n    }\n\n    private static final class ChemistryNumber { static String format(double v){ return Math.abs(v-Math.rint(v))<0.05 ? String.format(java.util.Locale.ITALY,"%.0f",v) : String.format(java.util.Locale.ITALY,"%.1f",v); } }\n\n    private void onFilmChanged() {','prefill da Log')
rep(newdev,'        i.putExtra("alternatives",r.alternatives); i.putExtra("rolls",rolls); i.putExtra("volumeMl",volume);\n        startActivity(i);','        i.putExtra("alternatives",r.alternatives); i.putExtra("rolls",rolls); i.putExtra("volumeMl",volume);\n        if(getIntent().getIntExtra("repeatTimeSeconds",0)>0){ i.putExtra("repeatTimeSeconds",getIntent().getIntExtra("repeatTimeSeconds",0)); i.putExtra("repeatOrigin",getIntent().getStringExtra("repeatOrigin")); }\n        startActivity(i);','propaga tempo storico Log')

# Strong regression guards.
timer_after={p.name:sha(p) for p in java.glob('*.java') if p.name!='MainActivity.java'}
if timer_before!=timer_after:
    bad=[n for n in sorted(set(timer_before)|set(timer_after)) if timer_before.get(n)!=timer_after.get(n)]
    raise SystemExit('v0.10.9 GUARDRAIL TIMER: '+', '.join(bad))
if sha(home)!=home_before: raise SystemExit('v0.10.9 GUARDRAIL HOME')
if sha(catalog)!=cat_before: raise SystemExit('v0.10.9 GUARDRAIL R2 DevelopmentCatalog')
if sha(chem)!=chem_before or sha(prepare)!=prepare_before: raise SystemExit('v0.10.9 GUARDRAIL R3 chemistry engine')

# Static acceptance.
mt=rd(manifest)
if mt.count('android.intent.action.MAIN')!=1 or mt.count('android.intent.category.LAUNCHER')!=1: raise SystemExit('v0.10.9 launcher non univoco')
if 'package="it.darkroom.timer"' not in mt: raise SystemExit('v0.10.9 package alterato')
for p,needles in {
 build:['VERSION_NAME = "0.10.9"','VERSION_CODE = "54"'], gradle:["versionCode 54","versionName '0.10.9'"],
 main:['homeButton.setText("←")','setContentDescription("Torna alla Home")','topBar.addView(title','private static final String APP_VERSION = "0.10.9"'],
 assistant:['MyRecipesActivity.class','DevelopmentLogActivity.class','LE MIE RICETTE','LOG SVILUPPI'],
 manifest:['.assistant.recipes.MyRecipesActivity','.assistant.log.DevelopmentLogActivity'],
 newdev:['RICETTA DAL LOG','applyPrefill','repeatTimeSeconds','prefillVolume'],
 result:['SALVA COME MIA RICETTA','SALVA SVILUPPO NEL LOG','MIA RICETTA PREFERITA','ORIGINALE FONTE','TEMPO DA IMPOSTARE SUL TIMER'],
 java/'assistant/data/AssistantDataSchema.java':['VERSION = 1','recipes_original_immutable','one_favorite_per_combo','development_logs'],
 java/'assistant/data/AssistantDatabase.java':['SQLiteOpenHelper','findPreferred','sameTemperature','recipeFromLog','resetOriginal'],
 java/'assistant/recipes/MyRecipesActivity.java':['VEDI ORIGINALE','RIPRISTINA ORIGINALE','ELIMINA RICETTA PERSONALE','PREFERITA'],
 java/'assistant/log/DevelopmentLogActivity.java':['RIPETI','USA COME MIA RICETTA','IMPOSTA COME RICETTA PREFERITA','CONFRONTA SVILUPPI']}.items():
    t=rd(p)
    for n in needles:
        if n not in t: raise SystemExit(f'v0.10.9 verifica fallita {n} in {p}')
if 'DROP TABLE' in rd(java/'assistant/data/AssistantDataSchema.java') or 'DROP TABLE' in rd(java/'assistant/data/AssistantDatabase.java'): raise SystemExit('v0.10.9 schema distruttivo vietato')
print('v0.10.9 RELEASE 4 DARKROOM ASSISTANT — VERIFICHE SORGENTE OK',flush=True)
